import time

from glQiwiApi.data import WrapperData

DEFAULT_QIWI_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer {token}',
    'Host': 'edge.qiwi.com',
}

P2P_QIWI_HEADERS = {
    'Authorization': 'Bearer {token}',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

QIWI_TO_CARD = WrapperData(
    json=
    {
        "id": str(int(time.time() * 1000)),
        "sum":
            {
                "amount": "", "currency": "643"
            },

        "paymentMethod":
            {
                "type": "Account", "accountId": "643"
            },
        "fields": {
            "account": ""
        }
    },
    headers=DEFAULT_QIWI_HEADERS
)

P2P_DATA = WrapperData(
    json={
        "amount": {
            "currency": "RUB",
            "value": "{amount}"
        },
        "expirationDateTime": "",
        "comment": "{comment}",
        "customFields": {
            "paySourcesFilter": "qw",
            "themeCode": "Yvan-YKaSh",
        }
    },

    headers=P2P_QIWI_HEADERS
)

QIWI_TO_WALLET = WrapperData(
    json={
        "id": str(int(time.time() * 1000)),
        "sum": {
            "amount": "",
            "currency": ""
        },
        "paymentMethod": {
            "type": "Account",
            "accountId": "643"
        },
        "comment": "",
        "fields": {
            "account": ""
        }
    },
    headers=DEFAULT_QIWI_HEADERS
)

TRANSACTION_TRANSFER = {
    'txnId': 'transaction_id',
    'personId': 'person_id',
    'account': 'to_account'
}

IDENTIFICATION_TRANSFER = {
    'id': 'identification_id',
    'firstName': 'first_name',
    'middleName': 'middle_name',
    'lastName': 'last_name',
    'birthDate': 'birth_date'
}

P2P_BILL_TRANSFER = {
    'siteId': 'site_id',
    'billId': 'bill_id',
    'creationDateTime': 'creation_date_time',
    'expirationDateTime': 'expiration_date_time',
    'payUrl': 'pay_url',
    'customFields': 'custom_fields',
    'value': 'amount'
}

LIMIT_TYPES = ['TURNOVER', 'REFILL', 'PAYMENTS_P2P', 'PAYMENTS_PROVIDER_INTERNATIONALS', 'PAYMENTS_PROVIDER_PAYOUT',
               'WITHDRAW_CASH']

LIMIT_TYPES_TRANSFER = {
    'max': 'max_limit',
    'type': 'limit_type'
}

ONLINE_COMMISSION_DATA = {
    "account": "",
    "paymentMethod": {
        "type": "Account",
        "accountId": "643"
    },
    "purchaseTotals":
        {
            "total":
                {"amount": "",
                 "currency": "643"
                 }
        }
}

COMMISSION_TRANSFER = {
    'providerId': 'provider_id',
    'withdrawSum': 'withdraw_sum',
    'qwCommission': 'qw_commission',
    'withdrawToEnrollmentRate': 'withdraw_to_enrollment_rate'
}
__all__ = (
    'LIMIT_TYPES', 'TRANSACTION_TRANSFER', 'IDENTIFICATION_TRANSFER', 'QIWI_TO_WALLET', 'QIWI_TO_CARD',
    'DEFAULT_QIWI_HEADERS', 'LIMIT_TYPES_TRANSFER', 'P2P_QIWI_HEADERS', 'P2P_DATA', 'P2P_BILL_TRANSFER',
    'ONLINE_COMMISSION_DATA', 'COMMISSION_TRANSFER'
)
