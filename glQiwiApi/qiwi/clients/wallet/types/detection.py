from __future__ import annotations

from typing import Optional, Any

from pydantic import BaseModel, Field

from glQiwiApi.base.types.base import Base


class Code(BaseModel):
    value: int
    name: str = Field(..., alias="_name")


class MobileOperatorDetection(Base):
    code: Code
    data: Optional[Any] = None
    message: int
    messages: Optional[Any] = None
