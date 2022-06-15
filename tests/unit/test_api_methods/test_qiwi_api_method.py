import json
from typing import ClassVar, List

import pytest
from pydantic import BaseModel

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.exceptions import QiwiAPIError


class M(BaseModel):
    id: int


class MyQiwiAPIMethod(QiwiAPIMethod[M]):
    url: ClassVar[str] = 'https://qiwi.com/hello/world'
    http_method: ClassVar[str] = 'GET'


def test_parse_http_response() -> None:
    method = MyQiwiAPIMethod()
    with pytest.raises(QiwiAPIError) as exc_info:
        resp = HTTPResponse(
            status_code=400,
            body=json.dumps({'message': 'Something went wrong', 'code': 'QWRPC-303'}).encode(
                'utf-8'
            ),
            headers={},
            content_type='',
        )
        method.parse_http_response(resp)

        assert exc_info.value.http_response == resp
        assert exc_info.value.error_code == '303'


def test_designate__returning_type__attribute() -> None:
    method = MyQiwiAPIMethod()
    assert method.__returning_type__ is M


def test_designate__returning_type_with_two_models() -> None:
    class Model1(QiwiAPIMethod[List[int]]):
        url: ClassVar[str] = 'https://qiwi.com/hello/world'
        http_method: ClassVar[str] = 'GET'

    class Model2(QiwiAPIMethod[M]):
        url: ClassVar[str] = 'https://qiwi.com/hello/world'
        http_method: ClassVar[str] = 'GET'

    assert Model1.__returning_type__ is List[int]
    assert Model2.__returning_type__ is M


def test_designate__returning_type__with_raw_api_method() -> None:
    class K(BaseModel):
        pass

    class MyAPIMethod(APIMethod[K]):
        url: ClassVar[str] = 'https://qiwi.com/hello/world'
        http_method: ClassVar[str] = 'PUT'

    assert MyAPIMethod.__returning_type__ is K
