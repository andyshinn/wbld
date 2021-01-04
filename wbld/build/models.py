from __future__ import annotations
from datetime import datetime
from typing import ClassVar, Union

from discord import Member, User
import humanize
from pydantic import BaseModel, constr, DirectoryPath, validator, Field

from wbld.build.enums import Kind, State
from wbld.build.storage import Storage
from wbld.log import logger


class Author:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, author: Union[Member, User]):
        types = Union[Member, User]
        fields = ["id", "name", "avatar_url", "discriminator"]

        if isinstance(author, types.__args__):
            return dict([(name, str(getattr(author, name))) for name in fields])
        elif isinstance(author, dict):
            if set(author) == set(fields):
                return author

        raise TypeError("Invalid value")


class BuildModel(BaseModel):
    author: Author = None
    build_file: ClassVar[str] = "build.json"
    duration: float = None
    env: str
    kind: Kind
    path: DirectoryPath = Field(default_factory=Storage.generate_build_uuid_path)
    sha1: constr(regex=r"^[0-9a-f]{40}$")
    snippet: str = None
    state: State = State.PENDING
    version: str

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        underscore_attrs_are_private = True

    def __setattr__(self, name, value):
        super(BuildModel, self).__setattr__(name, value)
        self.write()

    @property
    def date(self):
        return datetime.fromtimestamp(self.path.lstat().st_ctime)

    @property
    def date_diff_human(self):
        return humanize.naturaldelta(self.date)

    @property
    def duration_human(self):
        return humanize.precisedelta(self.duration)

    @property
    def file_log(self):
        return self.path.joinpath("combined.txt")

    @property
    def file_binary(self) -> DirectoryPath:
        return self.path.joinpath("firmware.bin")

    @property
    def build_id(self):
        return self.path.stem

    @validator("path")
    @classmethod
    def check_path_contains_shortuuid(cls, value):
        build_id_constraint = constr(regex=r"^[a-zA-Z0-9]{22}$")
        build_id_constraint.validate(value.stem)
        return value

    def write(self):
        with self.path.joinpath(self.build_file).open("w") as build_info:
            build_info.write(self.json(exclude={"build_file"}))

    @classmethod
    def parse_build_id(cls, build_id: str) -> BuildModel:
        return cls.parse_file(Storage.base_path.joinpath(build_id).joinpath(cls.build_file))

    @classmethod
    def parse_build_path(cls, build_path: DirectoryPath) -> BuildModel:
        return cls.parse_file(build_path.joinpath(cls.build_file))
