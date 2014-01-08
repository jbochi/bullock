import redis
import bullock

TEST_DB = 14

class Bullock(bullock.Bullock):
    "A modified lock that uses a db different from default since we flush it before all tests"
    def __init__(self, *args, **kwargs):
        kwargs['db'] = TEST_DB
        super(Bullock, self).__init__(*args, **kwargs)


def setup_function(func):
    r = redis.StrictRedis(db=TEST_DB)
    r.flushdb()


def test_can_acquire_lock():
    b = Bullock()
    assert b.lock()


def test_cannot_acquire_lock_if_other_is_locking():
    b1 = Bullock(key="mykey")
    assert b1.lock()

    b2 = Bullock(key="mykey")
    assert not b2.lock()


def test_cannot_lock_twice():
    b = Bullock()
    assert b.lock()
    assert not b.lock()


def test_can_acquire_lock_after_it_is_released():
    b = Bullock()
    assert b.lock()
    assert b.release()
    assert b.lock()


def test_another_instance_can_acquire_lock_after_it_is_released():
    b1 = Bullock(key="mykey")
    assert b1.lock()
    b2 = Bullock(key="mykey")
    assert not b2.lock()
    assert b1.release()
    assert b2.lock()


def test_lock_cannot_be_released_if_not_locking():
    b = Bullock()
    assert not b.release()


def test_lock_cannot_be_released_if_locked_by_another_instance():
    b1 = Bullock(key="mykey")
    b1.lock()
    b2 = Bullock(key="mykey")
    assert not b2.lock()
    assert not b2.release()
