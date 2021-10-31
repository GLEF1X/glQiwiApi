import base64
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any, List, cast

from pydantic import Field, root_validator

from glQiwiApi.types.base import Base, HashableBase
from glQiwiApi.types.amount import HashableSum
from glQiwiApi.types.exceptions import WebhookSignatureUnverified


def _get_sign_field(dictionary: Dict[Any, Any], nested_keys_list: List[str]) -> Any:
    """
    Recursively iter for nested_keys_list and get nested element.

    For example, imagine that we have list(nested_keys_list) like ["x", "y", "z"],
    x and y is a dictionaries and z is our desired value. So, it's not trivial task without recursion.

    Also, imagine that our nested dict(dictionary) is {"x": {"y": "some_value"}} or {"x": {"y": {"z": "some_value"}}}.
    So, in first example z is already value, in second z is a dict with the desired value and with this help function we
    can process both of this cases.

    @param dictionary:
    @param nested_keys_list:
    @return:
    """
    current = dictionary.get(nested_keys_list.pop(0))
    if isinstance(current, dict):
        return _get_sign_field(current, nested_keys_list)
    else:
        return current


class WebhookPayment(HashableBase):
    """Scheme of webhook payment object"""

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
    commission: Optional[HashableSum] = Field(default=None, alias="calc_commission")
    sum: HashableSum = Field(..., alias="sum")
    total: HashableSum = Field(..., alias="total")


class WebHook(HashableBase):
    """Object: WebHook"""

    hash: Optional[str] = Field(default=None, alias="hash")
    hook_id: str = Field(..., alias="hookId")
    message_id: Optional[str] = Field(default=None, alias="messageId")
    test: bool = Field(..., alias="test")
    version: str = Field(..., alias="version")
    payment: Optional[WebhookPayment] = Field(default=None, alias="payment")

    signature: str
    """NOT API field, this signature is generating in `webhook_signature_collector`"""

    @property
    def is_testable(self) -> bool:
        return self.test and not self.payment

    @root_validator(pre=True)
    def webhook_signature_collector(cls, values: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Get webhook signature to confirm it with hash by base64 encoded key.
        payment.signFields is string. e.g. "sum.currency,sum.amount,type,account,txnId".
        So, this string disassembled piece by piece recursively, because each of signField part, that separated by comma
        can be nested by "."

        @param values:
        @return:
        """
        payment = cast(Optional[Dict[Any, Any]], values.get("payment"))
        if payment is None:
            return values

        sign_fields_list = cast(str, payment.get("signFields")).split(",")
        webhook_signature = "|".join(
            str(_get_sign_field(payment, sign_field.split(".")))
            for sign_field in sign_fields_list
        )
        values.update(signature=webhook_signature)
        return values

    def verify_signature(self, webhook_base64_key: str) -> None:
        webhook_key = base64.b64decode(bytes(webhook_base64_key, "utf-8"))
        generated_hash = hmac.new(
            webhook_key, self.signature.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if generated_hash != self.hash:
            raise WebhookSignatureUnverified()


class HookParameters(Base):
    """hookParameters object"""

    url: str = Field(..., alias="url")


class WebHookConfig(Base):
    """WebHookConfig object"""

    hook_id: str = Field(..., alias="hookId")
    hook_type: str = Field(..., alias="hookType")
    txn_type: str = Field(..., alias="txnType")
    hook_parameters: HookParameters = Field(..., alias="hookParameters")


__all__ = ("WebHookConfig", "WebHook", "WebhookPayment")
