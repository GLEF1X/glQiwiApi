API_DATA = {
    "api_access_token": "2ef55757d94f77534a49251ee41c8d59",
    "secret_p2p":
        "eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6ImJuMXZmNy0wMCIsInVzZXJfaWQiOiIzODA5NjgzMTc0NTkiLCJzZWNyZXQiOiI4ZjI4NGVjYWQ0ZTE0Y2MwYzA5ZTRlOWNiNTJjM2Q3MzU2NGVjMWQxZDYyNWIwZDZhMTQ3NjIyZDEyZTJmNWFlIn19",
    "phone_number": "+380968317459"
}

YOO_MONEY_DATA = {
    "api_access_token": "4100116602400968.3CA5CF3053F6D047025F1BB937471BADD188C967D14C23F97F282FDC7697B574891F979175E072A4ABFAA5C91AE917C73D6781F6F3762058B45FAB1126C2CC6AC15D9306C6C767A84D9CF49C88DC9F7C12179C74CA75EA57727BCCE7564988A84E7529A19614E704F681337D97BE4A45A4E62E52EDDFE3C3A458BA16F6B6004F"
}

WRONG_API_DATA = {
    "api_access_token": dict(),
    "secret_p2p": 5454,
    "phone_number": 1234
}

TO_WALLET_DATA = {
    "to_number": "+380985272064",
    "trans_sum": 1,
    "comment": "unit_test"
}

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

WEBHOOK_RAW_DATA = """{
    "hash": "50779a03d90c4fa60ac44dfd158dbceec0e9c57fa4cf4f5298450fdde1868945",
    "hookId": "f57f95e2-149f-4278-b2cb-4114bc319727",
    "messageId": "f9a197a8-26b6-4d42-aac4-d86b789c373c",
    "payment": {"account": "thedandod",
                 "comment": "",
                 "date": "2018-05-18T16:05:15+03:00",
                 "errorCode": "0",
                 "personId": 79254914194,
                 "provider": 25549,
                 "signFields": "sum.currency,sum.amount,type,account,txnId",
                 "status": "WAITING",
                 "sum": {"amount": 1.73, "currency": 643},
                 "total": {"amount": 1.73, "currency": 643},
                 "txnId": "13117338074",
                 "type": "OUT"},
    "test": false,
    "version": "1.0.0"
    }"""

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

TEMP_DIRECTORY_NAME: str = 'temp'

RECEIPT_FILE_NAME: str = 'receipt'
