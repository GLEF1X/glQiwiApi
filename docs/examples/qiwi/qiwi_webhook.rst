========
Webhooks
========


.. caution:: **To correctly run the webhook you need a VPS server or configure the local machine for response to requests of QIWI API.**

.. caution:: **Firstly, you need to register webhook to your server using glQiwiApi**


🐺So, to "bind" webhook and gracefully work with glQiwiApi webhook API, you need to follow this instructions:

1. **Step one(bind webhook).**

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiWrapper
    from glQiwiApi.ext.url_builder import WebhookURL

    wrapper = QiwiWrapper(
        api_access_token="",
        secret_p2p="",
        phone_number="+"
    )


    async def main():
        # some tips:
        # - webhook_path have to starts with "/"
        url = WebhookURL.create(host="https://github.com", webhook_path="/GLEF1X/glQiwiApi")  # equal to https://github.com/GLEF1X/glQiwiApi
        # Also, you can pass url as string, but it's highly recomended to use WebhookURL extension
        await wrapper.bind_webhook(url=url, delete_old=True)


    asyncio.run(main())

2. **Step two(use handlers and start webhook).**

Using glQiwiApi you can use two types of handlers ``transaction_handler`` and ``bill_handler`` respectively.
Also, you can pass lambda filters to miss unnecessary updates from webhook.

.. literalinclude:: ./../../../examples/qiwi/qiwi_webhook.py
    :caption: Usage of webhooks
    :language: python
    :linenos:




