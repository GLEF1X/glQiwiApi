import abc
import re
from abc import ABC
from typing import (
    Any,
    Callable,
    Generic,
    Match,
    Optional,
    Pattern,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from glQiwiApi.utils.compat import Literal


class ValidationError(Exception):
    pass


PHONE_NUMBER_PATTERN: Pattern[str] = re.compile(
    r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$"
)

_FieldType = TypeVar("_FieldType", bound=Any)


class Field(ABC, Generic[_FieldType]):
    def __init__(self, *validators: Callable[[_FieldType], None]):
        self._validators = validators

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.private_name = "_" + name

    def __get__(self, obj: Any, objtype: Optional[Type[Any]] = None) -> _FieldType:
        return cast(_FieldType, getattr(obj, self.private_name))

    def __set__(self, obj: Any, value: _FieldType) -> None:
        self.validate(value)
        setattr(obj, self.private_name, value)

    def validate(self, value: _FieldType) -> None:
        for validator in self._validators:
            validator(value)


class AbstractValidator(ABC):
    def __init__(self, optional: bool = False):
        self._optional = optional

    def validate(self, value: Any) -> None:
        if self._optional is True and value is None:
            return
        self._validate(value)

    @abc.abstractmethod
    def _validate(self, value: Any) -> None:
        pass

    def __call__(self, value: Any) -> None:
        self.validate(value)


class StringValidator(AbstractValidator):
    def __init__(
        self,
        *,
        minsize: Optional[int] = None,
        maxsize: Optional[int] = None,
        predicate: Optional[Callable[[Any], bool]] = None,
        optional: bool = False,
    ):
        AbstractValidator.__init__(self, optional=optional)
        self.minsize = minsize
        self.maxsize = maxsize
        self.predicate = predicate
        self._optional = optional

    def _validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValidationError(f"Expected {value!r} to be an str")
        if self.minsize is not None and len(value) < self.minsize:
            raise ValidationError(f"Expected {value!r} to be no smaller than {self.minsize!r}")
        if self.maxsize is not None and len(value) > self.maxsize:
            raise ValidationError(f"Expected {value!r} to be no bigger than {self.maxsize!r}")
        if self.predicate is not None and not self.predicate(value):
            raise ValidationError(f"Expected {self.predicate} to be true for {value!r}")


class PhoneNumberValidator(StringValidator):
    def _validate(self, value: Optional[str]) -> None:
        StringValidator._validate(self, value)
        phone_number_match: Optional[Match[Any]] = re.fullmatch(PHONE_NUMBER_PATTERN, value)
        if not phone_number_match:
            raise ValidationError(
                "Failed to verify parameter `phone_number` by regex. "
                "Please, enter the correct phone number."
            )
        if not value.startswith("+"):  # type: ignore
            raise ValidationError(f"Expected {value!r} starts with + sign")


class IntegerValidator(AbstractValidator):
    def _validate(self, value: _FieldType) -> None:
        if not isinstance(value, int):
            raise ValidationError(f"Expected {value!r} to be an integer")


@overload
def String(optional: Literal[True], **options: Any) -> Field[Optional[str]]:
    ...


@overload
def String(optional: Literal[False], **options: Any) -> Field[str]:
    ...


def String(optional: bool = False, **options: Any) -> Union[Field[Optional[str]], Field[str]]:
    return Field(StringValidator(optional=optional, **options))


def PhoneNumber(**options: Any) -> Field[Optional[str]]:
    return Field(PhoneNumberValidator(**options))


@overload
def Integer(optional: Literal[True]) -> Field[Optional[int]]:
    ...


@overload
def Integer(optional: Literal[False]) -> Field[int]:
    ...


def Integer(optional: bool = False) -> Union[Field[Optional[int]], Field[int]]:
    return Field(IntegerValidator(optional=optional))
