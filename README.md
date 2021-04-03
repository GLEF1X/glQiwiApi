[![PyPI version](https://img.shields.io/pypi/v/glQiwiApi.svg)](https://pypi.org/project/glQiwiApi/) [![Python](https://img.shields.io/badge/Python-3.7+-green)](https://www.python.org/downloads/) [![Code Quality Score](https://www.code-inspector.com/project/20780/score/svg)](https://frontend.code-inspector.com/public/project/20780/glQiwiApi/dashboard) ![Code Grade](https://www.code-inspector.com/project/20780/status/svg) ![Downloads](https://img.shields.io/pypi/dm/glQiwiApi)

# glQiwiApi

## New feature. Add YooMoney support to library!:fireworks:

### Installation

```bash
pip install glQiwiApi
```

---

## Dependencies

| Library | Description                                    |
|:-------:|:----------------------------------------------:|
|aiohttp  | default http server                            |
|aiofiles | saving receipts in pdf                         |  
|aiosocks | to connect a SOCKS5 proxy                      |
|uvloop   | Optional(can boost API), but work only on Linux|

---

## Dive-in Examples

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number'
    )
    # Данным вызовом вы получите словарь с 2 ключами, текущим балансом и currency(код валюты)
    print(await wallet.get_balance())


asyncio.run(main())
```

---

## Checking transactions

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number'
    )
    # Таким образом мы проверим, была ли транзакция на сумму 999 рублей с комментарием
    # 'I like glQiwiApi!' и отправителем с номером +7904832168
    is_paid = await wallet.check_transaction(
        amount=999,
        comment='I like glQiwiApi!',
        sender_number='+7904832168'
    )
    print(is_paid)


asyncio.run(main())
```

## Create & check p2p bills

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number'
    )
    # Таким образом можно создать p2p счет
    # В примере указан счёт на 1 рубль с комментарием some_comment
    bill = await wallet.create_p2p_bill(
        amount=1,
        comment='my_comm'
    )
    # Проверка на статус "оплачено" созданного p2p счёта
    if (await wallet.check_p2p_bill_status(bill_id=bill.bill_id)) == 'PAID':
        print('Успешно оплачено')
    else:
        print('Транзакция не найдена')


asyncio.run(main())
```

#### That will create a form like that

![form](https://i.ibb.co/T0C5RYz/2021-03-21-14-58-33.png)

## Send to another wallet & get receipt(получение чека транзакции)

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number'
    )
    # Так выглядит перевод на другой киви кошелек
    # в примере перевод будет на номер +7904832168 с комментарием "На шоколадку" и суммой 1 рубль
    trans_id = await wallet.to_wallet(
        to_number='+7904832168',
        comment='На шоколадку',
        trans_sum=1
    )
    # В данном примере мы сохраним чек в директории, где вы запускаете скрипт как my_receipt.pdf
    await wallet.get_receipt(
        transaction_id=trans_id,
        transaction_type='OUT',
        file_path='my_receipt'
    )


asyncio.run(main())

```

## Send to card & check commission

```python
import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number'
    )
    # Так можно отправлять средства на карты разных банков, получая при этом айди транзакции
    trans_id = await wallet.to_card(
        trans_sum=1,
        to_card='4731219185432123'
    )
    print(trans_id)
    # Так можно предварительно расчитать комиссию за транзакцию
    commission = await wallet.commission(
        to_account='4731219185432123',
        pay_sum=1
    )
    print(commission.qw_commission)


asyncio.run(main())

```
# YooMoney API 
---

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
        api_access_token=TOKEN
    )
    transactions = await wallet.transactions()
    print(transactions)


asyncio.run(main())
```

## Send money to another wallet and checking this transaction

```python

import asyncio

from glQiwiApi import YooMoneyAPI

TOKEN = 'your_token'


async def main():
    w = YooMoneyAPI(TOKEN)
    # Так вы можете отослать средства на другой счет, в примере это перевод на аккаунт 4100116602400968
    # на сумму 2 рубля с комментарием "I LOVE glQiwiApi"
    payment = await w.send(
        to_account='4100116602400968',
        comment='I LOVE glQiwiApi',
        amount=2
    )
    # Опционально, так вы можете проверить транзакцию, поступила ли она человеку на счёт
    print(await w.check_transaction(amount=2, comment='I LOVE glQiwiApi', transaction_type='out'))


asyncio.run(main())

```

## Fetch account info

```python
import asyncio

from glQiwiApi import YooMoneyAPI

TOKEN = 'your_token'


async def main():
    w = YooMoneyAPI(TOKEN)
    # Так вы получаете информацию об аккаунте в виде объекта AccountInfo
    account_info = await w.account_info()
    print(account_info.account_status)
    print(account_info.balance)


asyncio.run(main()) 

```
