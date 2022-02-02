from typing import TypeVar, NoReturn, Optional, List, Any


class YooMoneyError(Exception):
    def __init__(self, error_code: Optional[str] = None):
        super().__init__(error_code)


_T = TypeVar("_T")


def match_error(err_code: str) -> NoReturn:
    _MatchErrorMixin.detect(err_code)


class _MatchErrorMixin:
    match = ""
    explanation: str

    __subclasses: List[Any] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super(_MatchErrorMixin, cls).__init_subclass__(**kwargs)
        if not hasattr(cls, f"_{cls.__name__}__group"):
            cls.__subclasses.append(cls)

    @classmethod
    def check(cls, message: str) -> bool:
        """
        Compare pattern with message
        :param message: always must be in lowercase
        :return: bool
        """
        return cls.match.lower() in message

    @classmethod
    def detect(cls, err_code: str) -> NoReturn:
        err_code = err_code.lower()
        for err in cls.__subclasses:
            if err is cls:
                continue
            if err.check(err_code):
                formatted_explanation = err.on_match(err_code, explanation=err.explanation)
                raise err(formatted_explanation or err_code)
        raise cls(err_code)  # type: ignore  # noqa

    @classmethod
    def on_match(cls, err_code: str, explanation: Optional[str] = None) -> Optional[str]:
        return cls.explanation


class BadRequest(YooMoneyError, _MatchErrorMixin):
    __group = True


class PaymentError(YooMoneyError, _MatchErrorMixin):
    __group = True


class IllegalParam(BadRequest):
    match = "illegal_param"
    explanation = "Invalid value for the {param} parameter."

    @classmethod
    def on_match(cls, err_code: str, explanation: Optional[str] = None) -> Optional[str]:
        param_name = err_code.removeprefix(cls.match)  # type: ignore
        param_name_without_underscore = param_name[1:]
        return explanation.format(param=param_name_without_underscore)  # type: ignore


class ProcessPaymentError(PaymentError):
    explanation = "Something went wrong while processing payment"


class ContractNotFound(ProcessPaymentError):
    match = "contract_not_found"
    explanation = "There is no existing unconfirmed payment with the specified request_id"


class NotEnoughFunds(ProcessPaymentError):
    match = "not_enough_funds"
    explanation = "The payer’s account does not have sufficient funds to make the payment. Additional funds should be credited to the account, and a new payment will need to be processed."


class LimitExceeded(ProcessPaymentError):
    match = "limit_exceeded"
    explanation = "One of the operation limits was exceeded:"
    "For the total amount of operations for the access token granted."
    "For the total amount of operations over a period of time for the access token granted."
    "YooMoney restrictions for various types of operations."


class MoneySourceNotAvailable(ProcessPaymentError):
    match = "money_source_not_available"
    explanation = "The requested payment method (money_source) is not available for this payment."


class PaymentRefused(ProcessPaymentError):
    match = "payment_refused"
    explanation = "The payment was refused. Possible reasons:"
    "The merchant refused to accept the payment (checkOrder request)."
    "The transfer to a YooMoney user is not possible (for example, the recipient’s wallet has reached the maximum amount allowed)."


class AuthorizationReject(ProcessPaymentError):
    match = "authorization_reject"
    explanation = """Authorization of the payment was refused. Possible reasons:

    The bank card expired.
    The issuing bank refused to perform the transaction for the card.
    Exceeds the limit for this user.
    A transaction with the current parameters is forbidden for this user.
    The user did not accept the User Agreement for the YooMoney service."""


class AccountBlocked(ProcessPaymentError):
    match = "account_blocked"
    explanation = """The user’s account has been blocked. In order to unblock the account, the user must be redirected to the address specified in the account_unblock_uri field."""
