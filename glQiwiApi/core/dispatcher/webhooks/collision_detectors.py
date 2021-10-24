from __future__ import annotations

import abc
from typing import TypeVar, List, Generic

T = TypeVar("T")


class UnexpectedCollision(Exception):
    pass


class BaseCollisionDetector(abc.ABC, Generic[T]):

    @abc.abstractmethod
    def has_collision(self, obj: T) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def add_already_processed_event(self, obj: T) -> None:
        raise NotImplementedError

    def remember_processed_object(self, obj: T) -> None:
        if self.has_collision(obj):
            raise UnexpectedCollision()
        self.add_already_processed_event(obj)


class HashBasedCollisionDetector(BaseCollisionDetector[T]):

    def __init__(self) -> None:
        self.already_processed_object_hashes: List[int] = []

    def add_already_processed_event(self, obj: T) -> None:
        self.already_processed_object_hashes.append(hash(obj))

    def has_collision(self, obj: T) -> bool:
        return any(
            hash(obj) == processed_hash
            for processed_hash in self.already_processed_object_hashes
        )
