from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import os
import shutil
from timeit import default_timer as timer
from pathlib import Path
from tempfile import mkdtemp, gettempdir

from platformio.package.manager.platform import PlatformPackageManager
from platformio.platform.exception import UnknownPlatform
from platformio.platform.factory import PlatformFactory
from platformio.project.config import ProjectConfig
from platformio.project.helpers import is_platformio_project

from wbld.log import logger
from wbld.build.config import CustomConfig
from wbld.build.models import BuildModel
from wbld.build.enums import Kind, State
from wbld.build.storage import Storage
from wbld.repository import Clone


class Build:
    def __new__(cls, build_id: str) -> BuildModel:
        return BuildModel.parse_build_id(build_id)


class Manager:
    @staticmethod
    def list_builds(sort=True, reverse=True):
        def sorting(key):
            if sort:
                return key.stat().st_ctime
            return None

        for path in sorted(Storage.base_path.iterdir(), key=sorting, reverse=reverse):
            if path.joinpath(BuildModel.build_file).exists():
                yield BuildModel.parse_build_path(path)

    @staticmethod
    def get_build(build_id) -> BuildModel:
        return BuildModel.parse_build_id(build_id)


class BuilderError(Exception):
    pass


class Builder:
    def __init__(self, clone: Clone, env):
        self.kind = Kind.BUILTIN
        self.build = BuildModel(kind=self.kind, env=env, version=clone.version, sha1=str(clone.sha1))
        self.clone = clone
        self.path = self.clone.path
        self.package_manager = None
        self._old_dir = None
        self.project_config = None

        if not is_platformio_project(self.path):
            logger.error(f"Raising FileNotFoundError for path: {self.path}")
            raise FileNotFoundError(self.path)

    def __enter__(self):
        logger.debug(f"Entering builder for build {self.build.build_id} at {self.path}")
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    # def _write_build_info(self, build: BuildModel):
    #     with self.build_path.joinpath("build.json").open("w") as build_info_file:
    #         build_info_file.write(build.json())

    def platform_install(self, platform, skip_default_package=True, silent=True):
        pkg = self.package_manager.install(spec=platform, skip_default_package=skip_default_package, silent=silent)
        return pkg

    @property
    def firmware_filename(self):
        return f"{self.path}/.pio/build/{self.build.env}/firmware.bin"

    # pylint: disable=too-many-arguments
    def run(self, variables=None, targets=None, silent=False, verbose=False, jobs=2):
        timer_start = timer()

        if not variables:
            variables = {"pioenv": self.build.env, "project_config": self.project_config.path}

        if not targets:
            targets = []

        try:
            options = self.project_config.items(env=self.build.env, as_dict=True)
            platform = options["platform"]
            logger.debug(f"Building {self.build.env} for {platform}")
        except KeyError:
            logger.error(f"Couldn't find platform for: {self.build.env}")
            self.build.state = State.FAILED
            return self.build

        try:
            factory = PlatformFactory.new(platform)
        except UnknownPlatform:
            self.platform_install(platform=platform, skip_default_package=True)
            factory = PlatformFactory.new(platform)

        log_combined = self.build.file_log.open("w")

        with redirect_stdout(log_combined), redirect_stderr(log_combined):
            self.build.state = State.BUILDING

            run = factory.run(variables, targets, silent, verbose, jobs)

        if run and run["returncode"] == 0:
            self.gather_files([open(self.firmware_filename, "rb")])
            self.build.state = State.SUCCESS
        else:
            self.build.state = State.FAILED

        timer_end = timer()
        duration = float(timer_end - timer_start)
        self.build.duration = duration
        return self.build

    def check_env(self):
        if self.build.env in self.project_config.envs():
            return True
        return False

    def setup(self):
        self._old_dir = os.getcwd()
        os.chdir(self.path)
        self.project_config = ProjectConfig(self.path.joinpath("platformio.ini"))
        self.package_manager = PlatformPackageManager()
        if not self.check_env():
            raise BuilderError(f"Environment doesn't exist: {self.build.env}")

    def cleanup(self):
        os.chdir(self._old_dir)
        self.clone.cleanup()

    def gather_files(self, files):
        for file in files:
            shutil.copy(file.name, self.build.path)
            file.close()
        logger.debug(f"Files gathered in {self.build.path}: {files}")


class BuilderCustom(Builder):
    def __init__(self, clone: Clone, snippet):
        logger.debug(f"Custom build in {clone.path} using snippet:\n{snippet}")
        custom_config = CustomConfig(snippet)
        with open(f"{clone.path}/platformio_override.ini", "w") as file:
            logger.debug(f"Writing out custom config to: {file.name}")
            custom_config.write(file)
        super(BuilderCustom, self).__init__(clone, custom_config.env)
        self.kind = Kind.CUSTOM
        self.build.kind = Kind.CUSTOM
        self.build.snippet = snippet
