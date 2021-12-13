Welcome to the glQiwiApi documentation!
=============================================

..  image:: https://img.shields.io/pypi/v/glQiwiApi.svg?style=flat-square
    :target: https://pypi.python.org/pypi/glQiwiApi
    :alt: Latest version released on PyPi

..  image:: https://img.shields.io/badge/Python-3.7+-blue?style=flat-square
    :target: https://pypi.python.org/pypi/glQiwiApi
    :alt: python version

..  image:: https://pepy.tech/badge/glqiwiapi/month
    :target: https://pepy.tech/project/glqiwiapi
    :alt: downloads per month

..  image:: https://pepy.tech/badge/glqiwiapi
    :target: https://pepy.tech/project/glqiwiapi
    :alt:  number of downloads for all time

..  image:: https://www.code-inspector.com/project/20780/status/svg?style=flat-square
    :target: https://frontend.code-inspector.com/public/project/20780/glQiwiApi/dashboard
    :alt: code grade

..  image:: https://codecov.io/gh/GLEF1X/glQiwiApi/branch/dev-1.x/graph/badge.svg?token=OD538HKV15
    :alt: code coverage

..  image:: https://github.com/GLEF1X/glQiwiApi/actions/workflows/tests.yml/badge.svg
    :alt: CI

=========
Features:
=========

    * It's working faster than other async wrappers for qiwi and yoomoney |:boom:|
    * Obviously, it's asynchronous
    * Fully supports `qiwi <https://qiwi.com>`_ apis: `qiwi-maps <https://github.com/QIWI-API/qiwi-map>`_, `bills <https://developer.qiwi.com/en/bill-payments/>`_, `wallet <https://developer.qiwi.com/en/qiwi-wallet-personal/>`_ and also `yoomoney <https://yoomoney.ru/docs/wallet>`_
    * Provides support of polling and webhooks for QIWI as well as possible
    * Furnishes many utils and extensions such a `pydantic <https://pydantic-docs.helpmanual.io/>`_  support, code coverage not less than 80% and many other handy things
    * Full compatibility with `static type checking(mypy) <https://mypy.readthedocs.io/en/stable/>`_


=============
Quick example
=============

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiWrapper, APIError


    async def print_balance(qiwi_token: str, phone_number: str) -> None:
        """
        This function allows you to get balance of your wallet using glQiwiApi library
        """
        async with QiwiWrapper(api_access_token=qiwi_token, phone_number=phone_number) as w:
            try:
                balance = await w.get_balance()
            # handle exception if wrong credentials or really API return error
            except APIError as err:
                print(err.json())
                raise
        print(f"Your current balance is {balance.amount} {balance.currency.name}")


    asyncio.run(print_balance(qiwi_token="qiwi api token", phone_number="+phone_number"))






Contents
========
.. toctree::

   installation
   getting-started/index
   API/index
   polling
   advanced_features/index
   types/index


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
