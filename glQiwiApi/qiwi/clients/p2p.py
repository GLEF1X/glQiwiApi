import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict, List

from glQiwiApi.base_types import PlainAmount
from glQiwiApi.core.abc.wrapper import Wrapper
from glQiwiApi.core.mixins import DataMixin
from glQiwiApi.core.request_service import RequestService
from glQiwiApi.core.session import AbstractSessionHolder
from glQiwiApi.qiwi.settings import QiwiKassaRouter, QiwiApiMethods
from glQiwiApi.qiwi.types import Bill, PairOfP2PKeys, RefundBill
from glQiwiApi.utils.dates_conversion import datetime_to_iso8601_with_moscow_timezone
from glQiwiApi.utils.payload import patch_p2p_create_payload
from glQiwiApi.utils.validators import String


def get_default_bill_time() -> datetime:
    return datetime.now() + timedelta(days=2)


class QiwiP2PClient(Wrapper, DataMixin):
    _api_access_token = String(optional=False)

    def __init__(
        self,
        secret_p2p: str,
        cache_time_in_seconds: Union[float, int] = 0,
        session_holder: Optional[AbstractSessionHolder[Any]] = None,
        shim_server_url: Optional[str] = None,
    ) -> None:
        """
        :param secret_p2p: QIWI P2P secret key received from https://p2p.qiwi.com/
        :param cache_time_in_seconds: Time to cache requests in seconds,
                           default 0, respectively the request will not use the cache by default
        :param session_holder: obtains session and helps to manage session lifecycle. You can pass
                               your own session holder, for example using httpx lib and use it
        :param shim_server_url:
        """
        self._router = QiwiKassaRouter()
        self._request_service = RequestService(
            error_messages=self._router.config.ERROR_CODE_MESSAGES,
            cache_time=cache_time_in_seconds,
            session_holder=session_holder,
        )
        self._api_access_token = secret_p2p
        self._shim_server_url = shim_server_url

    def _add_authorization_header(self, headers: Dict[Any, Any]) -> Dict[Any, Any]:
        auth = headers.get("Authorization")
        if auth is None:
            auth = "Bearer {token}"
        headers["Authorization"] = auth.format(token=self._api_access_token)
        return headers

    async def get_bill_by_id(self, bill_id: str) -> Bill:
        """
        Method for checking the status of a p2p transaction.\n
        Possible transaction types: \n
        WAITING	Bill is waiting for pay	\n
        PAID	Bill was paid	\n
        REJECTED	Bill was rejected\n
        EXPIRED	The bill has expired. Invoice not paid\n
        Docs:
        https://developer.qiwi.com/ru/p2p-payments/?shell#invoice-status

        :param bill_id:
        :return: status of bill
        """
        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._add_authorization_header(data.headers)
        response = await self._request_service.api_request(
            "GET",
            QiwiApiMethods.CHECK_P2P_BILL_STATUS,
            self._router,
            headers=headers,
            bill_id=bill_id,
        )
        return Bill.from_obj(self, response)

    async def get_bill_status(self, bill_id: str) -> str:
        """
        Method for checking the status of a p2p transaction.\n
        Possible transaction types: \n
        WAITING	Bill is waiting for pay	\n
        PAID	Bill was paid	\n
        REJECTED	Bill was rejected\n
        EXPIRED	The bill has expired. Invoice not paid\n
        Docs:
        https://developer.qiwi.com/ru/p2p-payments/?shell#invoice-status

        :param bill_id:
        :return: status of bill
        """
        return (await self.get_bill_by_id(bill_id)).status.value

    async def create_p2p_bill(
        self,
        amount: Union[int, float, str],
        bill_id: Optional[str] = None,
        comment: Optional[str] = None,
        expire_at: Optional[datetime] = None,
        theme_code: Optional[str] = None,
        pay_source_filter: Optional[List[str]] = None,
    ) -> Bill:
        """
        It is the reliable method for integration.
        Parameters are sent by means of server2server requests with authorization.
        Method allows you to issue an invoice, successful
         response contains payUrl link to redirect client on Payment Form.
        Possible values of pay_source_filter:
          - 'qw'
          - 'card'
          - 'mobile'

        :param amount: amount of payment
        :param bill_id: unique transaction number, if not transmitted,
         generated automatically,
        :param expire_at: the date until which the invoice will be available for payment.
        :param comment:
        :param theme_code:
        :param pay_source_filter: When you open the form, the following will be displayed
         only the translation methods specified in this parameter
        """
        if not isinstance(bill_id, (str, int)):
            bill_id = str(uuid.uuid4())
        expire_at = datetime_to_iso8601_with_moscow_timezone(  # type: ignore
            expire_at or get_default_bill_time()
        )
        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._add_authorization_header(data.headers)
        payload = patch_p2p_create_payload(
            data, amount, str(expire_at), comment, theme_code, pay_source_filter
        )
        response = await self._request_service.api_request(
            "PUT",
            QiwiApiMethods.CREATE_P2P_BILL,
            self._router,
            headers=headers,
            json=payload,
            bill_id=bill_id,
        )
        return Bill.from_obj(self, response)

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """Use this method to cancel unpaid invoice."""
        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._add_authorization_header(data.headers)
        response = await self._request_service.api_request(
            "POST",
            QiwiApiMethods.REJECT_P2P_BILL,
            self._router,
            headers=headers,
            bill_id=bill_id,
        )
        return Bill.from_obj(self, response)

    async def create_pair_of_p2p_keys(
        self, key_pair_name: str, server_notification_url: Optional[str] = None
    ) -> PairOfP2PKeys:
        """
        Creates a new pair of P2P keys to interact with P2P QIWI API

        :param key_pair_name: P2P token pair name
        :param server_notification_url: url for webhooks
        """
        headers = self._add_authorization_header(self._router.generate_default_headers())
        data = {
            "keysPairName": key_pair_name,
            "serverNotificationsUrl": server_notification_url,
        }
        response = await self._request_service.api_request(
            "POST",
            QiwiApiMethods.CREATE_P2P_KEYS,
            self._router,
            headers=headers,
            json=data,
        )
        return PairOfP2PKeys.from_obj(self, response)

    async def refund_bill(
        self,
        bill_id: Union[str, int],
        refund_id: Union[str, int],
        json_bill_data: Union[PlainAmount, Dict[str, Union[str, int]]],
    ) -> RefundBill:
        """
        The method allows you to make a refund on a paid invoice.
         in the JSON body of the request for the json_bill_data parameter:
         amount.value - refund amount.
         amount.currency - return currency.
        Can be a dictionary or an OptionalSum object
         Dictionary example: {
        "amount": {
            "currency": "RUB",
            "value": 1
            }
        }

        :param bill_id: unique account identifier in the merchant's system
        :param refund_id: unique identifier of the refund in the merchant's system.
        :param json_bill_data:
        :return: RefundBill object
        """
        headers = self._add_authorization_header(self._router.generate_default_headers())
        json = json_bill_data if isinstance(json_bill_data, dict) else json_bill_data.json()
        response = await self._request_service.api_request(
            "PUT",
            QiwiApiMethods.REFUND_BILL,
            self._router,
            headers=headers,
            json=json,
            refund_id=refund_id,
            bill_id=bill_id,
        )
        return RefundBill.from_obj(self, response)

    def get_request_service(self) -> RequestService:
        return self._request_service
