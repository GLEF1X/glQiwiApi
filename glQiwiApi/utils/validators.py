from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import (
    Optional,
    Any,
    Pattern,
    Match,
    Callable,
    Generic,
    TypeVar
)


class SkipValidation(Exception):
    pass


PHONE_NUMBER_PATTERN: Pattern[str] = re.compile(
    r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$"
)

_T = TypeVar("_T")


class Validator(ABC, Generic[_T]):

    def __set_name__(self, owner, name: str) -> None:
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None) -> _T:
        return getattr(obj, self.private_name)

    def __set__(self, obj, value) -> None:
        try:
            self.validate(value)
        except SkipValidation:
            # it means, that field is Optional and we don't need to do something with it
            return None
        setattr(obj, self.private_name, value)

    @abstractmethod
    def validate(self, value: Any) -> None:
        pass


class String(Validator[str]):

    def __init__(self, minsize: Optional[int] = None, maxsize: Optional[int] = None,
                 predicate: Callable[[Any], bool] = None, optional: bool = False):
        self.minsize = minsize
        self.maxsize = maxsize
        self.predicate = predicate
        self._optional = optional

    def validate(self, value: Any) -> None:
        if value is None and self._optional:
            raise SkipValidation()
        if not isinstance(value, str):
            raise TypeError(f'Expected {value!r} to be an str')
        if self.minsize is not None and len(value) < self.minsize:
            raise ValueError(
                f'Expected {value!r} to be no smaller than {self.minsize!r}'
            )
        if self.maxsize is not None and len(value) > self.maxsize:
            raise ValueError(
                f'Expected {value!r} to be no bigger than {self.maxsize!r}'
            )
        if self.predicate is not None and not self.predicate(value):
            raise ValueError(
                f'Expected {self.predicate} to be true for {value!r}'
            )


class PhoneNumber(String):
    def validate(self, value):
        String.validate(self, value)
        phone_number_match: Optional[Match[Any]] = re.fullmatch(PHONE_NUMBER_PATTERN, value)
        if not phone_number_match:
            raise ValueError(
                "Failed to verify parameter `phone_number` by regex. "
                "Please, enter the correct phone number."
            )
        if not value.startswith("+"):
            raise ValueError(
                f'Expected {value!r} starts with + sign'
            )

    def __set__(self, obj: Any, value: Any) -> None:
        try:
            self.validate(value)
        except SkipValidation:
            return None

        phone_number = value.replace("+", "")
        if phone_number.startswith("8"):
            phone_number = "7" + phone_number[1:]

        setattr(obj, self.private_name, phone_number)
