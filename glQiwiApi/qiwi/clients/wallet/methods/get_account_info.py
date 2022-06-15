from typing import Any, ClassVar

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import UserProfile


class GetUserProfile(QiwiAPIMethod[UserProfile]):
    url: ClassVar[str] = 'https://edge.qiwi.com/person-profile/v1/profile/current'
    http_method: ClassVar[str] = 'GET'

    include_auth_info: bool = Field(True, alias='authInfoEnabled')
    include_contract_info: bool = Field(True, alias='contractInfoEnabled')
    include_user_info: bool = Field(True, alias='userInfoEnabled')

    def build_request(self, **url_format_kw: Any) -> 'Request':
        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            params={
                'authInfoEnabled': str(self.include_auth_info),
                'contractInfoEnabled': str(self.include_contract_info),
                'userInfoEnabled': str(self.include_user_info),
            },
        )
