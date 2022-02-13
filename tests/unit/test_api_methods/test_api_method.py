from typing import ClassVar

from pydantic import BaseModel, Field

from glQiwiApi.core.abc.api_method import APIMethod, Request, RuntimeValue
from glQiwiApi.core.session.holder import HTTPResponse


class MyModel(BaseModel):
    f: str


class SimpleAPIMethod(APIMethod[MyModel]):
    url: ClassVar[str] = "https://hello.world"
    http_method: ClassVar[str] = "GET"


class APIMethodWithRequestSchema(APIMethod[MyModel]):
    http_method: ClassVar[str] = "PUT"
    url: ClassVar[str] = "https://hello.world/{id}"

    json_payload_schema = {"hello": {"world": {"nested": RuntimeValue()}}}

    id: int = Field(..., path_runtime_value=True)
    nested_field: str = Field(..., scheme_path="hello.world.nested")


def test_parse_response_if_status_code_is_200() -> None:
    assert isinstance(
        SimpleAPIMethod.parse_http_response(
            HTTPResponse(status_code=200, body=b'{"f": "some_value"}', headers={}, content_type="")
        ),
        MyModel,
    )


def test_build_request_of_simple_api_method() -> None:
    method = SimpleAPIMethod()
    assert method.build_request() == Request(
        endpoint="https://hello.world",
    )


def test_build_complicated_request() -> None:
    method = APIMethodWithRequestSchema(id=5, nested_field="hello world")
    assert method.build_request() == Request(
        endpoint="https://hello.world/5",
        json_payload={"hello": {"world": {"nested": "hello world"}}},
        http_method="PUT",
    )


def test_determine_returning_type_by_generic_value() -> None:
    method = SimpleAPIMethod()
    assert method.__returning_type__ is MyModel


def test_get_filled_request_schema() -> None:
    method = APIMethodWithRequestSchema(id=5, nested_field="hello world")
    assert method._get_filled_json_payload_schema() == {
        "hello": {"world": {"nested": "hello world"}}
    }


def test_get_runtime_path_values() -> None:
    method = APIMethodWithRequestSchema(id=5, nested_field="hello world")
    assert method._get_runtime_path_values() == {"id": 5}
