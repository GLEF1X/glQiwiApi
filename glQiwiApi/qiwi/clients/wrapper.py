from datetime import datetime
from typing import Optional, Union, Any, Type, TypeVar, Dict, List, Tuple

from glQiwiApi.base.types.amount import PlainAmount, AmountWithCurrency
from glQiwiApi.base.types.arbitrary import File
from glQiwiApi.core.cache.storage import CacheStorage
from glQiwiApi.core.mixins import DispatcherShortcutsMixin
from glQiwiApi.core.request_service import RequestServiceProto
from glQiwiApi.ext.webhook_url import WebhookURL
from glQiwiApi.qiwi import PaymentInfo, OrderDetails, PaymentDetails, PaymentMethod, CrossRate, Balance, \
    TransactionType, Statistic, QiwiAccountInfo, Card, Limit, Identification, Restriction, Transaction, \
    Source, History, WebhookInfo, Commission
from glQiwiApi.qiwi.clients.p2p.client import QiwiP2PClient
from glQiwiApi.qiwi.clients.p2p.types import PairOfP2PKeys, Bill, RefundedBill, InvoiceStatus
from glQiwiApi.qiwi.clients.wallet.client import QiwiWallet, AmountType
from glQiwiApi.qiwi.clients.wallet.methods.get_limits import ALL_LIMIT_TYPES

_T = TypeVar("_T")


class QiwiWrapper(DispatcherShortcutsMixin):
    """For backward compatibility with glQiwiApi <= 1.1.4"""

    def __init__(
            self,
            api_access_token: Optional[str] = None,
            phone_number: Optional[str] = None,
            secret_p2p: Optional[str] = None,
            cache_storage: Optional[CacheStorage] = None,
            request_service: Optional[RequestServiceProto] = None,
            shim_server_url: Optional[str] = None
    ) -> None:
        self._qiwi_wallet = QiwiWallet(api_access_token or "", phone_number, request_service, cache_storage)
        self._p2p_client = QiwiP2PClient(secret_p2p or "", request_service, cache_storage, shim_server_url)

    async def __aenter__(self) -> "QiwiWrapper":
        await self._qiwi_wallet.__aenter__()
        await self._p2p_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._qiwi_wallet.__aexit__(exc_type, exc_val, exc_tb)
        await self._p2p_client.__aexit__(exc_type, exc_val, exc_tb)

    def __new__(
            cls: Type[_T],
            api_access_token: Optional[str] = None,
            phone_number: Optional[str] = None,
            secret_p2p: Optional[str] = None,
            cache_time_in_seconds: Union[float, int] = 0,
            *args: Any,
            **kwargs: Any,
    ) -> _T:
        if (
                not isinstance(api_access_token, str)
                and not isinstance(secret_p2p, str)  # noqa: W503
        ):
            raise RuntimeError("Unable to initialize instance without tokens")

        return super().__new__(cls)  # type: ignore

    async def register_webhook(self, url: str, txn_type: int = 2) -> WebhookInfo:
        """
        This method register a new webhook

        :param url: service url
        :param txn_type:  0 => incoming, 1 => outgoing, 2 => all
        :return: Active Hooks
        """
        return await self._qiwi_wallet.register_webhook(url, txn_type)

    async def get_current_webhook(self) -> WebhookInfo:
        """
        List of active (active) notification handlers, associated with your wallet can be obtained with this request.
        Since now only one type of hook is used - webhook, then the response contains only one data object
        """
        return await self._qiwi_wallet.get_current_webhook()

    async def send_test_notification(self) -> Dict[Any, Any]:
        """
        Use this request to test your webhooks handler.
        Test notification is sent to the address specified during the call register_webhook
        """
        return await self._qiwi_wallet.send_test_webhook_notification()

    async def get_webhook_secret_key(self, hook_id: str) -> str:
        """
        Each notification contains a digital signature of the message, encrypted with a key.
        To obtain a signature verification key, use this request.

        :param hook_id: UUID of webhook
        :return: Base64 encoded key
        """
        return await self._qiwi_wallet.get_webhook_secret_key(hook_id)

    async def delete_current_webhook(self) -> Optional[Dict[str, str]]:
        """Method to delete webhook"""
        return await self._qiwi_wallet.delete_current_webhook()

    async def change_webhook_secret(self, hook_id: str) -> str:
        """
        Use this request to change the encryption key for notifications.

        :param hook_id: UUID of webhook
        :return: Base64 encoded key
        """
        return await self._qiwi_wallet.generate_new_webhook_secret(hook_id)

    async def bind_webhook(
            self,
            url: Union[str, WebhookURL],
            transactions_type: int = 2,
            *,
            send_test_notification: bool = False,
            delete_old: bool = False,
    ) -> Tuple[WebhookInfo, str]:
        """
        [NON-API] EXCLUSIVE method to register new webhook or get old

        :param url: service url
        :param transactions_type: 0 => incoming, 1 => outgoing, 2 => all
        :param send_test_notification:  test_qiwi will transfer_money
         you test webhook update
        :param delete_old: boolean, if True - delete old webhook

        :return: Tuple of Hook and Base64-encoded key
        """
        return await self._qiwi_wallet.bind_webhook(url, transactions_type=transactions_type,
                                                    send_test_notification=send_test_notification,
                                                    delete_old=delete_old)

    async def get_balance(self, *, account_number: int = 1) -> AmountWithCurrency:
        return await self._qiwi_wallet.get_balance(account_number=account_number)

    async def transactions(
            self,
            rows: int = 50,
            operation: TransactionType = TransactionType.ALL,
            sources: Optional[List[Source]] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
    ) -> History:
        """
        Method for receiving transactions on the account
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        :param rows: number of transactions you want to receive
        :param operation: The type of operations in the report for selection.
        :param sources: List of payment sources, for filter
        :param start_date: The starting date for searching for payments.
                            Used only in conjunction with end_date.
        :param end_date: the end date of the search for payments.
                            Used only in conjunction with start_date.
        """
        return await self._qiwi_wallet.history(rows, operation, sources, start_date, end_date)

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
        return await self._qiwi_wallet.get_transaction_info(transaction_id, transaction_type)

    async def get_restriction(self) -> List[Restriction]:
        """
        Method to check limits on your qiwi wallet
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: List where the dictionary is located with restrictions,
         if there are no restrictions, it returns an empty list
        """
        return await self._qiwi_wallet.get_restrictions()

    async def get_identification(self) -> Identification:
        """
        This method allows get your wallet identification data
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#ident
        """
        return await self._qiwi_wallet.get_identification()

    async def check_transaction(
            self,
            amount: AmountType,
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
        return await self._qiwi_wallet.check_transaction(
            amount, transaction_type, sender, rows_num, comment
        )

    async def get_limits(self, limit_types: List[str] = ALL_LIMIT_TYPES) -> Dict[str, Limit]:
        """
        Function for getting limits on the qiwi wallet account
        Returns wallet limits as a list,
        if there is no limit for a certain country, then it does not include it in the list
        Detailed documentation:

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits
        """
        return await self._qiwi_wallet.get_limits(limit_types)

    async def get_list_of_cards(self) -> List[Card]:
        return await self._qiwi_wallet.get_list_of_cards()

    async def authenticate(
            self,
            birth_date: str,
            first_name: str,
            last_name: str,
            middle_name: str,
            passport: str,
            oms: Optional[str] = None,
            inn: Optional[str] = None,
            snils: Optional[str] = None,
    ) -> Dict[Any, Any]:
        """
        This request allows you to transfer_money data to identify your QIWI wallet.
        It is allowed to identify no more than 5 wallets per owner

        To identify the wallet, you must transfer_money your full name, passport series number and date of birth.
        If the data has been verified, then the response will display
        your TIN and simplified wallet identification will be installed.
        If the data has not been verified,
        the wallet remains in the "Minimum" status.

        :param birth_date: Date of birth as a format string 1998-02-11
        :param first_name: First name
        :param last_name: Last name
        :param middle_name: Middle name
        :param passport: Series / Number of the passport. Ex: 4400111222
        :param oms:
        :param snils:
        :param inn:
        """
        return await self._qiwi_wallet.authenticate(
            birth_date, first_name, last_name, middle_name, passport, oms, inn, snils
        )

    async def get_receipt(
            self,
            transaction_id: Union[str, int],
            transaction_type: TransactionType,
            file_format: str = "PDF",
    ) -> File:
        """
        Method for receiving a receipt in byte format or file. \n
        Possible transaction_type values:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'

        :param transaction_id: transaction id, can be obtained by calling the transfer_money method,
         transfer_money_to_card
        :param transaction_type: type of transaction: 'IN', 'OUT', 'QIWI_CARD'
        :param file_format: format of file
        """
        return await self._qiwi_wallet.get_receipt(transaction_id, transaction_type, file_format)

    async def get_account_info(self) -> QiwiAccountInfo:
        """
        Метод для получения информации об аккаунте

        """
        return await self._qiwi_wallet.get_account_info()

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
        return await self._qiwi_wallet.fetch_statistics(start_date, end_date, operation, sources)

    async def list_of_balances(self) -> List[Balance]:
        """
        The request gets the current account balances of your QIWI Wallet.
        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list

        """
        return await self._qiwi_wallet.list_of_balances()

    async def create_new_balance(self, currency_alias: str) -> Optional[Dict[str, bool]]:
        """
        The request creates a new account and balance in your QIWI Wallet

        :param currency_alias: New account alias
        """
        return await self._qiwi_wallet.create_new_balance(currency_alias)

    async def available_balances(self) -> List[Balance]:
        """
        The request displays account aliases, available for creation in your QIWI Wallet

        """
        return await self._qiwi_wallet.available_balances()

    async def set_default_balance(self, currency_alias: str) -> Dict[Any, Any]:
        """
        The request sets up an account for your QIWI Wallet, whose balance will be used for funding
        all payments by default.
        The account must be contained in the list of accounts, you can get the list by calling
        list_of_balances method

        :param currency_alias:
        """
        return await self._qiwi_wallet.set_default_balance(currency_alias)

    async def transfer_money(
            self,
            to_phone_number: str,
            amount: Union[AmountType, str],
            comment: Optional[str] = None,
    ) -> PaymentInfo:
        """
        Method for transferring funds to wallet

        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#p2p

        :param to_phone_number: recipient number
        :param amount: the amount of money you want to transfer
        :param comment: payment comment
        """
        return await self._qiwi_wallet.transfer_money(to_phone_number, amount, comment)

    async def transfer_money_to_card(self, amount: AmountType, card_number: str) -> PaymentInfo:
        """
        Method for sending funds to the card.

        More detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards
        """
        return await self._qiwi_wallet.transfer_money_to_card(amount, card_number)

    async def predict_commission(self, to_account: str, pay_sum: AmountType) -> Commission:
        """
        Full calc_commission of QIWI Wallet is refunded for payment in favor of the specified provider
        taking into account all tariffs for a given set of payment details.

        :param to_account:
        :param pay_sum:
        :return: Commission object
        """
        return await self._qiwi_wallet.predict_commission(to_account, pay_sum)

    async def get_cross_rates(self) -> List[CrossRate]:
        """
        The method returns the current exchange rates and cross-rates of the QIWI Bank's currencies.

        """
        return await self._qiwi_wallet.get_cross_rates()

    async def payment_by_payment_details(
            self,
            payment_sum: AmountWithCurrency,
            payment_method: PaymentMethod,
            fields: PaymentDetails,
            payment_id: Optional[str] = None,
    ) -> PaymentInfo:
        """
        Payment for services of commercial organizations according to their bank details.

        :param payment_id: payment id, if not transmitted, is used uuid4 by default
        :param payment_sum: a Sum object, which indicates the amount of the payment
        :param payment_method: payment method
        :param fields: payment details
        """
        return await self._qiwi_wallet.payment_by_payment_details(
            payment_sum, payment_method, fields, payment_id
        )

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
        return await self._qiwi_wallet.buy_qiwi_master()

    async def issue_qiwi_master_card(self, card_alias: str = "qvc-cpa") -> Optional[OrderDetails]:
        """
        Issuing a new card using the Qiwi Master API

        When issuing a card, 3, and possibly 3 requests are made, namely,
        according to the following scheme:
            - _pre_qiwi_master_request - this method creates a request
            - _confirm_qiwi_master_request - confirms the issue of the card
            - _buy_new_qiwi_card - buys a new card,
              if such a card is not free
        Detailed documentation:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#qiwi-master-issue-card
        """
        return await self._qiwi_wallet.issue_qiwi_master_card(card_alias)

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """Use this method to cancel unpaid invoice."""
        return await self._p2p_client.reject_p2p_bill(bill_id)

    async def check_p2p_bill_status(self, bill_id: str) -> str:
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
        return await self._p2p_client.get_bill_status(bill_id)

    async def create_p2p_bill(
            self,
            amount: AmountType,
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
        return await self._p2p_client.create_p2p_bill(
            amount, bill_id, comment, life_time,
            theme_code, pay_source_filter
        )

    async def retrieve_bills(self, rows: int, statuses: str = "READY_FOR_PAY") -> List[Bill]:
        """
        A method for getting a list of your wallet's outstanding bills.

        The list is built in reverse chronological order.

        By default, the list is paginated with 50 items each,
        but you can specify a different number of elements (no more than 50).

        Filters by billing time can be used in the request,
        the initial account identifier.
        """
        return await self._qiwi_wallet.list_of_invoices(rows, statuses)

    async def pay_the_invoice(self, invoice_uid: str, currency: str) -> InvoiceStatus:
        """
        Execution of unconditional payment of the invoice without SMS-confirmation.

        ! Warning !
        To use this method correctly you need to tick "Проведение платежей без SMS"
        when registering QIWI API and retrieve token

        :param invoice_uid: Bill ID in QIWI system
        :param currency:
        """
        return await self._qiwi_wallet.pay_the_invoice(invoice_uid, currency)

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
        return await self._p2p_client.refund_bill(bill_id, refund_id, json_bill_data)

    async def create_p2p_keys(
            self, key_pair_name: str, server_notification_url: Optional[str] = None
    ) -> PairOfP2PKeys:
        """
        Creates a new pair of P2P keys to interact with P2P QIWI API

        :param key_pair_name: P2P token pair name
        :param server_notification_url: url for webhooks
        """
        return await self._p2p_client.create_pair_of_p2p_keys(key_pair_name, server_notification_url)
