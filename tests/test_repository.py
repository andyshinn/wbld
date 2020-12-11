import pytest

from wbld.repository import Clone


class TestClone:
    def test_clone_init(self):
        clone = Clone("fake_version")

        assert isinstance(clone, Clone)
        assert clone.version == "fake_version"
        assert clone.url == "https://github.com/Aircoookie/WLED.git"

    def test_clone_requires_version(self):
        with pytest.raises(TypeError):
            Clone()  # pylint: disable=no-value-for-parameter
