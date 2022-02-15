from typing import ClassVar

from pydantic import Field

from glQiwiApi.core.abc.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod


class GetWebhookSecret(QiwiAPIMethod[str]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/{hook_id}/key"

    hook_id: str = Field(..., path_runtime_value=True)

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> str:
        return response.json()["key"]
