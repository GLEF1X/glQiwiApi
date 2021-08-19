import os

API_DATA = {
    "api_access_token": os.getenv("API_ACCESS_TOKEN"),
    "secret_p2p": os.getenv("SECRET_P2P"),
    "phone_number": os.getenv("PHONE_NUMBER"),
}

YOO_MONEY_DATA = {"api_access_token": os.getenv("YOO_API_TOKEN")}

WRONG_API_DATA = {
    "api_access_token": dict(),
    "secret_p2p": "5454",
    "phone_number": "12121",
    "validate_params": True,
}

EMPTY_DATA: dict = {}

TO_WALLET_DATA = {"to_number": "+380985272064", "trans_sum": 1, "comment": "unit_test"}

NOTIFICATION_RAW_DATA = """{
"bill": {
    "siteId": "9hh4jb-00",
    "billId": "cc961e8d-d4d6-4f02-b737-2297e51fb48e",
    "amount": {
      "value": "1.00",
      "currency": "RUB"
    },
    "status": {
      "value": "PAID",
      "changedDateTime": "2021-01-18T15:25:18+03"
    },
    "customer": {
      "phone": "78710009999",
      "email": "test@tester.com",
      "account": "454678"
    },
    "customFields": {
      "paySourcesFilter": "qw",
      "themeCode": "Yvan-YKaSh",
      "yourParam1": "64728940",
      "yourParam2": "order 678"
    },
    "comment": "Text comment",
    "creationDateTime": "2021-01-18T15:24:53+03",
    "expirationDateTime": "2025-12-10T09:02:00+03"
  },
  "version": "1"
}"""

BASE64_WEBHOOK_KEY = "JcyVhjHCvHQwufz+IHXolyqHgEc5MoayBfParl6Guoc="

WEBHOOK_RAW_DATA = """{"messageId": "7814c49d-2d29-4b14-b2dc-36b377c76156",
                    "hookId": "5e2027d1-f5f3-4ad1-b409-058b8b8a8c22",
                    "payment": {"txnId": "13353941550", "date": "2018-06-27T13:39:00+03:00", "type": "IN",
                                "status": "SUCCESS",
                                "errorCode": "0", "personId": 78000008000, "account": "+79165238345", "comment": "",
                                "provider": 7,
                                "sum": {"amount": 1, "currency": 643}, "commission": {"amount": 0, "currency": 643},
                                "total": {"amount": 1, "currency": 643},
                                "signFields": "sum.currency,sum.amount,type,account,txnId"},
                    "hash": "76687ffe5c516c793faa46fafba0994e7ca7a6d735966e0e0c0b65eaa43bdca0",
                    "version": "1.0.0",
                    "test": false}"""

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
