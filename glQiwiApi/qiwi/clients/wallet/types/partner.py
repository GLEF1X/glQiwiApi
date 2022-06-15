"""Main model: Partner"""
from typing import List, Optional

from glQiwiApi.types.base import Base


class Partner(Base):
    """Base partner class"""

    title: str
    id: int

    maps: Optional[List[str]] = None


__all__ = ('Partner',)
