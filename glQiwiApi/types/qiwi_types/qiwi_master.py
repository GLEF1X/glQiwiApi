from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.types import Sum


class OrderDetails(BaseModel):
    """ object: OrderDetails """
    order_id: str = Field(..., alias="id")
    card_alias: str = Field(..., alias="cardAlias")
    status: str
    price: Optional[Sum] = None
    card_id: Optional[str] = Field(alias="cardId", default=None)


__all__ = (
    'OrderDetails'
)
