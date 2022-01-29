from __future__ import annotations

__all__ = ("YooMoneyMethods")


class YooMoneyMethods:
    # Operations with token
    BUILD_URL_FOR_AUTH: str = "/oauth/authorize"
    GET_ACCESS_TOKEN: str = "/oauth/token"
    REVOKE_API_TOKEN: str = "/api/revoke"

    ACCOUNT_INFO: str = "/api/account-info"
    # Transactions
    OPERATION_HISTORY: str = "/api/operation-history"
    OPERATION_DETAILS: str = "/api/operation-details"
    # Payments
    PRE_PROCESS_PAYMENT: str = "/api/request-payment"
    PROCESS_PAYMENT: str = "/api/process-payment"
    ACCEPT_INCOMING_TRANSFER: str = "/api/incoming-transfer-accept"
    INCOMING_TRANSFER_REJECT: str = "/api/incoming-transfer-reject"

    # Forms
    QUICK_PAY_FORM: str = "/quickpay/confirm.xml?"

    MAKE_REQUEST_PAYMENT = "/api/request-payment"
