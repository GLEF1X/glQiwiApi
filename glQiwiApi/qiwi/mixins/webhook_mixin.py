import asyncio
import copy
import logging
from typing import Optional, Any, Awaitable, Dict, Tuple, Callable, \
    MutableMapping

from aiohttp import web

from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.core.web_hooks import dispatcher, server
from glQiwiApi.core.web_hooks.config import Path
from glQiwiApi.types import WebHookConfig
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import RequestError


class QiwiWebHookMixin:
    """Mixin, which implements webhook logic"""

    def __init__(
            self,
            router: AbstractRouter,
            requests_manager: Any,
            secret_p2p: str
    ):
        self.dispatcher = dispatcher.Dispatcher(
            loop=asyncio.get_event_loop(),
            wallet=self
        )
        self._router = router
        self._requests = requests_manager
        self.secret_p2p = secret_p2p

    def _auth_token(
            self,
            headers: MutableMapping,
            p2p: bool = False
    ) -> MutableMapping:
        ...

    async def _register_webhook(
            self,
            web_url: Optional[str],
            txn_type: int = 2
    ) -> Optional[WebHookConfig]:
        """
        This method register a new webhook

        :param web_url: service url
        :param txn_type:  0 => incoming, 1 => outgoing, 2 => all
        :return: Active Hooks
        """
        url = self._router.build_url("REG_WEBHOOK")
        async for response in self._requests.fast().fetch(
                url=url,
                method='PUT',
                headers=self._auth_token(copy.deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                params={
                    'hookType': 1,
                    'param': web_url,
                    'txnType': txn_type
                }
        ):
            return WebHookConfig.parse_obj(response.response_data)

    async def get_current_webhook(self) -> Optional[WebHookConfig]:
        """
        Список действующих (активных) обработчиков уведомлений,
         связанных с вашим кошельком, можно получить данным запросом.
        Так как сейчас используется только один тип хука - webhook,
         то в ответе содержится только один объект данных

        """
        url = self._router.build_url("GET_CURRENT_WEBHOOK")
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(copy.deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                ))
        ):
            try:
                return WebHookConfig.parse_obj(response.response_data)
            except RequestError:
                return None

    async def _send_test_notification(self) -> Dict[str, str]:
        """
        Для проверки вашего обработчика webhooks используйте данный запрос.
        Тестовое уведомление отправляется на адрес, указанный при вызове
        register_webhook

        """
        url = self._router.build_url("SEND_TEST_NOTIFICATION")
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(copy.deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                ))
        ):
            return response.response_data

    async def get_webhook_secret_key(self, hook_id: str) -> str:
        """
        Каждое уведомление содержит цифровую подпись сообщения,
         зашифрованную ключом.
        Для получения ключа проверки подписи используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        url = self._router.build_url(
            "GET_WEBHOOK_SECRET",
            hook_id=hook_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(copy.deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                ))
        ):
            return response.response_data.get('key')

    async def delete_current_webhook(self) -> Optional[Dict[str, str]]:
        """
        Method to delete webhook

        :return: Описание результата операции
        """
        try:
            hook = await self.get_current_webhook()
        except RequestError as ex:
            raise RequestError(
                message=" You didn't register any webhook to delete ",
                status_code='422',
                json_info=ex.json()
            ) from None

        url = self._router.build_url(
            "DELETE_CURRENT_WEBHOOK",
            hook_id=hook.hook_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(copy.deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='DELETE'
        ):
            return response.response_data

    async def change_webhook_secret(self, hook_id: str) -> str:
        """
        Для смены ключа шифрования уведомлений используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        url = self._router.build_url(
            "CHANGE_WEBHOOK_SECRET",
            hook_id=hook_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(copy.deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='POST'
        ):
            return response.response_data.get('key')

    async def bind_webhook(
            self,
            url: Optional[str] = None,
            transactions_type: int = 2,
            *,
            send_test_notification: bool = False,
            delete_old: bool = False
    ) -> Tuple[Optional[WebHookConfig], str]:
        """
        [NON-API] EXCLUSIVE method to register new webhook or get old

        :param url: service url
        :param transactions_type: 0 => incoming, 1 => outgoing, 2 => all
        :param send_test_notification:  test_qiwi will send you test webhook update
        :param delete_old: boolean, if True - delete old webhook

        :return: Tuple of Hook and Base64-encoded key
        """
        key: Optional[str] = None

        if delete_old:
            await self.delete_current_webhook()

        try:
            # Try to register new webhook
            webhook = await self._register_webhook(
                web_url=url,
                txn_type=transactions_type
            )
        except (RequestError, TypeError):
            # Catching exception, if webhook already was registered
            try:
                webhook = await self.get_current_webhook()
            except RequestError as ex:
                raise RequestError(
                    message="You didn't pass on url to register new hook "
                            "and you didn't have registered webhooks",
                    status_code="422",
                    json_info=ex.json()
                )
            key = await self.get_webhook_secret_key(webhook.hook_id)
            return webhook, key

        if send_test_notification:
            await self._send_test_notification()

        if not isinstance(key, str):
            key = await self.get_webhook_secret_key(webhook.hook_id)

        return webhook, key

    def start_webhook(
            self,
            host: str = "localhost",
            port: int = 8080,
            path: Optional[Path] = None,
            app: Optional["web.Application"] = None,
            on_startup: Optional[
                Callable[
                    [web.Application], Awaitable[None]
                ]] = None,
            on_shutdown: Optional[
                Callable[
                    [web.Application], Awaitable[None]
                ]] = None,
            **logger_config: Any
    ):
        """
        Blocking function, which listening webhooks

        :param host: server host
        :param port: server port that open for tcp/ip trans.
        :param path: path for test_qiwi that will send requests
        :param app: pass web.Application
        :param on_startup: coroutine,which will be executed on startup
        :param on_shutdown: coroutine, which will be executed on shutdown
        """
        self._requests.without_context = True

        app = app if app is not None else web.Application()

        hook_config, key = api_helper.sync(self.bind_webhook)

        server.setup(
            dispatcher=self.dispatcher,
            app=app,
            path=Path() if not path else path,
            secret_key=self.secret_p2p,
            base64_key=key,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            instance=self
        )

        logging.basicConfig(**logger_config)

        web.run_app(app, host=host, port=port)

    @property
    def transaction_handler(self):
        """
        Handler manager for default test_qiwi transactions,
        you can pass on lambda filter, if you want,
        but it must to return a boolean

        """
        return self.dispatcher.transaction_handler_wrapper

    @property
    def bill_handler(self):
        """
        Handler manager for p2p bills,
        you can pass on lambda filter, if you want
        But it must to return a boolean

        """
        return self.dispatcher.bill_handler_wrapper
