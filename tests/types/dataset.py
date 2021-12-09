import os
from typing import Any, Dict

API_DATA = {
    "api_access_token": os.getenv("API_ACCESS_TOKEN"),
    "secret_p2p": os.getenv("SECRET_P2P"),
    "phone_number": os.getenv("PHONE_NUMBER"),
}

YOO_MONEY_DATA = {"api_access_token": os.getenv("YOO_API_TOKEN")}

WRONG_API_DATA = {
    "api_access_token": "sdfsdfs",
    "secret_p2p": "5454",
}

EMPTY_DATA: Dict[Any, Any] = {}

TO_WALLET_DATA = {"to_number": "+380985272064", "trans_sum": 1, "comment": "unit_test"}


TXN_RAW_DATA = """{
    "txnId":9309,
    "personId":79112223344,
    "date":"2017-01-21T11:41:07+03:00",
    "errorCode":0,
    "error":null,
    "status":"SUCCESS",
    "type":"OUT",
    "statusText":"Успешно",
    "trmTxnId":"1489826461807",
    "account":"0003***",
    "sum":{
        "amount":70,
        "currency":"RUB"
        },
    "commission":{
        "amount":0,
        "currency":"RUB"
        },
    "total":{
        "amount":70,
        "currency":"RUB"
        },
    "provider":{
      "id":5,
      "shortName":"test_provider"
    },
    "source": {},
    "comment":null,
    "currencyRate":1,
    "extras":null,
    "chequeReady":true,
    "bankDocumentAvailable":false,
    "bankDocumentReady":false,
    "repeatPaymentEnabled":false,
    "favoritePaymentEnabled": true,
    "regularPaymentEnabled": true
   }
"""

TEMP_DIRECTORY_NAME: str = "temp"
