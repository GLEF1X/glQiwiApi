from typing import Optional, Dict, Any

from pydantic import Field, Json

from glQiwiApi.types.base import Base


class Code(Base):
    value: str
    name: str = Field(..., alias="_name")


class MobileOperator(Base):
    code: Code
    data: Optional[Json]
    message: str
    messages: Optional[Dict[str, Any]]
