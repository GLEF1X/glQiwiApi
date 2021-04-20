===========
Quick start
===========

Simple template
---------------

Firstly, you need to import package

.. literalinclude:: ./../examples/quick_start.py
    :language: python
    :lines: 1-3

Create a new async function with instance of QiwiWrapper.

.. caution:: Context Manager in glQiwiApi. **If you will not be using a library with a context manager or if you are using a sync adapter you must pass without_context = True**

.. literalinclude:: ./../examples/quick_start.py
    :language: python
    :lines: 6-13

Get your balance, using get_balance() method

.. literalinclude:: ./../examples/quick_start.py
    :language: python
    :lines: 14

.. note:: Change from 0.2.0+ version. **You can use the async context manager from the 0.2.0 version of the API. This improves performance if many functions are called in 1 block of the context call.**


.. literalinclude:: ./../examples/quick_start.py
    :language: python
    :lines: 17-24




