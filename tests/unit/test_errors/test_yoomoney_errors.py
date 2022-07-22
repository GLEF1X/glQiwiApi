from typing import Type

import pytest

from glQiwiApi.yoo_money.exceptions import (
    AccountBlockedError,
    AccountClosedError,
    AuthorizationRejectError,
    ContractNotFoundError,
    ExtActionRequiredError,
    IllegalParamError,
    InsufficientScopeError,
    InvalidGrantError,
    InvalidRequestError,
    LimitExceededError,
    MoneySourceNotAvailableError,
    NotEnoughFundsError,
    PayeeNotFoundError,
    PaymentRefusedError,
    TechnicalError,
    UnauthorizedClientError,
    YooMoneyError,
    YooMoneyErrorSchema,
)


@pytest.mark.parametrize(
    ['error_code', 'expected_exception_type'],
    [
        ['not_enough_funds', NotEnoughFundsError],
        ['illegal_param_date', IllegalParamError],
        ['invalid_request', InvalidRequestError],
        ['unauthorized_client', UnauthorizedClientError],
        ['invalid_grant', InvalidGrantError],
        ['illegal_param_type', IllegalParamError],
        ['some_err', TechnicalError],
        ['illegal_param_operation_id', IllegalParamError],
        ['not_enough_funds', NotEnoughFundsError],
        ['payment_refused', PaymentRefusedError],
        ['payee_not_found', PayeeNotFoundError],
        ['authorization_reject', AuthorizationRejectError],
        ['limit_exceeded', LimitExceededError],
        ['account_blocked', AccountBlockedError],
        ['account_closed', AccountClosedError],
        ['ext_action_required', ExtActionRequiredError],
        ['contract_not_found', ContractNotFoundError],
        ['money_source_not_available', MoneySourceNotAvailableError],
        ['insufficient_scope', InsufficientScopeError],
    ],
)
def test_if_error_class_equals_to_expected(
    error_code: str, expected_exception_type: Type[Exception]
):
    with pytest.raises(expected_exception_type) as exc_info:
        YooMoneyError.raise_most_appropriate_error(YooMoneyErrorSchema(error_code=error_code))

    assert exc_info.errisinstance(expected_exception_type)


@pytest.mark.parametrize(
    ['expected_param_name', 'error_code'],
    [
        ['operation_id', 'illegal_param_operation_id'],
        ['date', 'illegal_param_date'],
    ],
)
def test_if_illegal_param_error_contains_param_name(expected_param_name: str, error_code: str):
    with pytest.raises(IllegalParamError) as exc_info:
        YooMoneyError.raise_most_appropriate_error(YooMoneyErrorSchema(error_code=error_code))

    assert exc_info.value.param_name == expected_param_name
