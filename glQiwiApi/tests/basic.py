import asyncio

from glQiwiApi import QiwiWrapper, YooMoneyAPI
from glQiwiApi.data import Payment


async def qiwi_basics_test():
    w = QiwiWrapper(
        api_access_token='35769645d9c57429df8a8fce435d08a0',
        phone_number='+380968317459',
    )
    b = await w.get_balance()
    print(b)


async def yoo_money_basic_test():
    TOKEN = '4100116602400968.67E45D8B0BEF430DBAEE8710C5A7D0F064402279B02D0FEF92E6B64831A274B7CCFF9351356271083D66C4B31B016AADEE43AB0726CB65956D60218ED792D50190B7F8B57E1B307A526346CE4AF4C6C76735A4F15F68FDAC77B3122EB184A1B799D4C83CE0A5772D3F56926EC7D718F38C6BDDA118ECCEB3AD5AB7EC53ED8CCA'
    wallet = YooMoneyAPI(
        api_access_token=TOKEN
    )
    # payment = await wallet.send(
    #     to_account='4100116633099701',
    #     amount=2,
    #     protect=True,
    #     comment_for_receiver='Возврат денег',
    #     comment_for_history="Обычный перевод"
    # )
    p = Payment(status='success', payment_id='670539518149104565', credit_amount=2.0, payer='4100116602400968', payee='4100116633099701', payee_uid=2298580599507153, invoice_id=None, balance=9.79, error=None, account_unblock_uri=None, acs_uri=None, acs_params=None, next_retry=None, digital_goods=None, protection_code='2811')
    print(await wallet.account_info())


asyncio.run(yoo_money_basic_test())
