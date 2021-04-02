import asyncio

from glQiwiApi import QiwiWrapper


async def basic_usage():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+your_number',
        public_p2p='your_public_p2p_token',
        secret_p2p='your_secret_p2p_token'
    )
    # Отправка денег на другой кошелек
    transaction_id = await wallet.to_wallet(
        to_number='+number_получателя',
        comment='комментарий',
        trans_sum=1
    )
    print(transaction_id)
    # Получение баланса, функция возвращает словарь с номером валюты и самой суммой
    balance = await wallet.get_balance()
    print(balance)
    # Транзакции в виде списка объектов Transaction
    transactions = await wallet.transactions()
    print(transactions)
    # Отправка денег на карту с киви кошелька
    card_transaction_id = await wallet.to_card(
        trans_sum=1,
        to_card='номер карты без пробелов'
    )
    print(card_transaction_id)
    # Упрощенный метод для проверки транзакции, в функции уже реализована логика проверки
    answer = await wallet.check_transaction(
        comment='комментарий платежа, которого вы хотите проверить',
        transaction_type='IN',
        amount=1,
        sender_number='номер получателя или отправителя'
    )
    print(answer)
    # Получение чека или байты, которые можно сохранить в файл
    # В данном случае создаться файл examples/receipt.pdf
    await wallet.get_receipt(
        transaction_type='IN',
        transaction_id=transaction_id,
        file_path='receipt'
    )


asyncio.run(basic_usage())
