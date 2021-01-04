from __future__ import annotations
import os

from platformio.project.config import ProjectConfig
from pydantic.error_wrappers import ValidationError
import pytest

from wbld.build.config import CustomConfig
from wbld.build.models import BuildModel
from wbld.build.enums import Kind, State
from wbld.build import Build, Builder, BuilderCustom
from wbld.repository import Clone


@pytest.fixture
def custom_config_snippet_esp():
    return """[env:fake_esp32_new]
board = esp32dev
build_unflags = ${common.build_unflags}
build_flags = ${common.build_flags_esp32} -D USE_APA102 -D CLKPIN=2 -D DATAPIN=4
lib_ignore =
  ESPAsyncTCP
  ESPAsyncUDPplatform = espressif32@2.0]
platform = espressif32@2.0
"""


@pytest.fixture
def builtin_config_snippet_d1():
    return """[env:d1_mini]
board = d1_mini
platform = ${common.platform_wled_default}
platform_packages = ${common.platform_packages}
upload_speed = 921600
board_build.ldscript = ${common.ldscript_4m1m}
build_unflags = ${common.build_unflags}
build_flags = ${common.build_flags_esp8266}
monitor_filters = esp8266_exception_decoder
"""


@pytest.fixture
def temp_clone_with_override(tmp_path_factory, builtin_config_snippet_d1):  # pylint: disable=redefined-outer-name
    path = tmp_path_factory.mktemp("clone")
    ini = path.joinpath("platformio.ini")
    ini.write_text(builtin_config_snippet_d1)
    clone = Clone("master2")
    clone.path = path
    clone.sha1 = "5d6b97a63e4357f09f561f06355b2965be52ace7"
    return clone


@pytest.fixture
def bad_uuid(storage_dir):  # pylint: disable=redefined-outer-name,unused-argument
    uuid = "tooshort"
    path = storage_dir.joinpath(uuid)
    path.mkdir()

    json = f"""{{
        "path": "{str(path)}",
        "duration": 0.0,
        "kind": 1,
        "author_avatar_url": null,
        "author_name": null,
        "author_discriminator": null,
        "env": "fake_env_esp8266",
        "version": "master3",
        "sha1": "1d6b97a63e3357f09f561f06355b2965be52ace7",
        "state": 3
    }}"""

    build_info = path / "build.json"
    build_info.write_text(json)

    print(json)
    print(build_info)

    return uuid


@pytest.fixture
def missing_uuid():
    return "0000000000000000000000"


@pytest.fixture
def good_uuid(storage_dir):  # pylint: disable=redefined-outer-name
    uuid = "f5J7V4PU6vQuaLCKdQJwkz"
    path = storage_dir.joinpath(uuid)
    path.mkdir()

    json = f"""{{
        "path": "{str(path)}",
        "duration": 0.0,
        "kind": 1,
        "author_avatar_url": null,
        "author_name": null,
        "author_discriminator": null,
        "env": "fake_env_esp32",
        "version": "master3",
        "sha1": "1d6b97a63e3357f09f561f06355b2965be52ace7",
        "state": 3
    }}"""

    build_info = path / "build.json"
    build_info.write_text(json)

    return path


def test_custom_config_name(custom_config_snippet_esp):  # pylint: disable=redefined-outer-name
    config = CustomConfig(custom_config_snippet_esp)

    assert isinstance(config, CustomConfig)
    assert config.env == "fake_esp32_new"


def test_build_bad_uuid(bad_uuid):  # pylint: disable=redefined-outer-name
    print(bad_uuid)

    with pytest.raises(ValidationError):
        Build(bad_uuid)


def test_build_missing_uuid(missing_uuid):  # pylint: disable=redefined-outer-name
    with pytest.raises(FileNotFoundError):
        Build(missing_uuid)


def test_good_uuid(good_uuid):  # pylint: disable=redefined-outer-name
    build = Build(good_uuid)
    assert isinstance(build, BuildModel)
    assert build.kind == Kind.BUILTIN  # pylint: disable=no-member
    assert build.state == State.SUCCESS  # pylint: disable=no-member


def test_custom_builder(temp_clone_with_override, custom_config_snippet_esp):  # pylint: disable=redefined-outer-name
    custom_builder = BuilderCustom(temp_clone_with_override, custom_config_snippet_esp)
    assert isinstance(custom_builder, BuilderCustom)
    assert custom_builder.kind == Kind.CUSTOM
    assert custom_builder.build.env == "fake_esp32_new"


def test_builtin_builder(temp_clone_with_override):  # pylint: disable=redefined-outer-name
    builtin_builder = Builder(temp_clone_with_override, "d1_mini")
    assert isinstance(builtin_builder, Builder)
    assert builtin_builder.kind == Kind.BUILTIN
    assert builtin_builder.build.env == "d1_mini"


def test_builtin_builder_contextmanager(temp_clone_with_override):  # pylint: disable=redefined-outer-name
    with Builder(temp_clone_with_override, "d1_mini") as builder:
        assert isinstance(builder, Builder)
        assert isinstance(builder.project_config, ProjectConfig)
        assert os.getcwd() == str(temp_clone_with_override.path)
