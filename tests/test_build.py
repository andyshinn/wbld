import pytest

from wbld.build import CustomConfig, BasePath, Build


@pytest.fixture
def custom_config_snippet_esp():
    return """
[env:esp32dev]
board = esp32dev
build_unflags = ${common.build_unflags}
build_flags = ${common.build_flags_esp32} -D USE_APA102 D CLKPIN=2 -D DATAPIN=4
lib_ignore =
  ESPAsyncTCP
  ESPAsyncUDPplatform = espressif32@2.0]
platform = espressif32@2.0
"""


@pytest.fixture
def bad_uuid():
    return "00000000-0000-0000-4444-88888888"


@pytest.fixture
def good_uuid(tmp_path):
    def mock_base_path(self):
        self.base_path = tmp_path

    BasePath.__init__ = mock_base_path

    uuid = "88888888-1111-2222-3333-77777777"
    path = tmp_path.joinpath(uuid)
    path.mkdir()

    return uuid


def test_custom_config_name(custom_config_snippet_esp):  # pylint: disable=redefined-outer-name
    config = CustomConfig(custom_config_snippet_esp)

    assert isinstance(config, CustomConfig)
    assert config.env == "esp32dev"


def test_build_bad_uuid(bad_uuid):  # pylint: disable=redefined-outer-name
    with pytest.raises(FileNotFoundError):
        Build(bad_uuid)


def test_good_uuid(good_uuid):  # pylint: disable=redefined-outer-name
    build = Build(good_uuid)
    assert isinstance(build, Build)
