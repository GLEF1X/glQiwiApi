========
Webhooks
========


.. caution:: **To correctly run the webhook you need a VPS server or configure the local machine for response to requests of QIWI API.**


Using glQiwiApi you can use two types of handlers ``transaction_handler`` and ``bill_handler`` respectively
Also, you can pass lambda filters to miss unnecessary updates from webhook.

.. literalinclude:: ./../../../examples/qiwi/qiwi_webhook.py
    :caption: Usage of webhooks
    :language: python
    :linenos:

