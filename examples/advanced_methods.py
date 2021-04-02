import asyncio

from glQiwiApi import QiwiWrapper
from glQiwiApi.data import Identification, Limit, Transaction


async def advanced_methods():
    wallet = QiwiWrapper(
        api_access_token='your_api_access_token',
        phone_number='+your_number',
        public_p2p='your_public_p2p_token',
        secret_p2p='your_secret_p2p_token'
    )
    # Получаем данные о индентификации вашего киви кошелька
    identification = await wallet.get_identification()
    assert isinstance(identification, Identification) is True
    # Создание p2p платежа
    bill = await wallet.create_p2p_bill(
        amount=999
    )
    # Отмена этого же платежа, перевод в статус REJECTED
    await wallet.reject_p2p_bill(
        bill_id=bill.bill_id
    )
    # Получение лимитов по вашему киви кошельку
    limits = await wallet.get_limits()
    assert all(isinstance(limit, Limit) for limit in limits) is True
    # Таким образом мы можем получить объект Transaction по его айди и типу
    trans = await wallet.transaction_info(
        transaction_id='some_trans_id',
        transaction_type='IN'
    )
    assert isinstance(trans, Transaction) is True
    # Таким образом возможно повысить статус до "Основной", получаем словарь {'success': True}, если успешно
    success = await wallet.authenticate(
        last_name='Пупкин',
        passport='43432423',
        birth_date='1998-02-11',
        first_name='Вася',
        patronymic='Васильевич'
    )
    assert success.get('success') is True
    # Получаем ограничения, которые есть на вашем кошельке, в ответе json формат
    restriction = await wallet.check_restriction()
    print(restriction)


asyncio.run(advanced_methods())
