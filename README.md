# :rainbow: glQiwiApi

## :fireworks:New feature. Add YooMoney support to library!:fireworks:

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

## :unlock:Important. How to get YooMoney access token

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
    print(await YooMoneyAPI.build_url_for_auth(
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
