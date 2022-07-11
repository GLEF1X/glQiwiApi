from typing import List

from pydantic import Field

from glQiwiApi.types.amount import Amount
from glQiwiApi.types.base import Base


class Statistic(Base):
    """object: Statistic"""

    incoming: List[Amount] = Field(alias='incomingTotal')
    out: List[Amount] = Field(alias='outgoingTotal')


__all__ = ['Statistic']
