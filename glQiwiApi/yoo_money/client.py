"""
Provides effortless work with YooMoney API using asynchronous requests.

"""
from __future__ import annotations

import asyncio
import typing
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Union

from glQiwiApi.core.abc.base_api_client import BaseAPIClient, RequestServiceFactoryType
from glQiwiApi.core.request_service import RequestService, RequestServiceProto
from glQiwiApi.core.session import AiohttpSessionHolder
from glQiwiApi.utils.payload import make_payload
from glQiwiApi.utils.validators import String
from glQiwiApi.yoo_money.methods.acccept_incoming_transfer import AcceptIncomingTransfer
from glQiwiApi.yoo_money.methods.build_auth_url import BuildAuthURL
from glQiwiApi.yoo_money.methods.get_access_token import GetAccessToken
from glQiwiApi.yoo_money.methods.make_cellular_payment import MakeCellularPayment
from glQiwiApi.yoo_money.methods.operation_details import OperationDetailsMethod
from glQiwiApi.yoo_money.methods.operation_history import OperationHistoryMethod
from glQiwiApi.yoo_money.methods.process_payment import ProcessPayment
from glQiwiApi.yoo_money.methods.reject_incoming_transfer import RejectIncomingTransfer
from glQiwiApi.yoo_money.methods.request_payment import RequestPayment
from glQiwiApi.yoo_money.methods.retrieve_account_info import RetrieveAccountInfo
from glQiwiApi.yoo_money.methods.revoke_api_token import RevokeAPIToken
from glQiwiApi.yoo_money.types import (
    AccountInfo,
    IncomingTransaction,
    OperationDetails,
    OperationHistory,
    Payment,
    RequestPaymentResponse,
)


class YooMoneyAPI(BaseAPIClient):
    """
    That class implements processing requests to YooMoney
    It is convenient in that it does not just give json such objects,
    and all this converts into pydantic models.
    To work with this class, you need to register a token,
    using the guide on the official github of the project

    """

    _api_access_token = String(optional=False)

    def __init__(
        self,
        api_access_token: str,
        request_service_factory: Optional[RequestServiceFactoryType] = None,
    ) -> None:
        """
        The constructor accepts a token obtained from the method class get_access_token
         and the special attribute without_context

        :param api_access_token: api token for requests
        """
        self._api_access_token = api_access_token
        BaseAPIClient.__init__(self, request_service_factory)

    async def _create_request_service(self) -> RequestServiceProto:
        return RequestService(
            session_holder=AiohttpSessionHolder(
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Bearer {self._api_access_token}',
                    'Host': 'yoomoney.ru',
                }
            )
        )

    @classmethod
    async def build_url_for_auth(
        cls, scopes: List[str], client_id: str, redirect_uri: str = 'https://example.com'
    ) -> str:
        """
        Method to get the link for further authorization and obtaining a token

        :param scopes: OAuth2 authorization of the application by the user,
         the rights are transferred by the list.
        :param client_id: application id, type string
        :param redirect_uri: a funnel where the temporary code that you need will go to
         to get the main token
        :return: the link to follow
         and make authorization via login / password
        """
        request_service = RequestService()
        request = BuildAuthURL(
            client_id=client_id, scopes=scopes, redirect_uri=redirect_uri
        ).build_request()
        try:
            return BuildAuthURL.parse_http_response(
                await request_service.send_request(
                    request.endpoint,
                    request.http_method,
                    params=request.params,
                    data=request.data,
                    headers=request.headers,
                )
            )
        finally:
            await request_service.shutdown()

    @classmethod
    async def get_access_token(
        cls,
        code: str,
        client_id: str,
        redirect_uri: str = 'https://example.com',
        client_secret: Optional[str] = None,
    ) -> str:
        """
        Method for obtaining a token for requests to the YooMoney API

        :param code: the temporary code that was obtained in the base_authorize method
        :param client_id: application id, type string
        :param redirect_uri: the funnel where the temporary code will go,
         which is needed to get the main token
        :param client_secret: The secret word for authenticating the application.
         Specified if the service is registered with authentication.
        :return: YooMoney API TOKEN
        """
        rs = RequestService()
        try:
            return await rs.execute_api_method(
                GetAccessToken(
                    code=code,
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    client_secret=client_secret,
                )
            )
        finally:
            await rs.shutdown()

    async def revoke_api_token(self) -> None:
        """
        Method for revoking the rights of a token, while all its rights also disappear
        Documentation:
        https://yoomoney.ru/docs/wallet/using-api/authorization/revoke-access-token
        """
        await self._request_service.execute_api_method(RevokeAPIToken())

    @classmethod
    def create_pay_form(
        cls,
        receiver: str,
        quick_pay_form: str,
        targets: str,
        payment_type: str,
        amount: Union[int, float],
        form_comment: Optional[str] = None,
        short_dest: Optional[str] = None,
        label: Optional[str] = None,
        comment: Optional[str] = None,
        success_url: Optional[str] = None,
        need_fio: Optional[bool] = None,
        need_email: Optional[bool] = None,
        need_phone: Optional[bool] = None,
        need_address: Optional[bool] = None,
    ) -> str:
        """
        The YooMoney form is a set of fields with information about a transfer.
        You can embed payment form into your interface (for instance, a website or blog).
        When the sender pushes the button, the details from the form are sent to YooMoney
        and an order for a transfer to your wallet is initiated.

        Detail docs: https://yoomoney.ru/docs/payment-buttons/using-api/forms?lang=en

        Possible values for quick_pay_form:
           * shop - for a multi purpose form;
           * small - for a button;
           * donate - for a charity form.

        @param receiver: Number of the YooMoney wallet which money from senders is credited to.
        @param quick_pay_form:
        @param targets: Payment purpose.
        @param payment_type: Payment method. Possible values: PC, AC, MC
        @param amount: 	Transfer amount (the amount debited from the sender).
        @param form_comment: Name of the transfer in sender’s history
                (for transfers from a wallet or linked bank card). Displayed in sender’s wallet.
                The simplest way to create it is to combine the names of the store and product.
                For instance:  My Store: white valenki boots
        @param short_dest: Name of the transfer on the confirmation page.
               We recommend using the same name as formcomment
        @param label: The label that a site or app assigns to a certain transfer.
                      For instance, a code or order identifier may be used for this label.
        @param comment: The field in which you can transfer_money sender’s comments.
        @param success_url: URL where the user is redirected after the transfer.
        @param need_fio: Sender’s full name required.
        @param need_email: Sender’s email address required.
        @param need_phone: Sender’s phone number required.
        @param need_address: Sender’s address required.
        @return: link to payment form
        """
        payload = make_payload(
            **{
                'receiver': receiver,
                'quickpay-form': quick_pay_form,
                'targets': targets,
                'paymentType': payment_type,
                'sum': amount,
                'formcomment': form_comment,
                'short-dest': short_dest,
                'label': label,
                'comment': comment,
                'successURL': success_url,
                'need-fio': need_fio,
                'need-email': need_email,
                'need-phone': need_phone,
                'need-address': need_address,
            }
        )
        base_url = 'https://yoomoney.ru/quickpay/confirm.xml?'
        params = ''.join(f'&{key}={value}' for key, value in payload.items())
        return base_url + params

    async def retrieve_account_info(self) -> AccountInfo:
        """
        Method for getting information about user account
        Detailed documentation:
        https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        return await self._request_service.execute_api_method(RetrieveAccountInfo())

    async def operation_history(
        self,
        operation_types: Optional[Iterable[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        start_record: Optional[int] = None,
        records: int = 30,
        label: Optional[Union[str, int]] = None,
        in_detail: bool = False,
    ) -> OperationHistory:
        """
        More details:
        https://yoomoney.ru/docs/wallet/user-account/operation-history\n
        The method allows you to view the history of operation_history (in whole or in part) in page mode.
        History records are displayed in reverse chronological order from most recent to earlier.

        Possible values: \n
        DEPOSITION — refill ;\n
        PAYMENT — consumption;\n
        INCOMING(incoming-transfers-unaccepted) — unaccepted incoming P2P transfers of any type.\n

        :param operation_types: Operation type
        :param label: string.
         Selection of payments by tag value.
         Selects payments that have a specified parameter value
         label of the request-payment call.
        :param start_date: Show operations from the moment in time
         (operations equal to start_date or later)
         If the parameter is absent, all operations are displayed.
        :param end_date: Output operations up to the point in time
            (operations older than end_date).
            If the parameter is absent, all operations are displayed.
        :param start_record: If the parameter is present, then operations will be displayed starting
          from start_record number.
         Operations are numbered from 0. More about paginated list output
        :param records:	The number of transaction history records requested.
         Valid values are from 1 to 100, the default is 30.
        :param in_detail:
        """
        return await self._request_service.execute_api_method(
            OperationHistoryMethod(
                operation_types=operation_types,
                start_record=start_record,
                start_date=start_date,
                records=records,
                label=label,
                in_detail=in_detail,
                end_date=end_date,
            )
        )

    async def operation_details(self, operation_id: Union[int, str]) -> OperationDetails:
        """
        Allows you to get detailed information about the operation from the history.
        Required token rights: operation-details.
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/user-account/operation-details

        :param operation_id: Operation ID
        """
        return await self._request_service.execute_api_method(
            OperationDetailsMethod(operation_id=operation_id)
        )

    async def make_cellular_payment(
        self, pattern_id: str, phone_number: str, amount: Union[int, float, str]
    ) -> Dict[str, Any]:
        return await self._request_service.execute_api_method(
            MakeCellularPayment(pattern_id=pattern_id, phone_number=phone_number, amount=amount)
        )

    async def transfer_money(
        self,
        to_account: str,
        amount: Union[int, float],
        pattern_id: str = 'p2p',
        protect: bool = False,
        comment_for_history: Optional[str] = None,
        comment: Optional[str] = None,
        expire_period: int = 1,
    ) -> Payment:
        """
        A method for sending money to another person's account or card.
        This function makes 2 requests at once, because of this you may feel a slight loss in performance,
          you can use the method
        make_request_payment and get the RequestPaymentResponse object,
        which contains information about a still unconfirmed payment \n
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/process-payments/process-payment

        :param pattern_id: Payment pattern ID
        :param to_account: string ID of the transfer recipient
         (account number, phone number or email).
        :param amount: Amount to be received
         (the invoice will be sent to the recipient's account after payment). MINIMUM AMOUNT 2.
         then you will need to pass card_type
         to search for a card in the list of your bank cards,
         and also optionally cvv2 code for making a payment
        :param comment_for_history: Comment to the translation,
         displayed in the sender's history.
        :param comment: Comment on the transfer, displayed to the recipient.
        :param protect: The value of the parameter is true - a sign that
         that the transfer is protected by a protection code.
         By default, there is no parameter (normal translation).
        :param expire_period: Number of days during which:
            the recipient of the transfer can enter the protection code and
            receive a transfer to your account,
            the recipient of the transfer on demand can receive the transfer.
            The parameter value must be in the range from 1 to 365.
            Optional parameter. The default is 1.


        """
        pre_payment = await self.make_request_payment(
            to_account=to_account,
            amount=amount,
            comment_for_history=comment_for_history,
            comment_for_receiver=comment,
            expire_period=expire_period,
            protect=protect,
            pattern_id=pattern_id,
        )
        return await self._request_service.execute_api_method(
            ProcessPayment(request_id=pre_payment.request_id)
        )

    async def make_request_payment(
        self,
        to_account: str,
        amount: Union[int, float],
        pattern_id: str = 'p2p',
        comment_for_history: Optional[str] = None,
        comment_for_receiver: Optional[str] = None,
        protect: bool = False,
        expire_period: int = 1,
    ) -> RequestPaymentResponse:
        """
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/process-payments/request-payment
        Creation of payment, verification of parameters and acceptance
        payment by the store or transfer of funds to the user account of YooMoney.
        This method is not recommended to be used directly, much
        it's easier to use transfer_money.
        Required token rights: to-account ("recipient id", "id type")

        :param pattern_id: Payment pattern ID
        :param to_account: string ID of the transfer recipient
         (account number, phone number or email).
        :param amount: Amount to be received
         (the invoice will be sent to the recipient's account after payment).
        :param comment_for_history: Comment to the translation,
         displayed in the sender's history.
        :param comment_for_receiver: string Comment to the translation,
         displayed to the recipient.
        :param protect: The value of the parameter is true - a sign that
         that the transfer is protected by a protection code.
         By default, there is no parameter (normal translation).
        :param expire_period: The number of days during which:
            the recipient of the transfer can enter the protection code
            and receive a transfer to your account,
            the recipient of the transfer on demand can receive the transfer.
            The parameter value must be in the range from 1 to 365.
            Optional parameter. The default is 1.
        """
        return await self._request_service.execute_api_method(
            RequestPayment(
                to_account=to_account,
                amount=amount,
                pattern_id=pattern_id,
                comment_for_history=comment_for_history,
                comment_for_receiver=comment_for_receiver,
                protect=protect,
                expire_period=expire_period,
            )
        )

    async def get_balance(self) -> float:
        return (await self.retrieve_account_info()).balance

    async def accept_incoming_transaction(
        self, operation_id: str, protection_code: str
    ) -> IncomingTransaction:
        """
        Acceptance of incoming transfers protected by a protection code,
        if you passed the protect parameter to the transfer_money method
        Number of reception attempts
        incoming transfer with a protection code is limited.
        When the number of attempts is exhausted, the transfer is automatically rejected
        (the transfer is returned to the sender).
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-accept

        :param operation_id: Operation identifier,
         the value of the operation_id parameter of the history () method response
        :param protection_code: Protection code. A string of 4 decimal digits.
         Indicated for an incoming transfer protected by a protection code.
         Not available for on-demand transfers.
        """
        return await self._request_service.execute_api_method(
            AcceptIncomingTransfer(operation_id=operation_id, protection_code=protection_code)
        )

    async def reject_incoming_transfer(self, operation_id: str) -> Dict[str, str]:
        """
        Cancellation of incoming transfers protected by a protection code if you transferred
         in the transfer_money method the protect parameter,
        and transfers on demand. \n
        If the transfer is canceled, it is returned to the sender. \n
        Required token rights: incoming-transfers
        Docs:
        https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-reject

        :param operation_id: Operation identifier, parameter value
         operation_id of history () method response.
        """
        return await self._request_service.execute_api_method(
            RejectIncomingTransfer(operation_id=operation_id)
        )

    async def check_if_operation_exists(
        self,
        check_fn: typing.Callable[[OperationDetails], bool],
        operation_types: Optional[Iterable[str]] = None,
        max_records: int = 100,
        check_timeout: Optional[float] = None,
    ) -> bool:
        """
        Method for verifying a transaction.
        This method uses self.operation_history (rows = rows) to receive payments.
        For a little optimization, you can decrease rows by setting it,
        however, this does not guarantee the correct result

        :param check_fn:
        :param operation_types: payment type
        :param max_records: number of payments to be checked
        :param check_timeout:
        :return: bool, is there such a transaction in the payment history
        """
        operation_history = await self.operation_history(
            operation_types=operation_types, records=max_records
        )
        get_operation_details_coroutines = [
            self.operation_details(op.id) for op in operation_history
        ]

        for future in asyncio.as_completed(
            get_operation_details_coroutines, timeout=check_timeout
        ):
            if check_fn(await future):
                return True

        return False
