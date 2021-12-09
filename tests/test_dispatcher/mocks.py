import dataclasses

TEST_BASE64_WEBHOOK_KEY = "JcyVhjHCvHQwufz+IHXolyqHgEc5MoayBfParl6Guoc="


@dataclasses.dataclass()
class WebhookTestData:
    bill_webhook_json: str
    base64_key_to_compare_hash: str
    transaction_webhook_json: str


MOCK_BILL_WEBHOOK_RAW_DATA = """{
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

MOCK_TRANSACTION_WEBHOOK_RAW_DATA = """{
   "messageId":"7814c49d-2d29-4b14-b2dc-36b377c76156",
   "hookId":"5e2027d1-f5f3-4ad1-b409-058b8b8a8c22",
   "payment":{
      "txnId":"13353941550",
      "date":"2018-06-27T13:39:00+03:00",
      "type":"IN",
      "status":"SUCCESS",
      "errorCode":"0",
      "personId":78000008000,
      "account":"+79165238345",
      "comment":"",
      "provider":7,
      "sum":{
         "amount":1,
         "currency":643
      },
      "commission":{
         "amount":0,
         "currency":643
      },
      "total":{
         "amount":1,
         "currency":643
      },
      "signFields":"sum.currency,sum.amount,type,account,txnId"
   },
   "hash":"76687ffe5c516c793faa46fafba0994e7ca7a6d735966e0e0c0b65eaa43bdca0",
   "version":"1.0.0",
   "test":false
}"""
