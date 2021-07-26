.. highlight:: shell

============
Installation
============

Supported Python versions: `3.7` and higher

Stable release
----------------

To install glQiwiApi, run this command in your terminal:

.. code-block:: console

    $ pip install glQiwiApi

This is the preferred installation method as it will always install the most recent stable release.
If you do not have installed `pip`_, this `Python Installation Reference`_ can help you in the process.

.. _pip: https://pip.pypa.io
.. _Python Installation Reference: http://docs.python-guide.org/en/latest/starting/installation/


From source files
------------------

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/GLEF1X/glQiwiApi

Once you get a copy of the source files, you can install them with:

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
