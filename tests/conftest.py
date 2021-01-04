import pytest
from wbld.build.storage import Storage


@pytest.fixture(autouse=True)
def storage_dir(tmp_path_factory, monkeypatch):
    path = tmp_path_factory.mktemp("wbld")
    monkeypatch.setattr(Storage, "base_path", path)
    return path
