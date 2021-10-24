"""
Provides effortless work with YooMoney API using asynchronous requests.

"""
from __future__ import annotations

import asyncio
import warnings
from datetime import datetime
from typing import List, Dict, Any, Union, Optional, Tuple, cast

from glQiwiApi.core.abc.wrapper import Wrapper
from glQiwiApi.core.constants import NO_CACHING
from glQiwiApi.core.mixins import DataMixin, ContextInstanceMixin
from glQiwiApi.core.request_service import RequestService
from glQiwiApi.core.session.holder import AbstractSessionHolder
from glQiwiApi.types import (
    AccountInfo,
    OperationType,
    Operation,
    OperationDetails,
    PreProcessPaymentResponse,
    Payment,
    IncomingTransaction,
)
from glQiwiApi.types.yoomoney_types.types import Card
from glQiwiApi.utils.exceptions import CantParseUrl, InvalidPayload
from glQiwiApi.utils.payload import (
    parse_auth_link,
    retrieve_base_headers_for_yoomoney,
    parse_iterable_to_list_of_objects,
    check_params,
    parse_amount,
    check_transactions_payload,
    make_payload, filter_none,
)
from glQiwiApi.utils.validators import String
from glQiwiApi.yoo_money.settings import YooMoneyRouter, YooMoneyMethods


class YooMoneyAPI(Wrapper, DataMixin, ContextInstanceMixin["YooMoneyAPI"]):
    """
    That class implements processing requests to YooMoney
    It is convenient in that it does not just give json such objects,
    and all this converts into pydantic models.
    To work with this class, you need to register a token,
    using the guide on the official github of the project

    """
    api_access_token = String(optional=False)

    def __init__(
            self,
            api_access_token: str,
            cache_time: Union[float, int] = NO_CACHING,
            session_holder: Optional[AbstractSessionHolder[Any]] = None,
    ) -> None:
        """
        The constructor accepts a token obtained from the method class get_access_token
         and the special attribute without_context

        :param api_access_token: api token for requests
        :param cache_time: Time to cache requests in seconds,
         default 0, respectively the request will not use the cache by default
        :param session_holder: obtains session and helps to manage session lifecycle. You can pass
                               your own session holder, for example using httpx lib and use it
        """
        self.api_access_token = api_access_token
        self._router = YooMoneyRouter()
        self._request_service = RequestService(self._router.config.ERROR_CODE_MESSAGES,
                                               cache_time, session_holder=session_holder)

        self.set_current(self)

    def get_request_service(self) -> RequestService:
        return self._request_service

    def _auth_token(self, headers: Dict[Any, Any]) -> Dict[Any, Any]:
        headers["Authorization"] = headers["Authorization"].format(
            token=self.api_access_token
        )
        return headers

    @classmethod
    async def build_url_for_auth(
            cls, scope: List[str], client_id: str, redirect_uri: str = "https://example.com"
    ) -> Optional[str]:
        """
        Method to get the link for further authorization and obtaining a token

        :param scope: OAuth2 authorization of the application by the user,
         the rights are transferred by the list.
        :param client_id: application id, type string
        :param redirect_uri: a funnel where the temporary code that you need will go to
         to get the main token
        :return: the link to follow
         and make authorization via login / password
        """
        router = YooMoneyRouter()
        headers = retrieve_base_headers_for_yoomoney()
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(scope),
        }
        url = router.build_url(YooMoneyMethods.BUILD_URL_FOR_AUTH)
        rs = RequestService(error_messages=router.config.ERROR_CODE_MESSAGES)
        response = await rs.text_content(url, "POST", headers=headers, data=params)
        try:
            return parse_auth_link(response)
        except IndexError:
            raise CantParseUrl(
                "Could not find the authorization link in the response from "
                "the api, check the client_id value"
            )
        finally:
            await rs.shutdown()

    @classmethod
    async def get_access_token(
            cls,
            code: str,
            client_id: str,
            redirect_uri: str = "https://example.com",
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
        router = YooMoneyRouter()
        headers = retrieve_base_headers_for_yoomoney(content_json=True)
        params = {
            "code": code,
            "client_id": client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "client_secret": client_secret,
        }
        rs = RequestService(error_messages=router.config.ERROR_CODE_MESSAGES)
        try:
            response = await rs.api_request(
                "POST",
                YooMoneyMethods.GET_ACCESS_TOKEN,
                router,
                headers=headers,
                data=params,
            )
        finally:
            await rs.shutdown()
        return cast(str, response["access_token"])

    async def revoke_api_token(self) -> Optional[Dict[str, bool]]:
        """
        Method for revoking the rights of a token, while all its rights also disappear
        Documentation:
        https://yoomoney.ru/docs/wallet/using-api/authorization/revoke-access-token
        """
        headers = self._auth_token(retrieve_base_headers_for_yoomoney(auth=True))
        return await self._request_service.api_request(
            "POST", YooMoneyMethods.REVOKE_API_TOKEN, self._router, headers=headers
        )

    @property
    async def account_info(self) -> AccountInfo:
        warnings.warn(
            "`QiwiWrapper.get_account_info` property is deprecated, and will be removed in next versions, "
            "use `QiwiWrapper.retrieve_account_info(...)` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.retrieve_account_info()

    @classmethod
    def create_pay_form(cls, receiver: str,
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
                        need_address: Optional[bool] = None) -> str:
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
        @param comment: The field in which you can send sender’s comments.
        @param success_url: URL where the user is redirected after the transfer.
        @param need_fio: Sender’s full name required.
        @param need_email: Sender’s email address required.
        @param need_phone: Sender’s phone number required.
        @param need_address: Sender’s address required.
        @return: link to payment form
        """
        payload = make_payload(**{
            "receiver": receiver,
            "quickpay-form": quick_pay_form,
            "targets": targets,
            "paymentType": payment_type,
            "sum": amount,
            "formcomment": form_comment,
            "short-dest": short_dest,
            "label": label,
            "comment": comment,
            "successURL": success_url,
            "need-fio": need_fio,
            "need-email": need_email,
            "need-phone": need_phone,
            "need-address": need_address
        })
        router = YooMoneyRouter()
        base_url = router.build_url(YooMoneyMethods.QUICK_PAY_FORM)
        params = "".join(f"&{key}={value}" for key, value in payload.items())
        return base_url + params

    async def retrieve_account_info(self) -> AccountInfo:
        """
        Method for getting information about user account
        Detailed documentation:
        https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        response = await self._request_service.api_request(
            "POST", YooMoneyMethods.ACCOUNT_INFO, self._router, headers=headers
        )
        return AccountInfo.parse_obj(response)

    async def transactions(
            self,
            operation_types: Optional[
                Union[List[OperationType], Tuple[OperationType, ...]]
            ] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            start_record: Optional[int] = None,
            records: int = 30,
            label: Optional[Union[str, int]] = None,
    ) -> List[Operation]:
        """
        More details:
        https://yoomoney.ru/docs/wallet/user-account/operation-history\n
        The method allows you to view the history of transactions (in whole or in part) in page mode.
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
        """
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        data = {"records": records, "label": label}
        payload = check_transactions_payload(
            data, records, operation_types, start_date, end_date, start_record
        )
        response = await self._request_service.api_request(
            "POST",
            YooMoneyMethods.TRANSACTIONS,
            self._router,
            headers=headers,
            data=filter_none(payload),
        )
        return parse_iterable_to_list_of_objects(
            iterable=cast(List[Any], response.get("operations")), model=Operation
        )

    async def transaction_info(self, operation_id: str) -> OperationDetails:
        """
        Allows you to get detailed information about the operation from the history.
        Required token rights: operation-details.
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/user-account/operation-details

        :param operation_id: Operation ID
        """
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        response = await self._request_service.api_request(
            "POST",
            YooMoneyMethods.TRANSACTION_INFO,
            self._router,
            data={"operation_id": operation_id},
            headers=headers,
        )
        return OperationDetails.parse_obj(response)

    async def _pre_process_payment(
            self,
            to_account: str,
            amount: Union[int, float],
            pattern_id: str = "p2p",
            comment_for_history: Optional[str] = None,
            comment_for_receiver: Optional[str] = None,
            protect: bool = False,
            expire_period: int = 1,
    ) -> PreProcessPaymentResponse:
        """
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/process-payments/request-payment
        Creation of payment, verification of parameters and acceptance
        payment by the store or transfer of funds to the user account of YooMoney.
        This method is not recommended to be used directly, much
        it's easier to use send.
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
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        payload = {
            "pattern_id": pattern_id,
            "to": to_account,
            "amount_due": amount,
            "comment": comment_for_history,
            "message": comment_for_receiver,
            "expire_period": expire_period,
            "codepro": protect,
        }
        response = await self._request_service.api_request(
            "POST",
            YooMoneyMethods.PRE_PROCESS_PAYMENT,
            self._router,
            headers=headers,
            data=payload,
        )
        return PreProcessPaymentResponse.parse_obj(response)

    async def send(
            self,
            to_account: str,
            amount: Union[int, float],
            money_source: str = "wallet",
            pattern_id: str = "p2p",
            cvv2_code: str = "",
            card_type: Optional[str] = None,
            protect: bool = False,
            comment_for_history: Optional[str] = None,
            comment: Optional[str] = None,
            expire_period: int = 1,
    ) -> Payment:
        """
        A method for sending money to another person's account or card.
        This function makes 2 requests at once, because of this you may feel a slight loss in performance,
          you can use the method
        _pre_process_payment and get the PreProcessPaymentResponse object,
        which contains information about a still unconfirmed payment \n
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/process-payments/process-payment

        :param pattern_id: Payment pattern ID
        :param to_account: string ID of the transfer recipient
         (account number, phone number or email).
        :param amount: Amount to be received
         (the invoice will be sent to the recipient's account after payment). MINIMUM AMOUNT 2.
        :param money_source: The requested payment method.
         wallet - from the user's account, if you want to use a card,
         then you will need to pass card_type
         to search for a card in the list of your bank cards,
         and also optionally cvv2 code for making a payment
        :param comment_for_history: Comment to the translation,
         displayed in the sender's history.
        :param card_type: Bank card type, you need to fill in,
         only if you want to debit funds from your card
        :param cvv2_code: optional, may not be passed, however
         if payment by card is required,
         the parameter should be passed
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
        if amount < 2:
            raise InvalidPayload(
                "Enter the amount that is more than the minimum (2 or more)"
            )
        pre_payment = await self._pre_process_payment(
            to_account=to_account,
            amount=amount,
            comment_for_history=comment_for_history,
            comment_for_receiver=comment,
            expire_period=expire_period,
            protect=protect,
            pattern_id=pattern_id,
        )
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        payload = {"request_id": pre_payment.request_id, "money_source": "wallet"}
        if (
                money_source == "card"
                and isinstance(pre_payment, PreProcessPaymentResponse)  # noqa: W503
                and pre_payment.money_source.cards.allowed == "true"  # type: ignore  # noqa: W503
        ):
            if not isinstance(card_type, str):
                cards = cast(Card, pre_payment.money_source.cards)  # type: ignore
                payload.update(
                    {"money_source": cards.items[0].item_id, "csc": cvv2_code}
                )
            else:
                cards = cast(Card, pre_payment.money_source.cards).items  # type: ignore
                for card in cards:
                    if card.item_type == card_type:  # type: ignore
                        payload.update(
                            {
                                "money_source": card.item_id,  # type: ignore
                                "csc": cvv2_code,
                            },
                        )
        response = await self._request_service.api_request(
            "POST",
            YooMoneyMethods.PROCESS_PAYMENT,
            self._router,
            headers=headers,
            data=payload,
        )
        return Payment.parse_obj(response).initialize(pre_payment.protection_code)

    async def get_balance(self) -> float:
        return (await self.retrieve_account_info()).balance

    async def accept_incoming_transaction(
            self, operation_id: str, protection_code: str
    ) -> IncomingTransaction:
        """
        Acceptance of incoming transfers protected by a protection code,
        if you passed the protect parameter to the send method
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
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        payload = {"operation_id": operation_id, "protection_code": protection_code}
        response = await self._request_service.api_request(
            "POST",
            YooMoneyMethods.ACCEPT_INCOMING_TRANSFER,
            self._router,
            headers=headers,
            data=payload,
        )
        return IncomingTransaction.parse_obj(response)

    async def reject_transaction(self, operation_id: str) -> Dict[str, str]:
        """
        Cancellation of incoming transfers protected by a protection code if you transferred
         in the send method the protect parameter,
        and transfers on demand. \n
        If the transfer is canceled, it is returned to the sender. \n
        Required token rights: incoming-transfers
        Docs:
        https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-reject

        :param operation_id: Operation identifier, parameter value
         operation_id of history () method response.
        """
        headers = self._auth_token(
            retrieve_base_headers_for_yoomoney(**self._router.config.content_and_auth)
        )
        return await self._request_service.api_request(
            "POST",
            YooMoneyMethods.INCOMING_TRANSFER_REJECT,
            self._router,
            headers=headers,
            data={"operation_id": operation_id},
        )

    async def check_transaction(
            self,
            amount: Union[int, float],
            operation_type: str = "in",
            comment: Optional[str] = None,
            rows: int = 100,
            recipient: Optional[str] = None,
    ) -> bool:
        """
        Method for verifying a transaction.
        This method uses self.transactions (rows = rows) to receive payments.
        For a little optimization, you can decrease rows by setting it,
        however, this does not guarantee the correct result

        :param amount: payment amount
        :param operation_type: payment type
        :param recipient: recipient number
        :param rows: number of payments to be checked
        :param comment: comment by which the transaction will be verified
        :return: bool, is there such a transaction in the payment history
        """
        types = [OperationType.from_input(operation_type)]
        transactions = await self.transactions(operation_types=types, records=rows)
        tasks = [self.transaction_info(txn.id) for txn in transactions]
        for detail in await asyncio.gather(*tasks):
            # Parse amount and comment,
            # because the parameters depend on the type of transaction
            amount_, comment_ = parse_amount(operation_type, detail)
            checked = check_params(amount_, amount, detail, operation_type)
            if checked and detail.status == "success":
                if comment_ == comment and detail.sender == recipient:
                    return True
                elif isinstance(comment, str) and isinstance(recipient, str):
                    continue
                elif comment_ == comment:
                    return True

        return False
