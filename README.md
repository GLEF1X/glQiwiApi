<h2 align="center">
<img src="https://github.com/GLEF1X/glQiwiApi/blob/master/docs/static/logo.png" width="200"></img>


[![PyPI version](https://img.shields.io/pypi/v/glQiwiApi.svg)](https://pypi.org/project/glQiwiApi/) [![Python](https://img.shields.io/badge/Python-3.7+-blue)](https://www.python.org/downloads/) [![Code Quality Score](https://www.code-inspector.com/project/20780/score/svg)](https://frontend.code-inspector.com/public/project/20780/glQiwiApi/dashboard) ![Code Grade](https://www.code-inspector.com/project/20780/status/svg) ![Downloads](https://img.shields.io/pypi/dm/glQiwiApi) ![docs](https://readthedocs.org/projects/pip/badge/?version=latest)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/GLEF1X/glQiwiApi.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/GLEF1X/glQiwiApi/context:python) [![CodeFactor](https://www.codefactor.io/repository/github/glef1x/glqiwiapi/badge)](https://www.codefactor.io/repository/github/glef1x/glqiwiapi)

<img src="https://github.com/GLEF1X/glQiwiApi/blob/master/demo.gif"/>
</h2>

## 🌎Official api resources:

* 🎓 __Docs: [here](https://glqiwiapi.readthedocs.io/en/master/index.html)__
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

| Library | Description                                    |
|:-------:|:----------------------------------------------:|
|aiohttp  | default http server                            |
|aiofiles | saving receipts in pdf                         |
|uvloop   | Optional(can boost API), but work only on Linux|
|pydantic | Json data validator. Very fast instead of custom|
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
        # Данным вызовом вы получите текущий баланс кошелька. 
        print((await w.get_balance()).amount)


# Also you can use it like here
my_wallet = QiwiWrapper(
    api_access_token='your_token',
    phone_number='+phone_number'
)


async def main_2():
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
        # Таким образом мы проверим, была ли транзакция на сумму 999 рублей с комментарием
        # 'I like glQiwiApi!' и отправителем с номером +7904832168
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
    # Таким образом можно создать p2p счет
    # В примере указан счёт на 1 рубль с комментарием some_comment
    bill = await w.create_p2p_bill(
      amount=1,
      comment='my_comm'
    )
    # Проверка на статус "оплачено" созданного p2p счёта
    if (await w.check_p2p_bill_status(bill_id=bill.bill_id)) == 'PAID':
      print('Успешно оплачено')
    else:
      print('Транзакция не найдена')
    # Или, начиная с версии апи 0.2.0
    print(await bill.paid)  # This will print you bool answer


asyncio.run(main())
```

#### That will create a form like that

![form](https://i.ibb.co/T0C5RYz/2021-03-21-14-58-33.png)

## ⛏Send to another wallet & get receipt(получение чека транзакции)

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    async with QiwiWrapper(api_access_token="token") as w:
        w.phone_number = "+number"
        # Так выглядит перевод на другой киви кошелек
        # в примере перевод будет на номер +7904832168 с комментарием "На шоколадку" и суммой 1 рубль
        trans_id = await w.to_wallet(
            to_number='+7904832168',
            comment='На шоколадку',
            trans_sum=1
        )
        # В данном примере мы сохраним чек в директории, где вы запускаете скрипт как my_receipt.pdf
        await w.get_receipt(
            transaction_id=trans_id,
            transaction_type='OUT',
            file_path='my_receipt'
        )


asyncio.run(main())

```

## 🌟Webhooks & handlers

```python

from glQiwiApi import QiwiWrapper, types
from glQiwiApi.utils import executor

wallet = QiwiWrapper(
    api_access_token='token from https://qiwi.com/api/',
    secret_p2p='secret token from https://qiwi.com/p2p-admin/'
)


@wallet.transaction_handler(lambda event: ...)
async def get_transaction(event: types.WebHook):
    print(event)


@wallet.bill_handler()
async def fetch_bill(notification: types.Notification):
    print(notification)

    
executor.start_webhook(wallet, port=80)
```

## 🧑🏻🔬Polling updates
```python
import datetime

from glQiwiApi import QiwiWrapper, types
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

wallet = QiwiWrapper(
    api_access_token=api_access_token,
    phone_number=phone_number
)


@wallet.transaction_handler()
async def my_first_handler(update: types.Transaction):
    assert isinstance(update, types.Transaction)


def on_startup(wrapper: QiwiWrapper):
    wrapper.dispatcher.logger.info("This message logged on startup")


executor.start_polling(
    wallet,
    on_startup=on_startup
)
```

## 💳Send to card & check commission

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    async with QiwiWrapper(api_access_token="token") as w:
        w.phone_number = "+number"
        # Так можно отправлять средства на карты разных банков, получая при этом айди транзакции
        trans_id = await w.to_card(
            trans_sum=1,
            to_card='4731219185432123'
        )
        print(trans_id)
        # Так можно предварительно расчитать комиссию за транзакцию
        commission = await w.commission(
            to_account='4731219185432123',
            pay_sum=1
        )
        print(commission.qiwi_commission.amount)


asyncio.run(main())

```

## 🚀Query caching (beta)

```python
import asyncio

from glQiwiApi import QiwiWrapper

# Кэширование по умолчанию отключено, так как
# эта функция все ещё находиться в бета тестировании и
# константа DEFAULT_CACHE_TIME = 0, чтобы это исправить и включить кэширование
# нужно передать cache_time в конструктор класса QiwiWrapper
# или YooMoneyAPI
wallet = QiwiWrapper(
    # Токен, полученный с https://qiwi.com/api
    api_access_token='token',
    # Номер вашего мобильного номера с "+"
    phone_number='+phone_number',
    # Время кэширование запроса в секундах(пока ещё в бета тестировании)
    cache_time=5
)


async def cache_test():
    async with wallet:
        # Результат заноситься в кэш
        print(await wallet.transactions(rows_num=50))
        # Этот запрос возьмется из кэша
        print(await wallet.transactions(rows_num=50))

        # Запросы ниже не будут браться из кэша,
        # причиной тому есть разница в параметрах запроса
        # Результат все также заноситься в кэш
        print(len(await wallet.transactions(rows_num=30)) == 30)  # True
        # Однако, повторный запрос к апи будет выполнен, поскольку
        # при попытке взятие результата из кэша валидатор сравнивает
        # параметры запроса, если они не совпадают, то
        # кэш игнорируется
        # Повторный запрос к апи
        print(len(await wallet.transactions(rows_num=10)) == 10)  # True


asyncio.run(cache_test())


```

## ⚠️Handling exceptions

```python
import asyncio

from glQiwiApi import QiwiWrapper, RequestError


async def main():
    async with QiwiWrapper(api_access_token='your_token') as w:
        w.phone_number = '+number'
        try:
            await w.to_card(to_card="some_card", trans_sum=2)
        except RequestError as ex:
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

+ #### Регистрируем своё приложение в YooMoney по ссылке: [click](https://yoomoney.ru/myservices/new)

![yoo_money_register_app](https://i.imgur.com/Mu6R8Po.png)

+ #### Получаем client_id после регистрации и далее используем уже YooMoneyAPI:

```python
import asyncio

from glQiwiApi import YooMoneyAPI


async def get_url_to_auth() -> None:
    # Получаем ссылку для авторизации, переходим по ней, если получаем invalid_request или какую-то ошибку
    # значит либо неправильно передан scope параметр, нужно уменьшить список прав или попробовать пересоздать приложение
    print(await YooMoneyAPI.build_url_for_auth(
        # Для платежей, проверки аккаунта и истории платежей, нужно указать scope=["account-info", "operation-history", "operation-details", "payment-p2p"]
        scope=["account-info", "operation-history"],
        client_id='айди, полученный при регистрации приложения выше',
        redirect_uri='ссылка, указаная при регистрации выше в поле Redirect URI'
    ))


asyncio.run(get_url_to_auth())
```

+ #### Теперь нужно получить временный код и МАКСИМАЛЬНО БЫСТРО получить токен, используя class method YooMoneyAPI:

![reg](https://i2.paste.pics/7660ed1444d1b3fc74b08128c74dbcd4.png?trs=9bfa3b1c0203c2ffe9982e7813a27700d047bfbc7ed23b79b99c1c4ffdd34995)

```python
import asyncio

from glQiwiApi import YooMoneyAPI


async def get_token() -> None:
    print(await YooMoneyAPI.get_access_token(
        code='код полученный из ссылки, как на скрине выше',
        client_id='айди приложения, полученое при регистрации',
        redirect_uri='ссылка, указанная при регистрации'
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
        # Так вы можете отослать средства на другой счет, в примере это перевод на аккаунт 4100116602400968
        # на сумму 2 рубля с комментарием "I LOVE glQiwiApi"
        payment = await w.send(
            to_account='4100116602400968',
            comment='I LOVE glQiwiApi',
            amount=2
        )
        # Опционально, так вы можете проверить транзакцию, поступила ли она человеку на счёт
        print(await w.check_transaction(amount=2, comment='I LOVE glQiwiApi',
                                        transaction_type='out'))


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
        # Так вы получаете информацию об аккаунте в виде объекта AccountInfo
        account_info = await w.account_info
        print(account_info.account_status)
        print(account_info.balance)


asyncio.run(main())

```
