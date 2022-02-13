from typing import Any

import pytest

from glQiwiApi.core.abc.api_method import RuntimeValue


@pytest.mark.parametrize(
    "rv,expected",
    [
        (RuntimeValue(default="hello"), True),
        (RuntimeValue(default_factory=lambda: "world"), True),
        (RuntimeValue(), False),
    ],
)
def test_has_default(rv: RuntimeValue, expected: bool) -> None:
    assert rv.has_default() is expected


@pytest.mark.parametrize(
    "rv,expected",
    [
        (RuntimeValue(default="hello"), "hello"),
        (RuntimeValue(default_factory=lambda: "world"), "world"),
        (RuntimeValue(), None),
    ],
)
def test_get_default(rv: RuntimeValue, expected: Any) -> None:
    assert rv.get_default() == expected
