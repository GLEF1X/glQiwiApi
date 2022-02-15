from typing import ClassVar

from pydantic import Field

from glQiwiApi.core.abc.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod


class GenerateWebhookSecret(QiwiAPIMethod[str]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/{hook_id}/newkey"
    http_method: ClassVar[str] = "POST"

    hook_id: str = Field(..., path_runtime_value=True)

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> ReturningType:
        return response.json()["key"]
