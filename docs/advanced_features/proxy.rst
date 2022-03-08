===========
Using proxy
===========


In the example below we'll use `aiohttp-socks` library to establish socks5 proxy:


.. code-block:: python

    import asyncio

    from aiohttp_socks import ProxyConnector

    from glQiwiApi import QiwiWallet
    from glQiwiApi.core import RequestService
    from glQiwiApi.core.session import AiohttpSessionHolder


    def create_request_service_with_proxy(w: QiwiWallet):
        return RequestService(
            session_holder=AiohttpSessionHolder(
                connector=ProxyConnector.from_url("socks5://34.134.60.185:443"),  # some proxy
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {w._api_access_token}",
                    "Host": "edge.qiwi.com",
                },
            )
        )


    wallet = QiwiWallet(
        api_access_token="your token",
        phone_number="+phone number",
        request_service_factory=create_request_service_with_proxy,
    )


    async def main():
        async with wallet:
            print(await wallet.get_balance())


    asyncio.run(main())
