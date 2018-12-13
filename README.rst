=======
Bullock
=======

A distributed lock using Redis. Inspired by `Sherlock <https://github.com/RealGeeks/sherlock>`_.

.. image:: https://travis-ci.org/jbochi/bullock.svg?branch=master
    :target: https://travis-ci.org/jbochi/bullock


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

Also supports using redis cluster:

.. code:: python

    from bullock import Bullock
    lock = Bullock(host="redis-hostname", key="my-first-lock", ttl=3600, redis_cluster=True)
    lock.acquire(blocking=True)
    # do critical work here
    lock.release()

For more examples, see tests_.

.. _tests: https://github.com/jbochi/bullock/blob/master/tests/test_bullock.py
