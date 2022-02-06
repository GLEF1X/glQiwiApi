import abc
import types
from http import HTTPStatus
from json import JSONDecodeError
from typing import TypeVar, Generic, Any

from glQiwiApi.core.abc.api_method import APIMethod, ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.exceptions import QiwiAPIError

try:
    from orjson import JSONDecodeError as OrjsonDecodeError
except ImportError:
    from json import JSONDecodeError as OrjsonDecodeError

T = TypeVar("T", bound=Any)


class QiwiAPIMethod(APIMethod[T], abc.ABC, Generic[T]):

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        response_is_invalid = False
        if response.status_code != HTTPStatus.OK:
            response_is_invalid = True

        try:
            json_response = response.json()
        except (JSONDecodeError, TypeError, OrjsonDecodeError):
            response_is_invalid = True

        if response_is_invalid:
            return QiwiAPIError(response).raise_exception_matching_error_code()

        # micro optimization that helps to avoid json re-deserialization
        response.json = types.MethodType(lambda self: json_response, response)  # type: ignore

        return super().parse_http_response(response)
