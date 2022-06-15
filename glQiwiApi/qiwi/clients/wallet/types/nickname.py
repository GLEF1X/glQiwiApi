from typing import Optional

from pydantic import Field

from glQiwiApi.types.base import Base


class NickName(Base):
    can_change: bool = Field(..., alias='canChange')
    can_use: bool = Field(..., alias='canUse')
    description: str
    nickname: Optional[str] = None
