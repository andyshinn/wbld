from abc import ABC, abstractmethod
import shutil
from timeit import default_timer as timer
from pathlib import Path
import json


from wbld.log import logger
from wbld.build.config import CustomConfig
from wbld.build.models import BuildModel
from wbld.build.enums import Kind, State
from wbld.build.storage import Storage
from wbld.repository import Clone
from wbld.pio import PioCommand


def is_platformio_project(path: Path) -> bool:
    return path.joinpath("platformio.ini").exists()


# class Pio:
#     @staticmethod
#     def system_info() -> dict:
#         return pio.system.info(json_output=True)


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
                logger.debug(path)
                yield BuildModel.parse_build_path(path)

    @staticmethod
    def get_build(build_id) -> BuildModel:
        return BuildModel.parse_build_id(build_id)


class BuilderError(Exception):
    pass


class Builder(ABC):
    def __init__(self, version: str, env: str):
        self.version = version
        self.env = env
        self._clone = None

    def __enter__(self):
        self.setup()
        logger.debug(f"Entering builder for build {self.build.build_id} at {self.path}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def platform_install(self, platform, skip_default_package=True, silent=True):
        pkg = self.package_manager.install(spec=platform, skip_default_package=skip_default_package, silent=silent)
        return pkg

    @property
    def firmware_filename(self):
        return f"{self._clone.path}/.pio/build/{self.build.env}/firmware.bin"

    @property
    @abstractmethod
    def kind(self):
        return NotImplementedError

    # pylint: disable=too-many-arguments
    def run(self, variables=None, targets=None, silent=False, verbose=False, jobs=2):
        timer_start = timer()
        log_combined = self.build.file_log.open("w")

        # global pio
        pio = PioCommand(out=log_combined)

        self.build.state = State.BUILDING
        run = pio.run(environment=self.build.env, project_dir=self.path, verbose=verbose, jobs=jobs)

        if run.exit_code == 0:
            self.gather_files([open(self.firmware_filename, "rb")])
            self.build.state = State.SUCCESS
        else:
            self.build.state = State.FAILED

        timer_end = timer()
        duration = float(timer_end - timer_start)
        self.build.duration = duration
        return self.build

    def get_list_of_envs(self):
        pio = PioCommand()
        project = pio.project.config(project_dir=self.path, json_output=True)
        return [env[0] for env in json.loads(project.stdout) if env[0].startswith("env:")]

    def check_env(self, env: str) -> bool:
        if f"env:{env}" in self.get_list_of_envs():
            return True
        return False

    def setup(self):
        self._clone = Clone(cleanup=False)
        self._clone.clone_version(self.version)

        if not is_platformio_project(self._clone.path):
            logger.error(f"Raising FileNotFoundError for path: {self._clone.path}")
            raise FileNotFoundError(self._clone.path)

        self.build = BuildModel(kind=self.kind, env=self.env, version=self._clone.version, sha1=str(self._clone.sha1))
        self.path = self._clone.path
        self.project_config = self.path.joinpath("platformio.ini")

        logger.debug(f"Builder setup for build {self.build.build_id} at {self.path}")

        if not self.check_env(self.build.env):
            raise BuilderError(f"Environment doesn't exist: {self.build.env}")

    def cleanup(self):
        self._clone.cleanup()

    def gather_files(self, files):
        for file in files:
            shutil.copy(file.name, self.build.path)
            file.close()
        logger.debug(f"Files gathered in {self.build.path}: {files}")


class BuilderBuiltin(Builder):
    def __init__(self, version: str, env: str):
        logger.debug(f"Built-in build for version {version} using env: {env}")
        super(BuilderBuiltin, self).__init__(version, env)

    @property
    def kind(self):
        return Kind.BUILTIN


class BuilderCustom(Builder):
    def __init__(self, version: str, clone: Clone, snippet):
        custom_config = CustomConfig(snippet)
        env = custom_config.env

        logger.debug(f"Custom build in {clone.path} using env: {env}")
        logger.trace(f"Custom config: {custom_config.snippet}")

        with open(f"{clone.path}/platformio_override.ini", "w") as file:
            logger.debug(f"Writing out custom config to: {file.name}")
            custom_config.write(file)

        super(BuilderCustom, self).__init__(clone, custom_config.env)
        self.build.snippet = snippet

    @property
    def kind(self):
        return Kind.CUSTOM
