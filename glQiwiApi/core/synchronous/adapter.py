from __future__ import annotations

import inspect
import pathlib
from abc import ABCMeta
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, Tuple, List
from typing import TypeVar, Type

from glQiwiApi.core import ContextInstanceMixin, constants
from glQiwiApi.core.constants import DEFAULT_CACHE_TIME
from glQiwiApi.core.mixins import DataMixin
from glQiwiApi.core.synchronous.decorator import async_as_sync
from glQiwiApi.core.synchronous.model_adapter import AdaptedBill, adapt_type
from glQiwiApi.ext.url_builder import WebhookURL
from glQiwiApi.qiwi.client import BaseWrapper, QiwiWrapper
from glQiwiApi.types import (
    WebHookConfig,
    Sum,
    Transaction,
    Restriction,
    Limit,
    Card,
    QiwiAccountInfo,
    Account,
    Balance,
    Commission,
    CrossRate,
    PaymentMethod,
    FreePaymentDetailsFields,
    PaymentInfo,
    OrderDetails,
    RefundBill,
    OptionalSum,
    P2PKeys,
    Statistic,
    AccountInfo,
    Operation,
    OperationDetails,
    PreProcessPaymentResponse,
    Payment,
    IncomingTransaction,
    OperationType,
    TransactionType,
)
from glQiwiApi.yoo_money.client import YooMoneyAPI

_T = TypeVar("_T")


class SyncAdapterMeta(ABCMeta):
    def __new__(
        mcs: Type[_T],
        name: str,
        bases: Tuple[Any, ...],
        attrs: Dict[Any, Any],
        **extra: Any,
    ) -> _T:
        adapted_instance = extra.get("adapted_cls")
        for attr, value in adapted_instance.__dict__.items():
            if inspect.iscoroutinefunction(value):
                if not attr.startswith("_"):
                    attrs[attr] = async_as_sync(
                        sync_shutdown_callback=adapt_type
                    ).__call__(value)
                else:
                    attrs[attr] = value

        return super().__new__(mcs, name, bases, attrs)  # type: ignore


class SyncAdaptedQiwi(
    BaseWrapper,
    ContextInstanceMixin["SyncAdaptedQiwi"],
    DataMixin,
    metaclass=SyncAdapterMeta,
    adapted_cls=QiwiWrapper,
):
    def __init__(
        self,
        api_access_token: Optional[str] = None,
        phone_number: Optional[str] = None,
        secret_p2p: Optional[str] = None,
        cache_time: Union[float, int] = DEFAULT_CACHE_TIME,  # 0 by default
        validate_params: bool = False,
        proxy: Any = None,
    ) -> None:
        super(SyncAdaptedQiwi, self).__init__(
            api_access_token,
            phone_number=phone_number,
            secret_p2p=secret_p2p,
            without_context=True,
            cache_time=cache_time,
            validate_params=validate_params,
            proxy=proxy,
        )

    def get_current_webhook(self) -> WebHookConfig:
        """
        List of active (active) notification handlers, associated with your wallet can be obtained with this request.
        Since now only one type of hook is used - webhook, then the response contains only one data object
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_webhook_secret_key(self, hook_id: str) -> str:
        """
        Each notification contains a digital signature of the message, encrypted with a key.
        To obtain a signature verification key, use this request.

        :param hook_id: UUID of webhook
        :return: Base64 encoded key
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_account_info(self) -> QiwiAccountInfo:
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def delete_current_webhook(self) -> Optional[Dict[str, str]]:
        """Method to delete webhook"""
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def change_webhook_secret(self, hook_id: str) -> str:
        """
        Use this request to change the encryption key for notifications.

        :param hook_id: UUID of webhook
        :return: Base64 encoded key
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def bind_webhook(
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
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_balance(self, *, account_number: int = 1) -> Sum:
        """Метод для получения баланса киви"""
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def transactions(
        self,
        rows_num: int = 50,
        operation: str = "ALL",
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

        :param rows_num: number of transactions you want to receive
        :param operation: Тип операций в отчете, для отбора.
        :param start_date:The starting date for searching for payments.
                            Used only in conjunction with end_date.
        :param end_date: the end date of the search for payments.
                            Used only in conjunction with start_date.
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def transaction_info(
        self, transaction_id: Union[str, int], transaction_type: str
    ) -> Transaction:
        """
        Метод для получения полной информации о транзакции\n
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#txn_info

        :param transaction_id: номер транзакции
        :param transaction_type: тип транзакции, может быть только IN или OUT
        :return: Transaction object
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def check_restriction(self) -> List[Restriction]:
        """
        Method to check limits on your qiwi wallet
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: List where the dictionary is located with restrictions,
         if there are no restrictions, it returns an empty list
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def check_transaction(
        self,
        amount: Union[int, float],
        transaction_type: str = "IN",
        sender: Optional[str] = None,
        rows_num: int = 50,
        comment: Optional[str] = None,
    ) -> bool:
        """
        [ NON API METHOD ]
        Method for verifying a transaction.
        This method uses self.transactions (rows = rows)
        to receive payments.
        For a little optimization, you can decrease rows by setting it,
        however, this does not guarantee the correct result
        Possible values for the transaction_type parameter:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'


        :param amount: сумма платежа
        :param transaction_type: тип платежа
        :param sender: номер получателя
        :param rows_num: кол-во платежей, которое будет проверяться
        :param comment: комментарий, по которому будет проверяться транзакция
        :return: bool, есть ли такая транзакция в истории платежей
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_limits(self) -> Dict[str, Limit]:
        """
        Function for getting limits on the qiwi wallet account
        Returns wallet limits as a list,
        if there is no limit for a certain country, then it does not include it in the list
        Detailed documentation:

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_list_of_cards(self) -> List[Card]:
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def authenticate(
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
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_receipt(
        self,
        transaction_id: Union[str, int],
        transaction_type: str,
        dir_path: Union[str, pathlib.Path, None] = None,
        file_name: Optional[str] = None,
    ) -> Union[bytes, int]:
        """
        Method for receiving a receipt in byte format or file. \n
        Possible transaction_type values:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'

        :param transaction_id: transaction id, can be obtained by calling the to_wallet method, to_card
        :param transaction_type: type of transaction: 'IN', 'OUT', 'QIWI_CARD'
        :param dir_path: path to the directory where you want to save the receipt, if not specified, returns bytes
        :param file_name:File name without format. Example: my_receipt
        :return:pdf file in byte form or number of bytes written
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def fetch_statistics(
        self,
        start_date: Union[datetime, timedelta],
        end_date: Union[datetime, timedelta],
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
            ALL - все операции,
            IN - только пополнения,
            OUT - только платежи,
            QIWI_CARD - только платежи по картам QIWI (QVC, QVP).
            По умолчанию ALL.
        :param sources: The sources of payments
            QW_RUB - рублевый счет кошелька,
            QW_USD - счет кошелька в долларах,
            QW_EUR - счет кошелька в евро,
            CARD - привязанные и непривязанные к кошельку банковские карты,
            MK - счет мобильного оператора. Если не указан,
            учитываются все источники платежа.
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def list_of_balances(self) -> List[Account]:
        """
        Запрос выгружает текущие балансы счетов вашего QIWI Кошелька.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list

        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def create_new_balance(self, currency_alias: str) -> Optional[Dict[str, bool]]:
        """
        The request creates a new account and balance in your QIWI Wallet

        :param currency_alias: New account alias
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def available_balances(self) -> List[Balance]:
        """
        The request displays account aliases, available for creation in your QIWI Wallet

        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def set_default_balance(self, currency_alias: str) -> Any:
        """
        The request sets up an account for your QIWI Wallet, whose balance will be used for funding
        all payments by default.
        The account must be contained in the list of accounts, you can get the list by calling
        list_of_balances method

        :param currency_alias: Псевдоним нового счета,
         можно получить из list_of_balances
        :return: Возвращает значение из декоратора allow_response_code
         Пример результата, если запрос был проведен успешно: {"success": True}
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def to_wallet(
        self,
        to_number: str,
        trans_sum: Union[str, float, int],
        currency: str = "643",
        comment: str = "+comment+",
    ) -> str:
        """
        Method for transferring money to another wallet \n
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#p2p

        :param to_number: recipient number
        :param trans_sum: the amount of money you want to transfer
        :param currency: special currency code
        :param comment: payment comment
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def to_card(self, trans_sum: Union[float, int], to_card: str) -> Optional[str]:
        """
        Method for sending funds to the card.
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards

        :param trans_sum: сумма перевода
        :param to_card: номер карты получателя
        :return:
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def calc_commission(
        self, to_account: str, pay_sum: Union[int, float]
    ) -> Commission:
        """
        Full calc_commission of QIWI Wallet is refunded for payment in favor of the specified provider
        taking into account all tariffs for a given set of payment details.

        :param to_account: номер карты или киви кошелька
        :param pay_sum: сумма, за которую вы хотите узнать комиссию
        :return: Commission object
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def get_cross_rates(self) -> List[CrossRate]:
        """
        The method returns the current exchange rates and cross-rates of the QIWI Bank's currencies.

        """
        pass

    def payment_by_payment_details(
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
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def buy_qiwi_master(self) -> PaymentInfo:
        """
        Method for buying QIWI Master package
        To call API methods, you need the QIWI Wallet API token with permissions to do the following:
        1. Management of virtual cards,
        2. Request information about the wallet profile,
        3. View payment history,
        4. Making payments without SMS.
        You can choose these rights when creating a new api token, to use api QIWI Master
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def issue_qiwi_master_card(
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
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def reject_p2p_bill(self, bill_id: str) -> AdaptedBill:
        """Use this method to cancel unpaid invoice."""
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def check_p2p_bill_status(self, bill_id: str) -> str:
        """
        Method for checking the status of a p2p transaction.\n
        Possible transaction types: \n
        WAITING	Bill is waiting for pay	\n
        PAID	Bill was paid	\n
        REJECTED	Bill was rejected\n
        EXPIRED	Время жизни счета истекло. Счет не оплачен\n
        Docs:
        https://developer.qiwi.com/ru/p2p-payments/?shell#invoice-status

        :param bill_id:
        :return: status of bill
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def create_p2p_bill(
        self,
        amount: Union[int, float],
        bill_id: Optional[str] = None,
        comment: Optional[str] = None,
        life_time: Optional[datetime] = None,
        theme_code: Optional[str] = None,
        pay_source_filter: Optional[List[str]] = None,
    ) -> AdaptedBill:
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
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def retrieve_bills(
        self, rows: int, statuses: str = constants.DEFAULT_BILL_STATUSES
    ) -> List[AdaptedBill]:
        """
        A method for getting a list of your wallet's outstanding bills.
        The list is built in reverse chronological order.
        By default, the list is paginated with 50 items each,
        but you can specify a different number of elements (no more than 50).
        Filters by billing time can be used in the request,
        the initial account identifier.
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def refund_bill(
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
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover

    def create_p2p_keys(
        self, key_pair_name: str, server_notification_url: Optional[str] = None
    ) -> P2PKeys:
        """
        :param key_pair_name: P2P token pair name (arbitrary string)
        :param server_notification_url: url for webhooks, optional
         параметр
        """
        pass  # real implementation in the QiwiWrapper class  # pragma: no cover


class SyncAdaptedYooMoney(
    ContextInstanceMixin["SyncAdaptedYooMoney"],
    metaclass=SyncAdapterMeta,
    adapted_cls=YooMoneyAPI,
):
    @classmethod
    def build_url_for_auth(
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    @classmethod
    def get_access_token(
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def revoke_api_token(self) -> Optional[Dict[str, bool]]:
        """
        Method for revoking the rights of a token, while all its rights also disappear
        Documentation:
        https://yoomoney.ru/docs/wallet/using-api/authorization/revoke-access-token
        """
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def account_info(self) -> AccountInfo:
        """
        Method for getting information about user account
        Detailed documentation:
        https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

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
        Подробная документация:
        https://yoomoney.ru/docs/wallet/user-account/operation-history\n
        The method allows you to view the history of transactions (in whole or in part) in page mode.
        History records are displayed in reverse chronological order from most recent to earlier.
        Possible values:
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def transaction_info(self, operation_id: str) -> OperationDetails:
        """
        Allows you to get detailed information about the operation from the history.
        Required token rights: operation-details.
        More detailed documentation:
        https://yoomoney.ru/docs/wallet/user-account/operation-details

        :param operation_id: Operation ID
        """
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def _pre_process_payment(
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def send(
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def get_balance(self) -> float:
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def accept_incoming_transaction(
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def reject_transaction(self, operation_id: str) -> Dict[str, str]:
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
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover

    def check_transaction(
        self,
        amount: Union[int, float],
        transaction_type: str = "in",
        comment: Optional[str] = None,
        rows_num: int = 100,
        recipient: Optional[str] = None,
    ) -> bool:
        """
        Method for verifying a transaction.
        This method uses self.transactions (rows = rows) to receive payments.
        For a little optimization, you can decrease rows by setting it,
        however, this does not guarantee the correct result

        :param amount: payment amount
        :param transaction_type: payment type
        :param recipient: recipient number
        :param rows_num: number of payments to be checked
        :param comment: comment by which the transaction will be verified
        :return: bool, is there such a transaction in the payment history
        """
        pass  # real implementation in the YooMoneyAPI class  # pragma: no cover
