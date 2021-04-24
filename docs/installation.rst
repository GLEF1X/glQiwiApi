.. highlight:: shell

============
Installation
============

Поддерживаемые версии Python: `3.7` и выше

Стабильный релиз
----------------

Для установки glQiwiApi, запустите эту команду в вашем терминале:

.. code-block:: console

    $ pip install glQiwiApi

Это предпочтительный метод установки, так как он всегда будет устанавливать самый последний стабильный релиз.
Если у вас нет установленного `pip`_, этот `Справочник по установке Python`_ может помочь в процессе.

.. _pip: https://pip.pypa.io
.. _Справочник по установке Python: http://docs.python-guide.org/en/latest/starting/installation/


Из исходных файлов
------------------

Вы можете либо клонировать публичный репозиторий:

.. code-block:: console

    $ git clone git://github.com/GLEF1X/glQiwiApi

Как только вы получите копию исходных файлов, вы можете установить их с помощью:

.. code-block:: console

    $ python setup.py install


Recommendations
---------------
You can speedup api by following next instructions:

- Use `uvloop <https://github.com/MagicStack/uvloop>`_ instead of default asyncio loop.

    *uvloop* is a fast, drop-in replacement of the built-in asyncio event loop. uvloop is implemented in Cython and uses libuv under the hood.

    **Installation:**

        .. code-block:: bash

            $ pip install uvloop

- Use `orjson <https://github.com/ijl/orjson>`_ instead of the default json module.

    orjson is a fast, correct JSON library for Python. It benchmarks as the fastest Python library for JSON and is more correct than the standard json library or other third-party libraries

    **Installation:**

        .. code-block:: bash

            $ pip install orjson

.. tip:: _GitHub репозитория: https://github.com/GLEF1X/glQiwiApi
