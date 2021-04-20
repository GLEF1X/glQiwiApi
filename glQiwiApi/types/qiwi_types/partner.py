"""Main model: Partner"""
from typing import List, Optional

from pydantic import BaseModel


class Partner(BaseModel):
    title: str
    id: int

    maps: Optional[List[str]] = None


__all__ = ("Partner",)