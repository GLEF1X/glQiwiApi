from pydantic import BaseConfig, BaseModel

from glQiwiApi.utils.compat import json


class Base(BaseModel):
    class Config(BaseConfig):
        json_dumps = json.dumps  # type: ignore
        json_loads = json.loads
        orm_mode = True


class HashableBase(Base):
    class Config(BaseConfig):
        allow_mutation = False
        frozen = True
