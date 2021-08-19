<h2 align="center">
<img src="https://github.com/GLEF1X/glQiwiApi/blob/master/docs/static/logo.png" width="200"></img>


[![PyPI version](https://img.shields.io/pypi/v/glQiwiApi.svg)](https://pypi.org/project/glQiwiApi/) [![Python](https://img.shields.io/badge/Python-3.7+-blue)](https://www.python.org/downloads/) [![Code Quality Score](https://www.code-inspector.com/project/20780/score/svg)](https://frontend.code-inspector.com/public/project/20780/glQiwiApi/dashboard) ![Code Grade](https://www.code-inspector.com/project/20780/status/svg) ![Downloads](https://img.shields.io/pypi/dm/glQiwiApi) ![docs](https://readthedocs.org/projects/pip/badge/?version=latest)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/GLEF1X/glQiwiApi.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/GLEF1X/glQiwiApi/context:python) [![CodeFactor](https://www.codefactor.io/repository/github/glef1x/glqiwiapi/badge)](https://www.codefactor.io/repository/github/glef1x/glqiwiapi)
![codecov](https://codecov.io/gh/GLEF1X/glQiwiApi/branch/dev-1.x/graph/badge.svg?token=OD538HKV15)
![CI](https://github.com/GLEF1X/glQiwiApi/actions/workflows/python-package.yml/badge.svg) ![mypy](https://img.shields.io/badge/%20type_checker-mypy-%231674b1?style=flat)

<img src="https://github.com/GLEF1X/glQiwiApi/blob/master/demo.gif"/>
</h2>

## 🌎Official api resources:

* 🎓 __Docs: [here](https://glqiwiapi.readthedocs.io/en/latest/)__
* 🖱️ __Developer
  contacts: [![Dev-Telegram](https://img.shields.io/badge/Telegram-blue.svg?style=flat-square&logo=telegram)](https://t.me/GLEF1X)__

### 📣Why glQiwiApi?

* :boom:__It's working faster than other async libraries for qiwi__
* :dizzy:__Frequent updates and edits__
* :innocent: __The library developer will always help you with any problems you
  might encounter__

### 💾Installation

```bash
pip install glQiwiApi
```

---

## 🐦Dependencies  

| Library | Description                                            |
|:-------:|:----------------------------------------------:        |
|aiohttp  | Asynchronous HTTP Client/Server for asyncio and Python.|
|aiofiles | saving receipts in pdf                                 |
|uvloop   | Optional(can boost API), but work only on Linux        |
|pydantic | Json data validator. Very fast instead of custom       |
|loguru   | library which aims to bring enjoyable logging in Python|

---

## 🧸Dive-in Examples

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    # If you want to use qiwi wrapper without async context just 
    # pass on "without_context=True"
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number',
        without_context=True
    )
    print((await wallet.get_balance()).amount)
    # OR(x3 performance boost with async context,
    # because it use only 1 aiohttp session to get response for all requests
    # in async with context manager)
    async with QiwiWrapper(api_access_token='your_token') as w:
        w.phone_number = '+number'
        print((await w.get_balance()).amount)


# Also you can use it like here
my_wallet = QiwiWrapper(
    api_access_token='your_token',
    phone_number='+phone_number'
)


async def laconic_variant():
    async with my_wallet as w:
        print(await w.get_balance())


asyncio.run(main())
```

---

## 🌀Checking transactions

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    async with QiwiWrapper(api_access_token='your_token') as w:
        w.phone_number = '+number'
        # This way we will check if the transaction was in the amount of 999 rubles with a comment
        # 'I like glQiwiApi!' and sender with phone number +7904832168
        is_paid = await w.check_transaction(
            amount=999,
            comment='I like glQiwiApi!',
            sender_number='+7904832168'
        )
        print(is_paid)


asyncio.run(main())
```

## 🌱Create & check p2p bills

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
  # You can pass on only p2p tokens, if you want to use only p2p api
  async with QiwiWrapper(
          secret_p2p="your_secret_p2p"
  ) as w:
    # This way you can create P2P bill using QIWI p2p API
    bill = await w.create_p2p_bill(
      amount=1,
      comment='my_comm'
    )
    # This way you can check status of transaction(exactly is transaction was paid)
    if (await w.check_p2p_bill_status(bill_id=bill.bill_id)) == 'PAID':
      print('You have successfully paid your invoice')
    else:
      print('Invoice was not paid')
    # Or, you can use method check on the instance of Bill 
    print(await bill.check())


asyncio.run(main())
```

#### That will create a form like that

![form](https://i.ibb.co/T0C5RYz/2021-03-21-14-58-33.png)

## ⛏Send to another wallet & get receipt

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
  async with QiwiWrapper(api_access_token="token") as w:
    w.phone_number = "+number"
    # It looks like a transfer to another qiwi wallet
    # in the example, the transfer will be to the number +7904832168 with the comment "for a chocolate bar" and the amount of 1 ruble
    trans_id = await w.to_wallet(
      to_number='+7904832168',
      comment='for a chocolate bar',
      amount=1
    )
    # In this example, we will save the receipt in the directory where you run the script as my_receipt.pdf
    await w.get_receipt(
      transaction_id=trans_id,
      transaction_type='OUT',
      file_path='my_receipt'
    )


asyncio.run(main())

```

## 🌟Webhooks & handlers

```python

from glQiwiApi import QiwiWrapper, types, BaseFilter
from glQiwiApi.utils import executor

wallet = QiwiWrapper(
  api_access_token='token from https://qiwi.com/api/',
  secret_p2p='secret token from https://qiwi.com/p2p-admin/'
)


class CustomFilter(BaseFilter):
  async def check(self, update: types.Transaction) -> bool:
    # some stuff
    return True


@wallet.transaction_handler(
  CustomFilter())  # start with 1.0.3b2 you can use class-based filters, but also combine it with lambda statements, if you want
async def get_transaction(event: types.WebHook):
  print(event)


@wallet.bill_handler()
async def fetch_bill(notification: types.Notification):
  print(notification)


executor.start_webhook(wallet, port=80)
```

## 🧑🏻🔬Polling updates

```python
from glQiwiApi import BaseFilter, QiwiWrapper, types
from glQiwiApi.utils import executor

# let's imagine that payload its a dictionary with your tokens =)
wallet = QiwiWrapper(**payload)


class MyFirstFilter(BaseFilter):
  async def check(self, update: types.Transaction) -> bool:
    return True


class MySecondFilter(BaseFilter):

  async def check(self, update: types.Transaction) -> bool:
    return False


@wallet.transaction_handler(MyFirstFilter(), lambda event: event is not None, ~MySecondFilter())
async def my_handler(event: types.Transaction):
  ...


executor.start_polling(wallet)
```

## 💳Send to card & predict commission

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    async with QiwiWrapper(api_access_token="token") as w:
        w.phone_number = "+number"
        # So you can send funds to cards of different banks, while receiving ID transactions
        trans_id = await w.to_card(
            trans_sum=1,
            to_card='4890494756089082'
        )
        print(trans_id)
        # This is how you can pre-calculate the transaction fee.
        calc_commission = await w.calc_commission(
            to_account='4890494756089082',
            pay_sum=1
        )
        print(calc_commission.qiwi_commission.amount)


asyncio.run(main())

```

## 🚀Query caching (beta)

```python
import asyncio

from glQiwiApi import QiwiWrapper

# Caching is disabled by default because
# this feature is still in beta testing and
# constant DEFAULT_CACHE_TIME = 0 to fix this and enable caching
# you need to pass cache_time to the constructor of the QiwiWrapper class
# or YooMoneyAPI
wallet = QiwiWrapper(
  # Qiwi token from https://qiwi.com/api
  api_access_token='token',
  # Your phone number startswith "+"
  phone_number='+phone_number',
  # Cache time in seconds
  cache_time=5
)


async def cache_test():
  async with wallet:
    # The result will be cached
    print(await wallet.transactions(rows=50))
    # The result will be taken from cache
    print(await wallet.transactions(rows=50))

    # The requests below will not be taken from the cache,
    # the reason for this is the difference in the request parameters
    # The result is also stored in the cache
    print(len(await wallet.transactions(rows=30)) == 30)  # True
    # However, a second request to the api will be executed, because
    # when trying to retrieve a result from the cache, the validator compares
    # request parameters, if they do not match, then
    # cache is ignored
    # Repeated request to api
    print(len(await wallet.transactions(rows=10)) == 10)  # True


asyncio.run(cache_test())


```

## ⚠️Handling exceptions

```python
import asyncio

from glQiwiApi import QiwiWrapper, APIError


async def main():
  async with QiwiWrapper(api_access_token='your_token') as w:
    w.phone_number = '+number'
    try:
      await w.to_card(to_card="some_card", trans_sum=2)
    except APIError as ex:
      # Its give u full traceback from api if response was bad
      print(ex.json())


asyncio.run(main())
```

---

## 🗺QIWI terminals

__glQiwiApi covers qiwi's MAPS api in QiwiMaps class__

---

# YooMoney API

## Important. How to get YooMoney access token

+ #### We register our application in YooMoney using the link: [click](https://yoomoney.ru/myservices/new)

![yoo_money_register_app](https://i.imgur.com/Mu6R8Po.png)

+ #### Here, we get the client_id after registration and then use YooMoneyAPI:

```python
import asyncio

from glQiwiApi import YooMoneyAPI


async def get_url_to_auth() -> None:
    # Get a link for authorization, follow it if we get invalid_request or some kind of error
    # means either the scope parameter is incorrectly passed, you need to reduce the list of rights or try to recreate the application
    print(await YooMoneyAPI.build_url_for_auth(
        # For payments, account verification and payment history, you need to specify scope = ["account-info", "operation-history", "operation-details", "payment-p2p"]
        scope=["account-info", "operation-history"],
        client_id='ID received when registering the application above',
        redirect_uri='the link specified during registration above in the Redirect URI field'
    ))


asyncio.run(get_url_to_auth())
```

+ #### Now you need to get the temporary code and get the token as fast as possible using the YooMoneyAPI class method:

![reg](https://i2.paste.pics/7660ed1444d1b3fc74b08128c74dbcd4.png?trs=9bfa3b1c0203c2ffe9982e7813a27700d047bfbc7ed23b79b99c1c4ffdd34995)

```python
import asyncio

from glQiwiApi import YooMoneyAPI


async def get_token() -> None:
    print(await YooMoneyAPI.get_access_token(
        code='the code obtained from the link, as in the screenshot above',
        client_id='Application ID received when registering the application above',
        redirect_uri='link provided during registration'
    ))


asyncio.run(get_token())
```

---

## Dive-in Examples

```python
import asyncio

from glQiwiApi import YooMoneyAPI

TOKEN = 'some_token'


async def main():
    wallet = YooMoneyAPI(
        api_access_token=TOKEN,
        without_context=True
    )
    transactions = await wallet.transactions()
    print(transactions)
    # OR(x3 performance boost)
    async with YooMoneyAPI(api_access_token=TOKEN) as w:
        print(await w.transactions(records=50))


asyncio.run(main())
```

## Send money to another wallet and checking this transaction

```python

import asyncio

from glQiwiApi import YooMoneyAPI

TOKEN = 'your_token'


async def main():
  w = YooMoneyAPI(TOKEN)
  async with w:
    # So you can send funds to another account, in the example this is a transfer to account 4100116602400968
    # worth 2 rubles with the comment "I LOVE glQiwiApi"
    payment = await w.send(
      to_account='4100116602400968',
      comment='I LOVE glQiwiApi',
      amount=2
    )
    # This way you can check the transaction, whether it was received by the person on the account
    print(await w.check_transaction(amount=2, comment='I LOVE glQiwiApi',
                                    operation_type='out'))


asyncio.run(main())

```

## Fetch account info

```python
import asyncio

from glQiwiApi import YooMoneyAPI

TOKEN = 'your_token'


async def main():
  w = YooMoneyAPI(TOKEN)
  async with w:
    # This gives you account information as AccountInfo object.
    get_account_info = await w.retrieve_account_info()
    print(get_account_info.account_status)
    print(get_account_info.balance)


asyncio.run(main())

```
