from typing import ClassVar, NoReturn, Optional

from pydantic import BaseModel


class YooMoneyErrorSchema(BaseModel):
    error_code: str
    error_description: Optional[str] = None
    status: Optional[str] = None


class YooMoneyError(Exception):
    """
    There are some facts about YooMoney API errors:

    * Error in json format contains at least one field - error.
    * Error field defines short description of error(like error code).

    * Sometimes error can contain field error_description,
      that enrich error code with some human-readable explanation.
      Also, error can contain status field and some technical fields.

    """

    match_error_code: ClassVar[Optional[str]] = None
    _explanation: ClassVar[Optional[str]] = None

    def __init__(self, error_schema: YooMoneyErrorSchema) -> None:
        self.error_schema = error_schema

        if error_schema.error_description is None and self._explanation is not None:
            error_schema.error_description = self._explanation

    def __str__(self) -> str:
        str_ = ''
        if self.error_schema.error_description:
            str_ += f'{self.error_schema.error_description}\n'
            str_ += f'For debugging purposes: \n'
            str_ += f"{'':>4}error code = {self.error_schema.error_code}"
            if self.error_schema.status:
                str_ += f"{'':>4}status={self.error_schema.status}"
        else:
            str_ += f'{self.error_schema.error_code}'
            if self.error_schema.status:
                str_ += ','
                str_ += f'status={self.error_schema.status}'

        return str_

    def json(self) -> str:
        return self.error_schema.json()

    @classmethod
    def raise_most_appropriate_error(cls, error_schema: YooMoneyErrorSchema) -> NoReturn:
        for subclass in cls.__subclasses__():
            if not subclass.is_i_matching_error_code(error_schema):
                continue

            raise subclass(error_schema)

        raise TechnicalError(error_schema)

    @classmethod
    def is_i_matching_error_code(cls, error_schema: YooMoneyErrorSchema) -> bool:
        return error_schema.error_code == cls.match_error_code


class InvalidRequestError(YooMoneyError):
    match_error_code = 'invalid_request'
    _explanation = 'The request is missing required parameters, or parameters have unsupported or invalid values.'


class UnauthorizedClientError(YooMoneyError):
    match_error_code = 'unauthorized_client'
    _explanation = 'The client_id value is invalid, or the application does not have rights to request authorization (for example, its client_id has been blocked by YooMoney).'


class InvalidGrantError(YooMoneyError):
    match_error_code = 'invalid_grant'
    _explanation = 'The access_token could not be issued. Either the temporary authorization code was not issued by YooMoney, or it has expired, or an access_token has already been issued for this temporary authorization code (a duplicate request for an access token using the same temporary authorization code).'


class InsufficientScopeError(YooMoneyError):
    match_error_code = 'insufficient_scope'
    _explanation = 'The token does not have permissions for the requested operation.'


class IllegalParamError(YooMoneyError):
    def __init__(self, error_schema: YooMoneyErrorSchema):
        super(IllegalParamError, self).__init__(error_schema)
        _, _, self.param_name = self.error_schema.error_code.rpartition('illegal_param_')
        self.error_schema.error_description = f'Illegal value of "{self.param_name}" param.'

    @classmethod
    def is_i_matching_error_code(cls, error_schema: YooMoneyErrorSchema) -> bool:
        if not error_schema.error_code.startswith('illegal_param_'):
            return False

        return True


class IllegalParamsError(YooMoneyError):
    match_error_code = 'illegal_params'
    _explanation = 'Required payment parameters are either missing or have invalid values.'


class NotEnoughFundsError(YooMoneyError):
    match_error_code = 'not_enough_funds'
    _explanation = 'The payer’s account does not have sufficient funds to make the payment. Additional funds should be credited to the account, and a new payment will need to be processed.'


class PayeeNotFoundError(YooMoneyError):
    match_error_code = 'payee_not_found'
    _explanation = 'The transfer recipient was not found. The specified account does not exist, or a phone number or email address was specified that is not linked to a user account or payee.'


class PaymentRefusedError(YooMoneyError):
    match_error_code = 'payment_refused'
    _explanation = 'The merchant refused to accept the payment (for example, the user tried to purchase an item that is not in stock).'


class AuthorizationRejectError(YooMoneyError):
    match_error_code = 'authorization_reject'
    _explanation = """Authorization of the payment was refused. Possible reasons:
A transaction with the current parameters is forbidden for this user.
The user did not accept the User Agreement for the YooMoney service.
"""


class LimitExceededError(YooMoneyError):
    match_error_code = 'limit_exceeded'
    _explanation = """One of the operation limits was exceeded:
For the total amount of operations for the access token granted.
For the total amount of operations over a period of time for the access token granted.
YooMoney restrictions for various types of operations."""


class AccountBlockedError(YooMoneyError):
    match_error_code = 'account_blocked'
    _explanation = 'The user’s account has been blocked. In order to unblock the account, the user must be redirected to the address specified in the account_unblock_uri field.'


class AccountClosedError(YooMoneyError):
    match_error_code = 'account_closed'
    _explanation = 'User’s account closed.'


class ExtActionRequiredError(YooMoneyError):
    match_error_code = 'ext_action_required'
    _explanation = """This type of payment cannot be made at this time.
To be able to make these types of payments, the user must go to the page with the ext_action_uri address and follow the instructions on that page.
This may be any of the following actions:
    * Entering identification data.
    * Accepting the offer.
    * Performing other actions according to the instructions."""


class ContractNotFoundError(YooMoneyError):
    match_error_code = 'contract_not_found'
    _explanation = 'There is no existing unconfirmed payment with the specified request_id.'


class MoneySourceNotAvailableError(YooMoneyError):
    match_error_code = 'money_source_not_available'
    _explanation = 'The requested payment method (money_source) is not available for this payment.'


class TechnicalError(YooMoneyError):
    """Acting like a fallback error."""
