import unittest

from glQiwiApi import YooMoneyAPI
from glQiwiApi.abstracts import AioTestCase
from glQiwiApi.data import Payment, AccountInfo, Operation

TOKEN = 'some_token'


class YooMoneyTest(AioTestCase):
    def setUp(self) -> None:
        self.w = YooMoneyAPI(TOKEN)

    async def test_build_url_to_get_token(self):
        url = await YooMoneyAPI.build_url_for_auth(
            scope=['account-info', "operation-history", 'operation-details'],
            client_id='some_client_id'
        )
        self.assertEqual(isinstance(url, str), True)

    async def test_get_access_token(self):
        token = await YooMoneyAPI.get_access_token(
            code='some_code',
            client_id='client_id'
        )
        self.assertEqual(isinstance(token, str), True)

    async def test_account_info(self) -> None:
        account_info = await self.w.account_info()
        self.assertEqual(isinstance(account_info, AccountInfo), True)

    async def test_transaction_history(self) -> None:
        transactions = await self.w.transactions()
        self.assertEqual(all(isinstance(transaction, Operation) for transaction in transactions), True)

    async def test_send(self):
        payment = await self.w.send(
            to_account='4100116633099701',
            protect=True,
            amount=2,
            comment_for_history='test_comment_for_history',
            comment='test_comment_for_receiver'
        )
        self.assertEqual(isinstance(payment, Payment), True)
        self.assertEqual(hasattr(payment, 'payment_id'), True)


if __name__ == '__main__':
    unittest.main()
