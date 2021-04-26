import datetime
import unittest

from glQiwiApi import QiwiWrapper, types, sync, RequestError, \
    InvalidData, QiwiMaps
from glQiwiApi.core import AioTestCase

TOKEN = 'TOKEN'
WALLET = '+NUMBER'
QIWI_SECRET = 'P2P TOKEN'


class SyncQiwiTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.wallet = QiwiWrapper(TOKEN, WALLET, secret_p2p=QIWI_SECRET,
                                  without_context=True)

    def test_account_info(self):
        info = sync(self.wallet.account_info)
        self.assertTrue(isinstance(info, types.QiwiAccountInfo))

    def test_commission(self) -> None:
        commission = sync(self.wallet.commission, to_account='+74957556983',
                          pay_sum=1)
        self.assertTrue(isinstance(commission, types.Commission))
        with self.assertRaises(RequestError):
            sync(self.wallet.commission, to_account='+380985272064',
                 pay_sum=-1)

    def test_fail(self):
        with self.assertRaises(InvalidData):
            sync(
                self.wallet.fetch_statistics,
                start_date=datetime.datetime.now() - datetime.timedelta(
                    days=100),
                end_date=datetime.datetime.now()
            )
        with self.assertRaises(RequestError):
            sync(self.wallet.to_wallet, to_number='+38056546456454',
                 trans_sum=1)
        with self.assertRaises(RequestError):
            sync(self.wallet.to_wallet, to_number='+74957556983',
                 trans_sum=-1)

    def test_transactions_history(self):
        transactions = sync(self.wallet.transactions,
                            rows_num=10, operation='IN')
        self.assertEqual(len(transactions), 10)
        self.assertTrue(
            all(isinstance(txn, types.Transaction) for txn in transactions)
        )

    def test_list_of_balances(self):
        balances = sync(self.wallet.list_of_balances)
        self.assertTrue(
            all(isinstance(balance, types.Account) for balance in balances)
        )

    def test_transaction_info(self):
        info = sync(self.wallet.transactions)
        self.assertTrue(
            isinstance(
                sync(
                    self.wallet.transaction_info,
                    info[0].transaction_id,
                    info[0].type
                ) , types.Transaction)
        )

    def test_to_wallet(self):
        txn_id = sync(self.wallet.to_wallet, to_number='+74957556983',
                      trans_sum=1)
        self.assertTrue(isinstance(txn_id, str))

    def test_balance(self):
        balance = sync(self.wallet.get_balance)
        self.assertTrue(isinstance(balance, types.Sum))

    def test_p2p_creation(self):
        bill = sync(self.wallet.create_p2p_bill, amount=1,
                    comment='my_comment')
        self.assertTrue(isinstance(bill, types.Bill))
        self.assertTrue(
            bill.comment == 'my_comment' and bill.amount.value == 1)

    def test_p2p_status_check(self):
        bill = sync(self.wallet.create_p2p_bill, amount=1,
                    comment='my_comment')
        checked = sync(bill.check)
        self.assertTrue(isinstance(checked, bool))
        self.assertTrue(
            isinstance(
                sync(self.wallet.check_p2p_bill_status, bill_id=bill.bill_id),
                str
            )
        )
        self.wallet.available_balances()

    def test_available_balances(self):
        balances = sync(self.wallet.available_balances)
        self.assertTrue(
            all(isinstance(balance, types.Balance) for balance in balances)

        )

    def test_to_card(self):
        txn_id = sync(self.wallet.to_card, to_card='4890494688391549',
                      trans_sum=1)
        self.assertTrue(isinstance(txn_id, str))
        with self.assertRaises(RequestError):
            sync(self.wallet.to_card, to_card='+74957556983', trans_sum=1)

    def test_test_limits(self):
        limits = sync(self.wallet.get_limits)
        self.assertTrue(
            isinstance(limits, dict)
        )

    def test_webhook_registration_test(self):
        hook_url = 'https://example.com/'
        config, key = sync(self.wallet.bind_webhook, url=hook_url)
        self.assertTrue(
            isinstance(config, types.WebHookConfig) and isinstance(key, str)
        )
        self.assertTrue(
            isinstance(sync(self.wallet.delete_current_webhook), dict))

    def test_webhook_delete_fail(self):
        hook_url = 'https://example.com/'
        sync(self.wallet.bind_webhook, url=hook_url)
        sync(self.wallet.delete_current_webhook)
        with self.assertRaises(RequestError):
            sync(self.wallet.bind_webhook, url=hook_url,
                 delete_old=True)


class AsyncQiwiTestCase(AioTestCase):
    """
    Async qiwi unit test, which using async with context manager
    Can raise many exceptions, because there aren't native async unit tests
    in Python
    """

    def setUp(self) -> None:
        self.wallet = QiwiWrapper(TOKEN, WALLET, secret_p2p=QIWI_SECRET)
        self.maps = QiwiMaps()

    async def test_account_info(self):
        async with self.wallet as w:
            info = await w.account_info()
        self.assertTrue(isinstance(info, types.QiwiAccountInfo))

    async def test_commission(self) -> None:
        async with self.wallet as w:
            commission = await (w.commission(to_account='+74957556983',
                                             pay_sum=1))
        self.assertTrue(isinstance(commission, types.Commission))
        with self.assertRaises(RequestError):
            async with self.wallet as w:
                await w.commission(to_account='+74957556983',
                                   pay_sum=-1)

    async def test_fail(self):
        with self.assertRaises(InvalidData):
            async with self.wallet as w:
                start_date = datetime.datetime.now() - datetime.timedelta(days=100)
                with self.assertRaises(InvalidData):
                    await w.fetch_statistics(
                        start_date=start_date,
                        end_date=datetime.datetime.now()
                    )

        with self.assertRaises(RequestError):
            async with self.wallet as w:
                await w.to_wallet(to_number='+3805654645645',
                                  trans_sum=1)
        with self.assertRaises(RequestError):
            async with self.wallet as w:
                await w.to_wallet(to_number='+74957556983',
                                  trans_sum=-1)

    async def test_transactions_history(self):
        async with self.wallet as w:
            transactions = await w.transactions(
                rows_num=10, operation='IN')
        self.assertEqual(len(transactions), 10)
        self.assertTrue(
            all(isinstance(txn, types.Transaction) for txn in transactions)
        )

    async def test_list_of_balances(self):
        async with self.wallet as w:
            balances = await w.list_of_balances()
        self.assertTrue(
            all(isinstance(balance, types.Account) for balance in balances)
        )

    async def test_transaction_info(self):
        async with self.wallet as w:
            transactions = await w.transactions()
            txn_info = await w.transaction_info(
                transaction_id=transactions[0].transaction_id,
                transaction_type=transactions[0].type
            )
            self.assertTrue(
                isinstance(
                    txn_info, types.Transaction)
            )

    async def test_to_wallet(self):
        async with self.wallet as w:
            txn_id = await w.to_wallet(to_number='+74957556983',
                                       trans_sum=1)
        self.assertTrue(isinstance(txn_id, str))

    async def test_balance(self):
        async with self.wallet as w:
            balance = await w.get_balance()
        self.assertTrue(isinstance(balance, types.Sum))

    async def test_p2p_creation(self):
        async with self.wallet as w:
            bill = await w.create_p2p_bill(amount=1,
                                           comment='my_comment')
        self.assertTrue(isinstance(bill, types.Bill))
        self.assertTrue(
            bill.comment == 'my_comment' and bill.amount.value == 1
        )

    async def test_p2p_status_check(self):
        async with self.wallet as w:
            bill = await w.create_p2p_bill(amount=1,
                                           comment='my_comment')
            checked = await bill.check()
            status = await self.wallet.check_p2p_bill_status(
                bill_id=bill.bill_id
            )
        self.assertTrue(isinstance(checked, bool))
        self.assertTrue(
            isinstance(
                status,
                str
            )
        )

    async def test_available_balances(self):
        async with self.wallet as w:
            balances = await w.available_balances()
        self.assertTrue(
            all(isinstance(balance, types.Balance) for balance in balances)

        )

    async def test_to_card(self):
        async with self.wallet as w:
            txn_id = await w.to_card(to_card='4890494688391549',
                                     trans_sum=1)
            with self.assertRaises(RequestError):
                sync(w.to_card, to_card='+74957556983', trans_sum=1)
        self.assertTrue(isinstance(txn_id, str))

    async def test_test_limits(self):
        async with self.wallet as w:
            limits = await w.get_limits()
        self.assertTrue(
            isinstance(limits, dict)
        )

    async def test_webhook_registration_test(self):
        hook_url = 'https://example.com/'
        async with self.wallet as w:
            config, key = await w.bind_webhook(hook_url)
            answer = await w.delete_current_webhook()
        self.assertTrue(
            isinstance(config, types.WebHookConfig) and isinstance(key, str)
        )
        self.assertTrue(
            isinstance(answer, dict))

    async def test_webhook_delete_fail(self):
        hook_url = 'https://example.com/'
        async with self.wallet as w:
            await w.bind_webhook(hook_url)
            await w.delete_current_webhook()
            with self.assertRaises(RequestError):
                await self.wallet.bind_webhook(url=hook_url,
                                               delete_old=True)

    async def test_qiwi_maps(self):
        async with self.maps as map_manager:
            partners = await map_manager.partners()
        self.assertTrue(
            all(isinstance(partner, types.Partner) for partner in partners)
        )


if __name__ == '__main__':
    unittest.main()
