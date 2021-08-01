from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from glQiwiApi import BaseFilter
from glQiwiApi.core.dispatcher import filters
from glQiwiApi.types import Transaction

pytestmark = pytest.mark.asyncio


class FirstCustomFilter(BaseFilter[Transaction]):
    async def check(self, update: Transaction) -> bool:
        return False


class SecondCustomFilter(BaseFilter[Transaction]):

    async def check(self, update: Transaction) -> bool:
        return True


def test_create_filters():
    first_filter = FirstCustomFilter()
    second_filter = SecondCustomFilter()
    assert all(isinstance(f, BaseFilter) for f in [first_filter, second_filter])


async def test_and_chain_filters(mocker: MockerFixture):
    mock = mocker.Mock(spec=Transaction)
    first_filter = FirstCustomFilter()
    second_filter = SecondCustomFilter()
    chained_filter = filters.AndFilter(first_filter, second_filter)
    assert not await chained_filter.check(mock)


async def test_not_filter(mocker: MockerFixture):
    mock = mocker.Mock(spec=Transaction)
    not_filter = filters.NotFilter(FirstCustomFilter())
    assert await not_filter.check(mock) is False


@pytest.mark.xfail(raises=TypeError, reason="We cannot chain two filters, if they don't inherits from BaseFilter")
async def test_fail_chain_filters():
    first_filter = FirstCustomFilter()
    second_filter = lambda x: x is not None  # wrong type  # noqa
    filters.AndFilter(first_filter, second_filter)  # type: ignore  # noqa


async def test_check_lambda_filter(mocker: MockerFixture):
    lambda_filter: filters.LambdaBasedFilter[Transaction] = filters.LambdaBasedFilter(lambda x: x is not None)
    mock = mocker.Mock(spec=Transaction)
    assert await lambda_filter.check(mock) is True
