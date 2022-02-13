from datetime import datetime
from typing import Optional, Union, Dict, List

from glQiwiApi.core.abc.base_api_client import BaseAPIClient
from glQiwiApi.core.cache.storage import CacheStorage
from glQiwiApi.core.request_service import (
    RequestService,
    RequestServiceProto,
    RequestServiceCacheDecorator,
)
from glQiwiApi.qiwi.clients.p2p.methods.create_p2p_bill import CreateP2PBill
from glQiwiApi.qiwi.clients.p2p.methods.create_p2p_key_pair import CreateP2PKeyPair
from glQiwiApi.qiwi.clients.p2p.methods.get_bill_by_id import GetBillByID
from glQiwiApi.qiwi.clients.p2p.methods.refund_bill import RefundBill
from glQiwiApi.qiwi.clients.p2p.methods.reject_p2p_bill import RejectP2PBill
from glQiwiApi.qiwi.clients.p2p.types import Bill, PairOfP2PKeys, RefundedBill, Customer
from glQiwiApi.types.amount import PlainAmount
from glQiwiApi.utils.validators import String


class NoShimUrlWasProvidedError(Exception):
    pass


class QiwiP2PClient(BaseAPIClient):
    _api_access_token = String(optional=False)

    def __init__(
        self,
        secret_p2p: str,
        request_service: Optional[RequestServiceProto] = None,
        cache_storage: Optional[CacheStorage] = None,
        shim_server_url: Optional[str] = None,
    ) -> None:
        """
        :param secret_p2p: QIWI P2P secret key received from https://p2p.qiwi.com/
        :param shim_server_url:
        """
        self._api_access_token = secret_p2p
        self._shim_server_url = shim_server_url

        BaseAPIClient.__init__(self, request_service, cache_storage)

    def _create_request_service(self) -> RequestServiceProto:
        rs: RequestServiceProto = RequestService(
            base_headers={
                "Authorization": f"Bearer {self._api_access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        if self._cache_storage is not None:
            rs = RequestServiceCacheDecorator(rs, self._cache_storage)

        return rs

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
        return await self._request_service.execute_api_method(GetBillByID(bill_id=bill_id))

    async def check_if_bill_was_paid(self, bill: Bill) -> bool:
        bill_status = await self.get_bill_status(bill.id)
        return bill_status == "PAID"

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
        customer: Optional[Customer] = None,
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
        :param customer:
        """
        return await self._request_service.execute_api_method(
            CreateP2PBill(
                bill_id=bill_id,
                expire_at=expire_at,
                amount=amount,
                comment=comment,
                theme_code=theme_code,
                pay_source_filter=pay_source_filter,
                customer=customer,
            )
        )

    async def reject_bill(self, bill: Bill) -> Bill:
        return await self.reject_p2p_bill(bill.id)

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """Use this method to cancel unpaid invoice."""
        return await self._request_service.execute_api_method(RejectP2PBill(bill_id=bill_id))

    async def create_pair_of_p2p_keys(
        self, key_pair_name: str, server_notification_url: Optional[str] = None
    ) -> PairOfP2PKeys:
        """
        Creates a new pair of P2P keys to interact with P2P QIWI API

        :param key_pair_name: P2P token pair name
        :param server_notification_url: endpoint for webhooks
        """
        return await self._request_service.execute_api_method(
            CreateP2PKeyPair(
                key_pair_name=key_pair_name, server_notification_url=server_notification_url
            )
        )

    async def refund_bill(
        self,
        bill_id: Union[str, int],
        refund_id: Union[str, int],
        json_bill_data: Union[PlainAmount, Dict[str, Union[str, int]]],
    ) -> RefundedBill:
        """
        The method allows you to make a refund on a paid invoice.
         in the JSON body of the request for the json_bill_data parameter:
         amount.value - refund amount.
         amount.currency - return currency.
        Can be a dictionary or an PlainAmount object
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
        return await self._request_service.execute_api_method(
            RefundBill(bill_id=bill_id, refund_id=refund_id, json_bill_data=json_bill_data)
        )

    def create_shim_url(self, invoice_uid: str) -> str:
        if self._shim_server_url is None:
            raise NoShimUrlWasProvidedError(
                "QiwiP2PClient has no shim endpoint -> can't create shim endpoint for bill"
            )

        return self._shim_server_url.format(invoice_uid)
