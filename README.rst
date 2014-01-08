=======
Bullock
=======

A distributed lock using Redis. Inspired by `Sherlock <https://github.com/RealGeeks/sherlock>`_.


Installation
------------

.. code:: bash

    $ pip install bullock


Usage
-----

.. code:: python

    from bullock import Bullock
    lock = Bullock(host="redis-hostname", key="my-first-lock", ttl=3600)
    lock.acquire(blocking=True)
    # do critical work here
    lock.release()

You can also use the with statement:

.. code:: python

    from bullock import Bullock
    with Bullock(host="redis-hostname", key="my-first-lock", ttl=3600):
        # do critical work here

For more examples, see tests.
