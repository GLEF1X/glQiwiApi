"""Main model: Partner"""
from typing import List, Optional

from glQiwiApi.qiwi.types.base import QiwiWalletResultBaseWithClient


class Partner(QiwiWalletResultBaseWithClient):
    """Base partner class"""

    title: str
    id: int

    maps: Optional[List[str]] = None


__all__ = ("Partner",)
