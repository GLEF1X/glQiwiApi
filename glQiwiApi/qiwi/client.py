"""
Gracefully and lightweight wrapper to deal with QIWI API
It's an open-source project so you always can improve the quality of code/API by
adding something of your own...
Easy to integrate to Telegram bot, which was written on aiogram or another async/sync library.

"""
from __future__ import annotations

import uuid
import warnings
from abc import ABC
from contextlib import suppress
from copy import deepcopy
from datetime import datetime
from typing import (
    List,
    Tuple,
    Dict,
    Union,
    Optional,
    Any,
    Pattern,
    Match,
    cast,
    Iterable,
    Type,
)

from glQiwiApi.core import RequestManager, constants
from glQiwiApi.core.constants import DEFAULT_CACHE_TIME
from glQiwiApi.core.mixins import (
    ContextInstanceMixin,
    ToolsMixin,
    DataMixin,
    HandlerCollectionMixin,
)
from glQiwiApi.ext.url_builder import WebhookURL
from glQiwiApi.qiwi.settings import QiwiRouter, QiwiKassaRouter, QiwiApiMethods
from glQiwiApi.types import (
    QiwiAccountInfo,
    Transaction,
    Statistic,
    Limit,
    Account,
    Balance,
    Identification,
    Sum,
    Card,
    Restriction,
    Commission,
    CrossRate,
    PaymentMethod,
    FreePaymentDetailsFields,
    PaymentInfo,
    OrderDetails,
    Bill,
    OptionalSum,
    P2PKeys,
    RefundBill,
    WebHookConfig,
    N,
    TransactionType,
    InvoiceStatus,
)
from glQiwiApi.utils.decorators import allow_response_code, override_error_messages
from glQiwiApi.utils.exceptions import APIError, InvalidData
from glQiwiApi.utils.format_casts import datetime_to_iso8601
from glQiwiApi.utils.payload import (
    make_payload,
    check_dates,
    parse_iterable_to_list_of_objects,
    patch_p2p_create_payload,
    get_new_card_data,
    get_qiwi_master_data,
    parse_commission_request_payload,
    retrieve_card_data,
    set_data_to_wallet,
    check_dates_for_statistic_request,
    parse_limits,
    check_transaction,
)


def _is_copy_signal(kwargs: Dict[Any, bool]) -> bool:
    try:
        return kwargs.pop("__copy_signal__")
    except KeyError:
        return False


def _validate_params(
        api_access_token: Optional[str],
        phone_number: Optional[str],
        secret_p2p: Optional[str],
        without_context: bool,
        cache_time: Union[float, int],
) -> None:
    """Validating all parameters by `isinstance` function or `regex`"""
    import re

    if not isinstance(api_access_token, str):
        raise InvalidData(
            "Invalid type of api_access_token parameter, required `string`,"
            "you have passed %s" % type(api_access_token)
        )
    if not isinstance(secret_p2p, str):
        raise InvalidData(
            "Invalid type of secret_p2p parameter, required `string`,"
            "you have passed %s" % type(secret_p2p)
        )
    if not isinstance(without_context, bool):
        raise InvalidData(
            "Invalid type of without_context parameter, required `bool`,"
            "you have passed %s" % type(without_context)
        )
    if not isinstance(cache_time, (float, int)):
        raise InvalidData(
            "Invalid type of cache_time parameter, required `bool`,"
            "you have passed %s" % type(cache_time)
        )

    phone_number_pattern: Pattern[str] = re.compile(
        r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$"
    )
    phone_number_match: Optional[Match[Any]] = re.fullmatch(
        phone_number_pattern, phone_number
    )

    if not phone_number_match:
        raise InvalidData(
            "Failed to verify parameter `phone_number` by regex. "
            "Please, enter the correct phone number."
        )


class BaseWrapper(ABC, ContextInstanceMixin["QiwiWrapper"]):
    def __init__(
            self,
            api_access_token: Optional[str] = None,
            phone_number: Optional[str] = None,
            secret_p2p: Optional[str] = None,
            without_context: bool = False,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME,  # 0 by default
            validate_params: bool = False,
            proxy: Any = None,
    ) -> None:
        """
        :param api_access_token: QIWI API token received from https://qiwi.com/api
        :param phone_number: your phone number starting with +
        :param secret_p2p: QIWI P2P secret key received from https://p2p.qiwi.com/
        :param without_context: bool, indicates whether the object of the class will be
         a "global" variable or will be used in an async with context
        :param cache_time:Time of caching requests in seconds,
         default 0, respectively
         the request will not use the cache by default, the maximum time
         caching 60 seconds
        :param proxy: The proxy that will be used when creating a session may slow down
            API work
        """
        if validate_params:
            _validate_params(
                api_access_token=api_access_token,
                cache_time=cache_time,
                secret_p2p=secret_p2p,
                phone_number=phone_number,
                without_context=without_context,
            )

        if isinstance(phone_number, str):
            self.phone_number = phone_number.replace("+", "")
            if self.phone_number.startswith("8"):
                self.phone_number = "7" + self.phone_number[1:]

        self._router = QiwiRouter()
        self._p2p_router = QiwiKassaRouter()
        self._requests = RequestManager(
            without_context=without_context,
            messages=self._router.config.ERROR_CODE_NUMBERS,
            cache_time=cache_time,
            proxy=proxy,
        )
        self.api_access_token = api_access_token
        self.secret_p2p = secret_p2p

        self.set_current(self)  # type: ignore

    @property
    def request_manager(self) -> RequestManager:
        return self._requests

    @request_manager.setter
    def request_manager(self, other: RequestManager) -> None:
        if not isinstance(other, RequestManager):
            raise TypeError(
                f"Expected `RequestManager` instance, despite got {type(other)}"
            )
        self._requests = other

    def _auth_token(self, headers: Dict[Any, Any], p2p: bool = False) -> Dict[Any, Any]:
        if not p2p:
            headers["Authorization"] = headers["Authorization"].format(
                token=self.api_access_token
            )
        else:
            headers["Authorization"] = headers["Authorization"].format(
                token=self.secret_p2p
            )
        return headers

    @property
    def stripped_number(self) -> str:
        """returns number, in which the `+` sign is removed"""
        try:
            return self.phone_number.replace("+", "")
        except AttributeError:
            raise InvalidData(
                "You should pass on phone number to execute this method"
            ) from None

    def __new__(
            cls: Type[N],
            api_access_token: Optional[str] = None,
            phone_number: Optional[str] = None,
            secret_p2p: Optional[str] = None,
            without_context: bool = False,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
            *args: Any,
            **kwargs: Any,
    ) -> N:
        if (
                not isinstance(api_access_token, str)
                and not isinstance(secret_p2p, str)  # noqa: W503
                and not _is_copy_signal(kwargs)  # noqa: W503
        ):
            raise RuntimeError("Unable to initialize instance without tokens")

        return super().__new__(cls)  # type: ignore


class QiwiWrapper(
    BaseWrapper,
    ToolsMixin,
    HandlerCollectionMixin,
    DataMixin
):
    """
    Delegates the work of QIWI API, webhooks, polling.
    Fast and versatile wrapper.

    """

    __slots__ = (
        "api_access_token",
        "phone_number",
        "secret_p2p",
        "_requests",
        "_router",
        "_p2p_router",
        "_dispatcher",
        "__context_instance",
    )

    async def _register_webhook(
            self, web_url: Optional[str], txn_type: int = 2
    ) -> WebHookConfig:
        """
        This method register a new webhook

        :param web_url: service url
        :param txn_type:  0 => incoming, 1 => outgoing, 2 => all
        :return: Active Hooks
        """
        response = await self._requests.send_request(
            "PUT",
            QiwiApiMethods.REG_WEBHOOK,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            params={"hookType": 1, "param": web_url, "txnType": txn_type},
        )
        return WebHookConfig.parse_obj(response)

    async def get_current_webhook(self) -> WebHookConfig:
        """
        List of active (active) notification handlers, associated with your wallet can be obtained with this request.
        Since now only one type of hook is used - webhook, then the response contains only one data object
        """
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.GET_CURRENT_WEBHOOK,
            self._router,
            headers=self._auth_token(self._router.default_headers),
        )
        return WebHookConfig.parse_obj(response)

    async def _send_test_notification(self) -> Dict[Any, Any]:
        """
        Use this request to test your webhooks handler.
        Test notification is sent to the address specified during the call register_webhook
        """
        return await self._requests.send_request(
            "GET",
            QiwiApiMethods.SEND_TEST_NOTIFICATION,
            self._router,
            headers=self._auth_token(self._router.default_headers),
        )

    async def get_webhook_secret_key(self, hook_id: str) -> str:
        """
        Each notification contains a digital signature of the message, encrypted with a key.
        To obtain a signature verification key, use this request.

        :param hook_id: UUID of webhook
        :return: Base64 encoded key
        """
        resp = await self._requests.send_request(
            "GET",
            QiwiApiMethods.GET_WEBHOOK_SECRET,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            hook_id=hook_id,
        )
        return cast(str, resp["key"])

    async def delete_current_webhook(self) -> Optional[Dict[str, str]]:
        """Method to delete webhook"""
        try:
            hook = await self.get_current_webhook()
        except APIError as ex:
            raise APIError(
                message=" You didn't register any webhook to delete ",
                status_code="422",
                traceback_info=ex.traceback_info,
            ) from None
        return await self._requests.send_request(
            "DELETE",
            QiwiApiMethods.DELETE_CURRENT_WEBHOOK,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            hook_id=hook.hook_id,
        )

    async def change_webhook_secret(self, hook_id: str) -> str:
        """
        Use this request to change the encryption key for notifications.

        :param hook_id: UUID of webhook
        :return: Base64 encoded key
        """
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.CHANGE_WEBHOOK_SECRET,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            hook_id=hook_id,
        )
        return cast(str, response["key"])

    async def bind_webhook(
            self,
            url: Optional[Union[str, WebhookURL]] = None,
            transactions_type: int = 2,
            *,
            send_test_notification: bool = False,
            delete_old: bool = False,
    ) -> Tuple[Optional[WebHookConfig], str]:
        """
        [NON-API] EXCLUSIVE method to register new webhook or get old

        :param url: service url
        :param transactions_type: 0 => incoming, 1 => outgoing, 2 => all
        :param send_test_notification:  test_qiwi will send
         you test webhook update
        :param delete_old: boolean, if True - delete old webhook

        :return: Tuple of Hook and Base64-encoded key
        """
        key: Optional[str] = None
        if isinstance(url, WebhookURL):
            url = url.render()

        if delete_old:
            with suppress(APIError):
                await self.delete_current_webhook()

        try:
            # Try to register new webhook
            webhook = await self._register_webhook(url, transactions_type)
        except (APIError, TypeError):
            # Catching exceptions, if webhook already was registered or TypeError because missing url to bind
            try:
                webhook = await self.get_current_webhook()
            except APIError as ex:
                raise APIError(
                    message="An error occurred while getting the current webhook config. Most likely you did not call "
                            "method `QiwiWrapper.bind_webhook(...)` to register webhook"
                            " or did not pass on url to register it",
                    status_code=ex.status_code,
                    traceback_info=ex.traceback_info,
                ) from None
            key = await self.get_webhook_secret_key(webhook.hook_id)
            return webhook, key

        if send_test_notification:
            await self._send_test_notification()

        if not isinstance(key, str):
            key = await self.get_webhook_secret_key(webhook.hook_id)

        return webhook, key

    @override_error_messages(
        {
            404: {
                "message": "Wrong card number entered, possibly"
                           "the card to which you transfer is blocked"
            }
        }
    )
    async def _detect_mobile_number(self, phone_number: str) -> str:
        """
        Help method for getting phone ID

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = self._router.default_headers
        headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        response = await self._requests.make_request(
            url="https://qiwi.com/mobile/detect.action",
            method="POST",
            headers=headers,
            data={"phone": phone_number},
        )
        return cast(str, response["message"])

    async def get_balance(self, *, account_number: int = 1) -> Sum:
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.GET_BALANCE,
            self._router,
            headers=headers,
            phone_number=self.phone_number,
        )
        return Sum.parse_obj(response["accounts"][account_number - 1]["balance"])

    async def transactions(
            self,
            rows: int = 50,
            operation: TransactionType = TransactionType.ALL,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
    ) -> List[Transaction]:
        """
        Method for receiving transactions on the account
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        Possible values for the operation parameter:
         - 'ALL'
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'

        :param rows: number of transactions you want to receive
        :param operation: The type of operations in the report for selection.
        :param start_date:The starting date for searching for payments.
                            Used only in conjunction with end_date.
        :param end_date: the end date of the search for payments.
                            Used only in conjunction with start_date.
        """
        if rows > 50 or rows <= 0:
            raise InvalidData("You can check no more than 50 transactions")
        headers = self._auth_token(self._router.default_headers)
        payload_data = check_dates(
            start_date=start_date,
            end_date=end_date,
            payload_data={"rows": rows, "operation": operation.value},
        )
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.TRANSACTIONS,
            self._router,
            params=payload_data,
            headers=headers,
            stripped_number=self.stripped_number,
        )
        return parse_iterable_to_list_of_objects(
            cast(Iterable[Any], response.get("data")), Transaction
        )

    async def transaction_info(
            self, transaction_id: Union[str, int], transaction_type: TransactionType
    ) -> Transaction:
        """
        Method for obtaining complete information about a transaction

        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#txn_info

        :param transaction_id:
        :param transaction_type: only IN or OUT
        :return: Transaction object
        """
        headers = self._auth_token(self._router.default_headers)
        payload_data = {"type": transaction_type.value}
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.TRANSACTION_INFO,
            self._router,
            headers=headers,
            params=payload_data,
            transaction_id=transaction_id,
        )
        return Transaction.parse_obj(response)

    async def check_restriction(self) -> List[Restriction]:
        """
        Method to check limits on your qiwi wallet
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: List where the dictionary is located with restrictions,
         if there are no restrictions, it returns an empty list
        """
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.CHECK_RESTRICTION,
            self._router,
            headers=headers,
            phone_number=self.phone_number,
        )
        return parse_iterable_to_list_of_objects(iterable=response, model=Restriction)

    @property
    async def identification(self) -> Identification:
        warnings.warn(
            "`QiwiWrapper.identification` async property has beign deprecated, and will be removed in next versions, "
            "use `QiwiWrapper.get_identification(...)` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.get_identification()

    async def get_identification(self) -> Identification:
        """
        This method allows get your wallet identification data
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#ident
        """
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.GET_IDENTIFICATION,
            self._router,
            headers=headers,
            phone_number=self.phone_number,
        )
        return Identification.parse_obj(response)

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: TransactionType = TransactionType.IN,
            sender: Optional[str] = None,
            rows_num: int = 50,
            comment: Optional[str] = None,
    ) -> bool:
        """
        [ NON API METHOD ]

        Method for verifying a transaction.
        This method uses self.transactions (rows = rows) "under the hood" to check payment.

        For a little optimization, you can decrease rows by setting it,
        however, this does not guarantee the correct result

        Possible values for the transaction_type parameter:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'


        :param amount: amount of payment
        :param transaction_type: type of payment
        :param sender: number of receiver
        :param rows_num: number of payments to be checked
        :param comment: comment by which the transaction will be verified
        """
        if rows_num > 50 or rows_num <= 0:
            raise InvalidData("You can check no more than 50 transactions.")
        transactions = await self.transactions(rows=rows_num)
        return check_transaction(
            transactions=transactions,
            transaction_type=transaction_type,
            comment=comment,
            amount=amount,
            sender=sender,
        )

    async def get_limits(
            self, limit_types: Optional[List[str]] = None
    ) -> Dict[str, Limit]:
        """
        Function for getting limits on the qiwi wallet account
        Returns wallet limits as a list,
        if there is no limit for a certain country, then it does not include it in the list
        Detailed documentation:

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits
        """
        headers = self._auth_token(self._router.default_headers)
        limit_types = limit_types or self._router.config.DEFAULT_LIMIT_TYPES
        # payload of limit types must be dict in format like array of strings {
        #    "types[0]": "Some type",
        #    "types[1]": "some other type",
        #    "types[n]": "n type"
        # }
        payload = {
            f"types[{index}]": limit_type
            for index, limit_type in enumerate(limit_types)
        }
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.GET_LIMITS,
            self._router,
            headers=headers,
            params=payload,
            stripped_number=self.stripped_number,
        )
        return parse_limits(response)

    async def get_list_of_cards(self) -> List[Card]:
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET", QiwiApiMethods.GET_LIST_OF_CARDS, self._router, headers=headers
        )
        return parse_iterable_to_list_of_objects(iterable=response, model=Card)

    async def authenticate(
            self,
            birth_date: str,
            first_name: str,
            last_name: str,
            patronymic: str,
            passport: str,
            oms: Optional[str] = None,
            inn: Optional[str] = None,
            snils: Optional[str] = None,
    ) -> Dict[Any, Any]:
        """
        This request allows you to send data to identify your QIWI wallet.
        It is allowed to identify no more than 5 wallets per owner

        To identify the wallet, you must send your full name, passport series number and date of birth.
        If the data has been verified, then the response will display
        your TIN and simplified wallet identification will be installed.
        If the data has not been verified,
        the wallet remains in the "Minimum" status.

        :param birth_date: Date of birth as a format string 1998-02-11
        :param first_name: First name
        :param last_name: Last name
        :param patronymic: Middle name
        :param passport: Series / Number of the passport. Ex: 4400111222
        :param oms:
        :param snils:
        :param inn:
        """

        payload = {
            "birthDate": birth_date,
            "firstName": first_name,
            "inn": inn,
            "lastName": last_name,
            "middleName": patronymic,
            "oms": oms,
            "passport": passport,
            "snils": snils,
        }
        headers = self._auth_token(self._router.default_headers)
        return await self._requests.send_request(
            "POST",
            QiwiApiMethods.AUTHENTICATE,
            self._router,
            stripped_number=self.stripped_number,
            headers=headers,
            data=self._requests.filter_dict(payload),
        )

    @override_error_messages(
        {
            422: {
                "message": "It is impossible to receive a check due to the fact that "
                           "the transaction for this ID has not been completed,"
                           "that is, an error occurred during the transaction"
            }
        }
    )
    async def get_receipt(
            self,
            transaction_id: Union[str, int],
            transaction_type: TransactionType,
            file_format: str = "PDF",
    ) -> bytes:
        """
        Method for receiving a receipt in byte format or file. \n
        Possible transaction_type values:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'

        :param transaction_id: transaction id, can be obtained by calling the to_wallet method, to_card
        :param transaction_type: type of transaction: 'IN', 'OUT', 'QIWI_CARD'
        :param file_format: format of file
        """
        headers = self._auth_token(self._router.default_headers)
        data = {"type": transaction_type.value, "format": file_format}
        url = self._router.build_url(
            QiwiApiMethods.GET_RECEIPT, transaction_id=transaction_id
        )
        return await self._requests.retrieve_bytes(
            url, "GET", params=data, headers=headers
        )

    async def get_account_info(self) -> QiwiAccountInfo:
        """
        ?????????? ?????? ?????????????????? ???????????????????? ???? ????????????????

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET", QiwiApiMethods.ACCOUNT_INFO, self._router, headers=headers
        )
        return QiwiAccountInfo.parse_obj(response)

    async def fetch_statistics(
            self,
            start_date: datetime,
            end_date: datetime,
            operation: TransactionType = TransactionType.ALL,
            sources: Optional[List[str]] = None,
    ) -> Statistic:
        """
        This query is used to get summary statistics
        by the amount of payments for a given period.
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        :param start_date:The start date of the statistics period.
        :param end_date: End date of the statistics period.
        :param operation: The type of operations taken into account when calculating statistics.
         Allowed values:
            ALL - ?????? ????????????????,
            IN - ???????????? ????????????????????,
            OUT - ???????????? ??????????????,
            QIWI_CARD - ???????????? ?????????????? ???? ???????????? QIWI (QVC, QVP).
            ???? ?????????????????? ALL.
        :param sources: The sources of payments
            QW_RUB - ???????????????? ???????? ????????????????,
            QW_USD - ???????? ???????????????? ?? ????????????????,
            QW_EUR - ???????? ???????????????? ?? ????????,
            CARD - ?????????????????????? ?? ?????????????????????????? ?? ???????????????? ???????????????????? ??????????,
            MK - ???????? ???????????????????? ??????????????????. ???????? ???? ????????????,
            ?????????????????????? ?????? ?????????????????? ??????????????.
        """
        headers = self._auth_token(self._router.default_headers)
        check_dates_for_statistic_request(start_date=start_date, end_date=end_date)
        params = {
            "startDate": datetime_to_iso8601(start_date),
            "endDate": datetime_to_iso8601(end_date),
            "operation": operation.value,
        }
        if sources:
            params.update({"sources": " ".join(sources)})
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.FETCH_STATISTICS,
            self._router,
            params=params,
            headers=headers,
            stripped_number=self.stripped_number,
        )
        return Statistic.parse_obj(response)

    async def list_of_balances(self) -> List[Account]:
        """
        The request gets the current account balances of your QIWI Wallet.
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.LIST_OF_BALANCES,
            self._router,
            headers=headers,
            stripped_number=self.stripped_number,
        )
        return parse_iterable_to_list_of_objects(
            cast(Iterable[Any], response.get("accounts")), Account
        )

    @allow_response_code(201)
    async def create_new_balance(
            self, currency_alias: str
    ) -> Optional[Dict[str, bool]]:
        """
        The request creates a new account and balance in your QIWI Wallet

        :param currency_alias: New account alias
        """
        headers = self._auth_token(self._router.default_headers)
        payload = {"alias": currency_alias}
        return await self._requests.send_request(
            "POST",
            QiwiApiMethods.CREATE_NEW_BALANCE,
            self._router,
            headers=headers,
            data=payload,
            stripped_number=self.stripped_number,
        )

    async def available_balances(self) -> List[Balance]:
        """
        The request displays account aliases, available for creation in your QIWI Wallet

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.AVAILABLE_BALANCES,
            self._router,
            headers=headers,
            stripped_number=self.stripped_number,
        )
        return parse_iterable_to_list_of_objects(iterable=response, model=Balance)

    @allow_response_code(status_code=204)
    async def set_default_balance(self, currency_alias: str) -> Dict[Any, Any]:
        """
        The request sets up an account for your QIWI Wallet, whose balance will be used for funding
        all payments by default.
        The account must be contained in the list of accounts, you can get the list by calling
        list_of_balances method

        :param currency_alias:
        """
        headers = self._auth_token(self._router.default_headers)
        return await self._requests.send_request(
            "PATCH",
            QiwiApiMethods.SET_DEFAULT_BALANCE,
            self._router,
            headers=headers,
            json={"defaultAccount": True},
            stripped_number=self.stripped_number,
            currency_alias=currency_alias,
        )

    async def to_wallet(
            self,
            to_number: str,
            amount: Union[str, float, int],
            currency: str = "643",
            comment: Optional[str] = None,
    ) -> PaymentInfo:
        """
        Method for transferring money to another wallet \n
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#p2p

        :param to_number: recipient number
        :param amount: the amount of money you want to transfer
        :param currency: special currency code
        :param comment: payment comment
        """
        data = set_data_to_wallet(
            data=deepcopy(self._router.config.QIWI_TO_WALLET),
            to_number=to_number,
            trans_sum=amount,
            currency=currency,
            comment=comment,
        )
        data.headers = self._auth_token(headers=data.headers)
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.TO_WALLET,
            self._router,
            json=data.json,
            headers=data.headers,
        )
        return PaymentInfo.parse_obj(response)

    async def to_card(self, trans_sum: Union[float, int], to_card: str) -> PaymentInfo:
        """
        Method for sending funds to the card.
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards
        """
        data = retrieve_card_data(
            default_data=self._router.config.QIWI_TO_CARD,
            to_card=to_card,
            trans_sum=trans_sum,
            auth_maker=self._auth_token,
        )
        privat_card_id = await self._detect_card_number(card_number=to_card)
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.TO_CARD,
            self._router,
            headers=data.headers,
            json=data.json,
            privat_card_id=privat_card_id,
        )
        return PaymentInfo.parse_obj(response)

    async def _detect_card_number(self, card_number: str) -> str:
        """
        Method for getting card ID

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        response = await self._requests.make_request(
            "https://qiwi.com/card/detect.action",
            "POST",
            headers=headers,
            data={"cardNumber": card_number},
        )
        return cast(str, response["message"])

    async def calc_commission(
            self, to_account: str, pay_sum: Union[int, float]
    ) -> Commission:
        """
        Full calc_commission of QIWI Wallet is refunded for payment in favor of the specified provider
        taking into account all tariffs for a given set of payment details.

        :param to_account: ?????????? ?????????? ?????? ???????? ????????????????
        :param pay_sum: ??????????, ???? ?????????????? ???? ???????????? ???????????? ????????????????
        :return: Commission object
        """
        payload, special_code = parse_commission_request_payload(
            default_data=self._router.config.COMMISSION_DATA,
            auth_maker=self._auth_token,
            to_account=to_account,
            pay_sum=pay_sum,
        )
        code = special_code or await self._detect_card_number(to_account)
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.COMMISSION,
            self._router,
            headers=payload.headers,
            json=payload.json,
            special_code=code,
        )
        return Commission.parse_obj(response)

    async def get_cross_rates(self) -> List[CrossRate]:
        """
        The method returns the current exchange rates and cross-rates of the QIWI Bank's currencies.

        """
        response = await self._requests.send_request(
            "GET", QiwiApiMethods.GET_CROSS_RATES, self._router
        )
        return parse_iterable_to_list_of_objects(
            iterable=response["result"], model=CrossRate
        )

    async def payment_by_payment_details(
            self,
            payment_sum: Sum,
            payment_method: PaymentMethod,
            fields: FreePaymentDetailsFields,
            payment_id: Optional[str] = None,
    ) -> PaymentInfo:
        """
        Payment for services of commercial organizations according to their bank details.

        :param payment_id: payment id, if not transmitted, is used uuid4 by default
        :param payment_sum: a Sum object, which indicates the amount of the payment
        :param payment_method: payment method
        :param fields: payment details
        """
        payload = {
            "id": payment_id if isinstance(payment_id, str) else str(uuid.uuid4()),
            "sum": payment_sum.dict(),
            "paymentMethod": payment_method.dict(),
            "fields": fields.dict(),
        }
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.SPECIAL_PAYMENT,
            self._router,
            headers=self._router.default_headers,
            json=payload,
        )
        return PaymentInfo.parse_obj(response)

    async def buy_qiwi_master(self) -> PaymentInfo:
        """
        Method for buying QIWI Master package
        To call API methods, you need the QIWI Wallet API token with permissions to do the following:
        1. Management of virtual cards,
        2. Request information about the wallet profile,
        3. View payment history,
        4. Making payments without SMS.
        You can choose these rights when creating a new api token, to use api QIWI Master
        """
        payload = get_qiwi_master_data(
            self.stripped_number, self._router.config.QIWI_MASTER
        )
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.BUY_QIWI_MASTER,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            json=payload,
        )
        return PaymentInfo.parse_obj(response)

    async def __pre_qiwi_master_request(
            self, card_alias: str = "qvc-cpa"
    ) -> OrderDetails:
        """Method for Issuing QIWI Master Virtual Card"""
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.PRE_QIWI_REQUEST,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            json={"cardAlias": card_alias},
            stripped_number=self.stripped_number,
        )
        return OrderDetails.parse_obj(response)

    async def _confirm_qiwi_master_request(
            self, card_alias: str = "qvc-cpa"
    ) -> OrderDetails:
        """Confirmation of the card issue order"""
        details = await self.__pre_qiwi_master_request(card_alias)
        response = await self._requests.send_request(
            "PUT",
            QiwiApiMethods.CONFIRM_QIWI_MASTER,
            self._router,
            headers=self._auth_token(self._router.default_headers),
            stripped_number=self.stripped_number,
            order_id=details.order_id,
        )
        return OrderDetails.parse_obj(response)

    async def __buy_new_qiwi_card(self, **kwargs: Any) -> Optional[OrderDetails]:
        kwargs.update(data=self._router.config.QIWI_MASTER)
        payload = get_new_card_data(**kwargs)
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.BUY_QIWI_CARD,
            self._router,
            json=payload,
            headers=self._auth_token(self._router.default_headers),
        )
        return OrderDetails.parse_obj(response)

    async def issue_qiwi_master_card(
            self, card_alias: str = "qvc-cpa"
    ) -> Optional[OrderDetails]:
        """
        Issuing a new card using the Qiwi Master API

        When issuing a card, 3, and possibly 3 requests are made, namely, according to the following scheme:
            - __pre_qiwi_master_request - this method creates a request
            - _confirm_qiwi_master_request - confirms the issue of the card
            - __buy_new_qiwi_card - buys a new card,
              if such a card is not free
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#qiwi-master-issue-card
        """
        pre_response = await self._confirm_qiwi_master_request(card_alias)
        if pre_response.status == "COMPLETED":
            return pre_response
        return await self.__buy_new_qiwi_card(
            ph_number=self.stripped_number, order_id=pre_response.order_id
        )

    async def _cards_qiwi_master(self) -> Dict[Any, Any]:
        return await self._requests.send_request(
            "GET",
            QiwiApiMethods.CARDS_QIWI_MASTER,
            self._router,
            headers=self._auth_token(self._router.default_headers),
        )

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """Use this method to cancel unpaid invoice."""
        if not self.secret_p2p:
            raise InvalidData("???? ?????????? p2p ??????????")
        data = deepcopy(self._p2p_router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.REJECT_P2P_BILL,
            self._p2p_router,
            headers=headers,
            bill_id=bill_id,
        )
        return Bill.parse_obj(response)

    async def check_p2p_bill_status(self, bill_id: str) -> str:
        """
        Method for checking the status of a p2p transaction.\n
        Possible transaction types: \n
        WAITING	Bill is waiting for pay	\n
        PAID	Bill was paid	\n
        REJECTED	Bill was rejected\n
        EXPIRED	?????????? ?????????? ?????????? ??????????????. ???????? ???? ??????????????\n
        Docs:
        https://developer.qiwi.com/ru/p2p-payments/?shell#invoice-status

        :param bill_id:
        :return: status of bill
        """
        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.CHECK_P2P_BILL_STATUS,
            self._p2p_router,
            headers=headers,
            bill_id=bill_id,
        )
        return Bill.parse_obj(response).status.value

    async def create_p2p_bill(
            self,
            amount: Union[int, float],
            bill_id: Optional[str] = None,
            comment: Optional[str] = None,
            life_time: Optional[datetime] = None,
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
        :param life_time: the date until which the invoice will be available for payment.
        :param comment:
        :param theme_code:
        :param pay_source_filter: When you open the form, the following will be displayed
         only the translation methods specified in this parameter
        """
        if not isinstance(bill_id, (str, int)):
            bill_id = str(uuid.uuid4())
        life_time = datetime_to_iso8601(life_time or constants.get_default_bill_time())  # type: ignore
        data = deepcopy(self._p2p_router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        payload = patch_p2p_create_payload(
            data, amount, str(life_time), comment, theme_code, pay_source_filter
        )
        response = await self._requests.send_request(
            "PUT",
            QiwiApiMethods.CREATE_P2P_BILL,
            self._p2p_router,
            headers=headers,
            json=payload,
            bill_id=bill_id,
        )
        return Bill.parse_obj(response)

    async def get_bills(
            self, rows_num: int, bill_statuses: str = "READY_FOR_PAY"
    ) -> List[Bill]:
        warnings.warn(
            "`QiwiWrapper.get_bills` is deprecated, and will be removed in next versions, "
            "use `QiwiWrapper.retrieve_bills(...)` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.retrieve_bills(rows=rows_num, statuses=bill_statuses)

    async def retrieve_bills(
            self, rows: int, statuses: str = constants.DEFAULT_BILL_STATUSES
    ) -> List[Bill]:
        """
        A method for getting a list of your wallet's outstanding bills.

        The list is built in reverse chronological order.

        By default, the list is paginated with 50 items each,
        but you can specify a different number of elements (no more than 50).

        Filters by billing time can be used in the request,
        the initial account identifier.
        """
        params = make_payload(**locals())
        headers = self._auth_token(self._router.default_headers)
        if rows > 50:
            raise InvalidData("You can get no more than 50 invoices")
        response = await self._requests.send_request(
            "GET",
            QiwiApiMethods.GET_BILLS,
            self._router,
            headers=headers,
            params=params,
        )
        return parse_iterable_to_list_of_objects(response["bills"], Bill)

    async def pay_the_invoice(self, invoice_uid: str, currency: str) -> InvoiceStatus:
        """
        Execution of unconditional payment of the invoice without SMS-confirmation.

        ! Warning !
        To use this method correctly you need to tick "???????????????????? ???????????????? ?????? SMS"
        when registering QIWI API and retrieve token

        :param invoice_uid: Bill ID in QIWI system
        :param currency:
        """
        payload = make_payload(**locals())
        headers = self._auth_token(self._router.default_headers)
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.GET_BILLS,
            self._router,
            headers=headers,
            json=payload,
        )
        return InvoiceStatus.parse_obj(response)

    async def refund_bill(
            self,
            bill_id: Union[str, int],
            refund_id: Union[str, int],
            json_bill_data: Union[OptionalSum, Dict[str, Union[str, int]]],
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
        headers = self._auth_token(self._router.default_headers, p2p=True)
        json = (
            json_bill_data
            if isinstance(json_bill_data, dict)
            else json_bill_data.json()
        )
        response = await self._requests.send_request(
            "PUT",
            QiwiApiMethods.REFUND_BILL,
            self._router,
            headers=headers,
            json=json,
            refund_id=refund_id,
            bill_id=bill_id,
        )
        return RefundBill.parse_obj(response)

    async def create_p2p_keys(
            self, key_pair_name: str, server_notification_url: Optional[str] = None
    ) -> P2PKeys:
        """
        Creates new pair of P2P keys to interact with P2P QIWI API

        :param key_pair_name: P2P token pair name
        :param server_notification_url: url for webhooks
        """
        headers = self._auth_token(self._router.default_headers, p2p=True)
        data = {
            "keysPairName": key_pair_name,
            "serverNotificationsUrl": server_notification_url,
        }
        response = await self._requests.send_request(
            "POST",
            QiwiApiMethods.CREATE_P2P_KEYS,
            self._router,
            headers=headers,
            json=data,
        )
        return P2PKeys.parse_obj(response)
