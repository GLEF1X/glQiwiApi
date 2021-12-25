from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from aiohttp import RequestInfo
from pydantic import BaseModel

from glQiwiApi.base_types.exceptions import WebhookSignatureUnverifiedError

if TYPE_CHECKING:
    from glQiwiApi.base_types.errors import QiwiErrorAnswer


class CantParseUrl(Exception):
    pass


class RequestInfoModel(BaseModel):
    method: str
    url: str
    real_url: str


class SecretP2PTokenIsEmpty(Exception):
    pass


class ExceptionTraceback(BaseModel):
    status_code: int
    msg: Optional[str] = None
    additional_info: Optional[str] = None
    request_info: Optional[RequestInfoModel] = None


class ChequeIsNotAvailable(Exception):
    def __init__(self, err_model: QiwiErrorAnswer):
        self.error_model = err_model


class APIError(Exception):
    def __init__(
        self,
        message: Optional[str],
        status_code: Union[str, int],
        additional_info: Optional[str] = None,
        request_data: Optional[Union[RequestInfo, str, bytes, Dict[Any, Any]]] = None,
    ) -> None:
        super(APIError, self).__init__()
        self.message = message
        self.status_code = status_code
        self.additional_info = additional_info
        self.request_data = request_data

    def __str__(self) -> str:
        resp = (
            "code={sc} doc(for specific cases may be deceiving)={msg}, additional_info={info}" ""
        )
        return resp.format(sc=self.status_code, msg=self.message, info=self.additional_info)

    def to_model(self) -> ExceptionTraceback:
        """Convert exception to :class:`ExceptionTraceback`"""
        if not isinstance(self.request_data, RequestInfo):
            raise TypeError(
                "Cannot convert exception to `ExceptionTraceback`, because "
                "this method require `RequestInfo` object"
            )
        return ExceptionTraceback(
            status_code=self.status_code,
            msg=self.message,
            additional_info=self.additional_info,
            request_info=RequestInfoModel(
                method=self.request_data.method,
                url=self.request_data.url.__str__(),
                real_url=self.request_data.real_url.__str__(),
            ),
        )

    def json(self, indent: int = 4, **dump_kw: Any) -> str:
        """
        Method, that makes json format from traceback

        :param indent:
        :param dump_kw:
        """
        if isinstance(self.request_data, RequestInfo):
            info = self.to_model().dict(exclude_none=True)
        else:
            info = self._make_dict()
        return json.dumps(info, indent=indent, ensure_ascii=False, **dump_kw)

    def _make_dict(self) -> Dict[str, Any]:
        return {
            "code": self.status_code,
            "msg": self.message,
            "additional_info": self.additional_info,
            "traceback_info": self.request_data,
        }


__all__ = (
    "CantParseUrl",
    "APIError",
    "ChequeIsNotAvailable",
    "SecretP2PTokenIsEmpty",
    "WebhookSignatureUnverifiedError",
)
