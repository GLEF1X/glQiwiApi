from typing import Hashable

from pydantic import BaseModel, BaseConfig

from glQiwiApi.utils.compat import json


class Base(BaseModel):
    class Config(BaseConfig):
        json_dumps = json.dumps  # type: ignore
        json_loads = json.loads
        orm_mode = True


class HashableBase(Base):
    class Config(BaseConfig):
        allow_mutation = False

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

    def __eq__(self, other: Hashable) -> bool:
        return self.__hash__() == other.__hash__()
