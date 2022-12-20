import logging

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.webhook import configure_app
from aiohttp import web

from glQiwiApi import QiwiWallet
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import HandlerContext, configure_app_for_qiwi_webhooks
from glQiwiApi.core.event_fetching.webhooks.config import (
    EncryptionConfig,
    HookRegistrationConfig,
    WebhookConfig,
)
from glQiwiApi.qiwi.clients.p2p.types import BillWebhook

qiwi_dp = QiwiDispatcher()

dp = Dispatcher(Bot('BOT TOKEN'))
wallet = QiwiWallet(api_access_token='wallet api token')


@qiwi_dp.bill_handler()
async def handle_webhook(webhook: BillWebhook, ctx: HandlerContext):
    # handle bill
    bill = webhook.bill


app = web.Application()
configure_app(
    dp,
    configure_app_for_qiwi_webhooks(
        wallet,
        qiwi_dp,
        app,
        WebhookConfig(
            encryption=EncryptionConfig(
                secret_p2p_key='secret p2p token, который был зарегистрирован с указанием айпи. '
                'Например http://айпи:8080/webhooks/qiwi/bills/'
            ),
            hook_registration=HookRegistrationConfig(host_or_ip_address='айпи:8080'),
        ),
    ),
    '/bot',
)

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    # Порт может быть любым
    web.run_app(app, port=8080)
