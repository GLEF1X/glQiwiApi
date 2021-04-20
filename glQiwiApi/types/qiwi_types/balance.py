from pydantic import BaseModel

from glQiwiApi.utils.basics import custom_load


class Balance(BaseModel):
    alias: str
    currency: int

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return super().__str__()

        def __repr__(self) -> str:
            return super().__repr__()
