import abc
from typing import Any, Generic, Set, TypeVar

T = TypeVar('T')


class UnexpectedCollision(Exception):
    pass


class UnhashableObjectError(TypeError):
    pass


class AbstractCollisionDetector(abc.ABC, Generic[T]):
    """
    QIWI API can transfer_money the same update twice or more, so we need to avoid this problem anyway.
    Also, you can override it with redis usage or more advanced hashing.
    """

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


class HashBasedCollisionDetector(AbstractCollisionDetector[T]):
    def __init__(self) -> None:
        self.already_processed_object_hashes: Set[int] = set()

    def add_already_processed_event(self, obj: T) -> None:
        if _is_object_unhashable(obj):
            raise UnhashableObjectError(f'Object {obj!r} is unhashable')
        self.already_processed_object_hashes.add(hash(obj))

    def has_collision(self, obj: T) -> bool:
        if _is_object_unhashable(obj):
            raise UnhashableObjectError(f'Object {obj!r} is unhashable')
        return any(
            hash(obj) == processed_hash for processed_hash in self.already_processed_object_hashes
        )


def _is_object_unhashable(obj: Any) -> bool:
    try:
        hash(obj)
        return False
    except TypeError:
        return True
