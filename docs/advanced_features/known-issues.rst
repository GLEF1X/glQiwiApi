=============
Known issues:
=============


```
aiohttp.client_exceptions.ClientConnectorError: Cannot connect to api.qiwi.com ssl:true...
```

This exception can be fixed this way:

.. code-block:: python

    import glQiwiApi
    from glQiwiApi import QiwiWallet
    from glQiwiApi.core import RequestService
    from glQiwiApi.core.session import AiohttpSessionHolder


    async def create_request_service(w: QiwiWallet):
        return RequestService(
            session_holder=AiohttpSessionHolder(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {w._api_access_token}",
                    "Host": "edge.qiwi.com",
                    "User-Agent": f"glQiwiApi/{glQiwiApi.__version__}",
                },
                trust_env=True
            )
        )


    wallet = QiwiWallet(request_service_factory=create_request_service)
