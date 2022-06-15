import abc
import types
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any, ClassVar, Generic, Sequence, TypeVar, cast

from glQiwiApi.core.abc.api_method import APIMethod, ReturningType, _sentinel
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.exceptions import QiwiAPIError

try:
    from orjson import JSONDecodeError as OrjsonDecodeError
except ImportError:
    from json import JSONDecodeError as OrjsonDecodeError

T = TypeVar('T', bound=Any)


class QiwiAPIMethod(APIMethod[T], abc.ABC, Generic[T]):
    arbitrary_allowed_response_status_codes: ClassVar[Sequence[int]] = ()

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        response_is_successful = cls.check_if_response_status_success(response)

        try:
            json_response = response.json()
        except (JSONDecodeError, TypeError, OrjsonDecodeError):
            response_is_successful = False

        if not response_is_successful:
            QiwiAPIError(response).raise_exception_matching_error_code()

        # micro optimization that helps to avoid json re-deserialization
        response.json = types.MethodType(lambda self: json_response, response)  # type: ignore

        manually_parsed_json = cls.on_json_parse(response)
        if manually_parsed_json is not _sentinel:
            return cast(ReturningType, manually_parsed_json)

        return super().parse_http_response(response)

    @classmethod
    def check_if_response_status_success(cls, response: HTTPResponse) -> bool:
        if response.status_code == HTTPStatus.OK:
            return True
        elif response.status_code in cls.arbitrary_allowed_response_status_codes:
            return True
        return False
