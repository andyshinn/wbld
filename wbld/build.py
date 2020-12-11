from configparser import ConfigParser
from contextlib import redirect_stderr, redirect_stdout
import os
import uuid
import io

from platformio.package.manager.platform import PlatformPackageManager
from platformio.platform.exception import UnknownPlatform
from platformio.platform.factory import PlatformFactory
from platformio.project.config import ProjectConfig
from platformio.project.helpers import is_platformio_project

from wbld.log import logger


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

    @property
    def section(self):
        return self.sections()[0]

    @property
    def env(self):
        return self.section.lstrip("env:")

    @property
    def config(self):
        return self[self.section]

    @property
    def pc_config(self):
        return [(self.section, list(self.config.items()))]


class CustomProjectConfig(ProjectConfig):
    def __init__(self, config):
        super(CustomProjectConfig, self).__init__()
        self.update([(config.name, list(config.items()))])


class Builder:
    def __init__(self, path, env):
        self.uuid = uuid.uuid4()
        self.env = env
        self.path = path
        self.package_manager = PlatformPackageManager()
        self._old_dir = None
        self.project_config = None

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

    def run(self):
        options = self.project_config.items(env=self.env, as_dict=True)
        logger.debug(options)
        platform = options["platform"]

        try:
            factory = PlatformFactory.new(platform)
        except UnknownPlatform:
            self.platform_install(platform=platform, skip_default_package=True)
            factory = PlatformFactory.new(platform)

        run_options = {"pioenv": self.env, "project_config": self.project_config.path}
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            run = factory.run(run_options, [], True, False, 1)

        logger.debug(output.getvalue())
        logger.debug(f"Returning run: {run}")
        return run

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


class BuilderCustom(Builder):
    def __init__(self, path, snippet):
        logger.debug(f"Custom build in {path} using snippet:\n{snippet}")
        custom_config = CustomConfig(snippet)
        with open(f"{path.name}/platformio_override.ini", "w") as file:
            logger.debug(f"Writing out custom config to: {file.name}")
            custom_config.write(file)
        super(BuilderCustom, self).__init__(path, custom_config.env)
