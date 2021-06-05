from datetime import datetime
from typing import Optional

from pydantic import Field

from glQiwiApi.types import Sum
from glQiwiApi.types.base import Base


class Payment(Base):
    """ Scheme of webhook payment object """
    account: str = Field(..., alias="account")
    comment: str = Field(..., alias="comment")
    date: datetime = Field(..., alias="date")
    error_code: str = Field(..., alias="errorCode")
    person_id: int = Field(..., alias="personId")
    provider: int = Field(..., alias="provider")
    sign_fields: str = Field(..., alias="signFields")
    status: str = Field(..., alias="status")
    txn_id: str = Field(..., alias="txnId")
    type: str = Field(..., alias="type")
    commission: Optional[Sum] = Field(default=None, alias="commission")
    sum: Sum = Field(..., alias="sum")
    total: Sum = Field(..., alias="total")


class WebHook(Base):
    """
    Хуки или уведомления с данными о событии (платеже/пополнении)

    """

    hash: Optional[str] = Field(default=None, alias="hash")
    hook_id: str = Field(..., alias="hookId")
    message_id: Optional[str] = Field(default=None, alias="messageId")
    test: bool = Field(..., alias="test")
    version: str = Field(..., alias="version")
    payment: Optional[Payment] = Field(default=None, alias="payment")


class HookParameters(Base):
    """hookParameters object"""

    url: str = Field(..., alias="url")


class WebHookConfig(Base):
    """WebHookConfig object"""

    hook_id: str = Field(..., alias="hookId")
    hook_type: str = Field(..., alias="hookType")
    txn_type: str = Field(..., alias="txnType")
    hook_parameters: HookParameters = Field(..., alias="hookParameters")


__all__ = ('WebHookConfig', 'WebHook')
