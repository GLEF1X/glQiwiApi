from pydantic import BaseModel

from glQiwiApi.utils.basics import custom_load


class Balance(BaseModel):
    alias: str
    currency: int

    class Config:
        json_loads = custom_load
