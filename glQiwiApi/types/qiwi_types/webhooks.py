from pydantic import BaseModel, Field

from glQiwiApi.types import Sum
from glQiwiApi.utils.basics import custom_load


class Payment(BaseModel):
    """ Scheme of webhook payment object """
    account: str = Field(..., alias="account")
    comment: str = Field(..., alias="comment")
    date: str = Field(..., alias="date")
    error_code: str = Field(..., alias="errorCode")
    person_id: int = Field(..., alias="personId")
    provider: int = Field(..., alias="provider")
    sign_fields: str = Field(..., alias="signFields")
    status: str = Field(..., alias="status")
    txn_id: str = Field(..., alias="txnId")
    type: str = Field(..., alias="type")
    commission: Sum = Field(..., alias="commission")
    sum: Sum = Field(..., alias="sum")
    total: Sum = Field(..., alias="total")


class WebHook(BaseModel):
    """WebHook object"""

    hash: str = Field(..., alias="hash")
    hook_id: str = Field(..., alias="hookId")
    message_id: str = Field(..., alias="messageId")
    test: bool = Field(..., alias="test")
    version: str = Field(..., alias="version")
    payment: Payment = Field(..., alias="payment")

    class Config:
        json_loads = custom_load


class HookParameters(BaseModel):
    """hookParameters object"""

    url: str = Field(..., alias="url")


class WebHookConfig(BaseModel):
    """WebHookConfig object"""

    hook_id: str = Field(..., alias="hookId")
    hook_type: str = Field(..., alias="hookType")
    txn_type: str = Field(..., alias="txnType")
    hook_parameters: HookParameters = Field(..., alias="hookParameters")

    class Config:
        json_loads = custom_load


__all__ = ('WebHookConfig', 'WebHook')
