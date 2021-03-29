# :rainbow: glQiwiApi

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

#### If you don't find the examples you want [click](https://github.com/GLEF1X/glQiwiApi/tree/master/examples)