from pydantic import BaseModel

from glQiwiApi.utils.basics import custom_load


class Balance(BaseModel):
    """ object: Balance """
    alias: str
    currency: int

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()
