import os

QIWI_WALLET_CREDENTIALS = {
    "phone_number": os.getenv("PHONE_NUMBER"),
    "api_access_token": os.getenv("API_ACCESS_TOKEN"),
}

SECRET_P2P_CREDENTIALS = {"secret_p2p": os.getenv("SECRET_P2P")}

YOO_MONEY_DATA = {"api_access_token": os.getenv("YOO_API_TOKEN")}

YOO_MONEY_TEST_CLIENT_ID = os.getenv("YOO_TEST_CLIENT_ID")

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
