import os
from pathlib import Path
from tempfile import gettempdir

import shortuuid


class Storage:
    base_path = Path(os.getenv("STORAGE_DIR", f"{gettempdir()}/wbld"))

    @classmethod
    def create(cls, parents=False, exist_ok=True):
        cls.base_path.mkdir(parents=parents, exist_ok=exist_ok)

    @classmethod
    def generate_build_uuid_path(cls) -> Path:
        path = cls.base_path.joinpath(Path(str(shortuuid.uuid())))
        path.mkdir()
        return path
