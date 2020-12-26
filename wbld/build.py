from configparser import ConfigParser
from contextlib import redirect_stderr, redirect_stdout
import os
import shutil
import uuid
from pathlib import Path
from tempfile import mkdtemp, gettempdir

import pendulum
from platformio.package.manager.platform import PlatformPackageManager
from platformio.platform.exception import UnknownPlatform
from platformio.platform.factory import PlatformFactory
from platformio.project.config import ProjectConfig
from platformio.project.helpers import is_platformio_project

from wbld.log import logger

STORAGE = os.getenv("STORAGE_DIR", f"{gettempdir()}/wbld")


class CustomConfigException(Exception):
    def __init__(self, cc, message="Too many sections in configuration"):
        self.message = message

        if cc:
            self.message += f": {len(cc)}"

        super(CustomConfigException, self).__init__(self.message)


class CustomConfig(ConfigParser):
    def __init__(self, snippet):
        super(CustomConfig, self).__init__()
        self.snippet = snippet
        self.read_string(self.snippet)

        if len(self) > 1:
            raise CustomConfigException(self)

    def __len__(self):
        return len(self._sections)

    def __str__(self):
        return self.snippet

    @staticmethod
    def remove_prefix(text, prefix):
        if text.startswith(prefix):
            return text[len(prefix) :]
        return text

    @property
    def section(self):
        return self.sections()[0]

    @property
    def env(self):
        return CustomConfig.remove_prefix(self.section, "env:")

    @property
    def config(self):
        return self[self.section]

    @property
    def pc_config(self):
        return [(self.section, list(self.config.items()))]


class CustomProjectConfig(ProjectConfig):
    def __init__(self, path=None):
        super(CustomProjectConfig, self).__init__(path)

    def append_custom_config(self, custom_config):
        self.update([(custom_config.name, list(custom_config.items()))])

    def get_env_platform(self, env):
        env_items = self.items(env=env, as_dict=True)

        logger.debug(env_items)

        if "platform" in env_items:
            return env_items["platform"]

        return None


class BasePath:
    def __init__(self):
        self.base_path = Path(STORAGE)


class Build(BasePath):
    def __init__(self, uuid):  # pylint: disable=redefined-outer-name
        super(Build, self).__init__()
        self.path = self.base_path.joinpath(str(uuid))
        self.uuid = uuid

        if not self.path.is_dir():
            raise FileNotFoundError

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.uuid)

    def __str__(self):
        return str(self.uuid)

    def _get_file(self, file, mode="r"):
        file = self.path.joinpath(file)

        if file.exists():
            return open(file, mode)
        return None

    @property
    def log(self):
        return self._get_file("combined")

    @property
    def firmware(self):
        return self._get_file("firmware.bin", "rb")

    @property
    def datetime_creation(self):
        return pendulum.from_timestamp(self.path.stat().st_ctime)

    @property
    def datetime_w3c(self):
        return self.datetime_creation.to_w3c_string()

    @property
    def datetime_human_diff(self):
        return self.datetime_creation.diff_for_humans()


class Manager(BasePath):
    def list_builds(self):
        return [Build(path.name) for path in self.base_path.iterdir()]

    def get_build(self, uuid):  # pylint: disable=redefined-outer-name
        return Build(uuid)


class Builder:
    def __init__(self, path, env):
        self.uuid = uuid.uuid4()
        self.env = env
        self.path = path
        self.package_manager = PlatformPackageManager()
        self._old_dir = None
        self.project_config = None
        self.uuid = uuid.uuid4()

        if not is_platformio_project(self.path.name):
            logger.debug(f"Raising FileNotFoundError for path: {self.path}")
            raise FileNotFoundError(self.path)

    def __enter__(self):
        logger.debug(f"Enter builder: {self.path}")
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def platform_install(self, platform, skip_default_package=True, silent=True):
        pkg = self.package_manager.install(spec=platform, skip_default_package=skip_default_package, silent=silent)
        return pkg

    @property
    def firmware_filename(self):
        return f"{self.path.name}/.pio/build/{self.env}/firmware.bin"

    # pylint: disable=too-many-arguments
    def run(self, variables=None, targets=None, silent=False, verbose=False, jobs=2):
        if not variables:
            variables = {"pioenv": self.env, "project_config": self.project_config.path}

        if not targets:
            targets = []

        options = self.project_config.items(env=self.env, as_dict=True)
        logger.debug(f"Building env: {self.env}")
        logger.debug(options)
        platform = options["platform"]

        try:
            factory = PlatformFactory.new(platform)
        except UnknownPlatform:
            self.platform_install(platform=platform, skip_default_package=True)
            factory = PlatformFactory.new(platform)

        log_dir = mkdtemp()
        log_combined = open(file=f"{log_dir}/combined.txt", mode="w")

        with redirect_stdout(log_combined), redirect_stderr(log_combined):
            run = factory.run(variables, targets, silent, verbose, jobs)

        logger.debug(run)

        logger.debug(f"Logged stdout and stderr to: {log_combined.name}")

        if run:
            self.gather_files([log_combined, open(self.firmware_filename, "rb")])
            return Build(self.uuid)

        return False

    def build_file(self):
        run = self.run()

        if not run["returncode"] == 0:
            return None

        logger.debug(f"Returning file: {self.firmware_filename}")
        return open(self.firmware_filename, "rb")

    def check_env(self):
        if self.env in self.project_config.envs():
            return True
        return False

    def setup(self):
        self._old_dir = os.getcwd()
        os.chdir(self.path.name)
        self.project_config = ProjectConfig(os.path.join(self.path.name, "platformio.ini"))

    def cleanup(self):
        os.chdir(self._old_dir)
        self.path.cleanup()

    def gather_files(self, files):
        path = Path(f"{STORAGE}/{str(self.uuid)}")
        path.mkdir(parents=True, exist_ok=True)
        for file in files:
            shutil.copy(file.name, path)
            file.close()
        logger.debug(f"File temporary path: {path}")


class BuilderCustom(Builder):
    def __init__(self, path, snippet):
        logger.debug(f"Custom build in {path} using snippet:\n{snippet}")
        custom_config = CustomConfig(snippet)
        with open(f"{path.name}/platformio_override.ini", "w") as file:
            logger.debug(f"Writing out custom config to: {file.name}")
            custom_config.write(file)
        super(BuilderCustom, self).__init__(path, custom_config.env)
