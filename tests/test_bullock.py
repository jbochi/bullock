import bullock
import redis
import time

TEST_DB = 14

class Bullock(bullock.Bullock):
    "A modified lock that uses a db different from default since we flush it before all tests"
    def __init__(self, key, *args, **kwargs):
        kwargs['db'] = TEST_DB
        super(Bullock, self).__init__(key, *args, **kwargs)


def setup_function(func):
    r = redis.StrictRedis(db=TEST_DB)
    r.flushdb()


def test_can_acquire_lock():
    b = Bullock("mylock")
    assert b.acquire()


def test_cannot_acquire_lock_if_other_is_locking():
    b1 = Bullock(key="mykey")
    assert b1.acquire()

    b2 = Bullock(key="mykey")
    assert not b2.acquire()


def test_can_acquire_lock_twice():
    b = Bullock("mylock")
    assert b.acquire()
    assert b.acquire()


def test_can_acquire_lock_with_same_value():
    b1 = Bullock("mylock", value="uniquevalue")
    b2 = Bullock("mylock", value="uniquevalue")
    assert b1.acquire()
    assert b2.acquire()


def test_can_acquire_lock_after_it_is_released():
    b = Bullock("mylock")
    assert b.acquire()
    assert b.release()
    assert b.acquire()


def test_another_instance_can_acquire_lock_after_it_is_released():
    b1 = Bullock(key="mykey")
    assert b1.acquire()
    b2 = Bullock(key="mykey")
    assert not b2.acquire()
    assert b1.release()
    assert b2.acquire()


def test_lock_cannot_be_released_if_not_locking():
    b = Bullock("mylock")
    assert not b.release()


def test_lock_cannot_be_released_if_locked_by_another_instance():
    b1 = Bullock(key="mykey")
    b1.acquire()
    b2 = Bullock(key="mykey")
    assert not b2.acquire()
    assert not b2.release()


def test_lock_expires():
    assert Bullock("mylock", ttl=0.1).acquire()
    time.sleep(0.05)
    assert not Bullock("mylock", ttl=0.1).acquire()
    time.sleep(0.2)
    assert Bullock("mylock", ttl=0.1).acquire()


def test_cannot_release_if_lock_has_expired():
    b = Bullock("mylock", ttl=0.1)
    assert b.acquire()
    time.sleep(0.2)
    assert not b.release()


def test_can_renew_lock_to_prevent_it_from_expiring():
    b = Bullock("mylock", ttl=0.1)
    assert b.acquire()
    for i in xrange(10):
        time.sleep(0.05)
        assert b.renew()
    assert b.release()


def test_can_acquire_locked_lock_if_blocking():
    b1 = Bullock("mykey", ttl=0.5)
    assert b1.acquire()
    b2 = Bullock("mykey")
    assert b2.acquire(blocking=True)


def test_with_statement():
    with Bullock("mykey") as l:
        assert l.locked
        b = Bullock("mykey")
        assert not b.acquire()
    assert b.acquire()
