import bullock
import redis
import rediscluster
import time
import os
import pytest

TEST_DB = 14
REDIS_CLUSTER = 'redis_cluster'
REDIS_REGULAR = 'redis'


class Bullock(bullock.Bullock):
    "A modified lock that uses a db different from default since we flush it before all tests"
    def __init__(self, key, *args, **kwargs):
        kwargs['db'] = TEST_DB
        kwargs['host'] = os.getenv('REDIS_HOST', 'localhost')
        kwargs['port'] = os.getenv('REDIS_PORT', '6379')
        super(Bullock, self).__init__(key, *args, **kwargs)

@pytest.fixture(params=[REDIS_REGULAR, REDIS_CLUSTER])
def redis_type(request):
    if request.param == REDIS_REGULAR:
        os.environ["REDIS_HOST"] = 'redis'
        os.environ["REDIS_PORT"] = '6379'
        r = redis.StrictRedis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=TEST_DB)
    else:
        os.environ["REDIS_HOST"] = 'redis-cluster'
        os.environ["REDIS_PORT"] = '7000'
        r = rediscluster.StrictRedisCluster(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'))
    r.flushdb()
    return request.param


def test_can_acquire_lock(redis_type):
    b = Bullock("mylock", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b.acquire(), "failed to acquire for %s" % redis_type

def test_cannot_acquire_lock_if_other_is_locking(redis_type):
    b1 = Bullock(key="mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b1.acquire(), "failed to acquire for %s" % redis_type

    b2 = Bullock(key="mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert not b2.acquire(), "failed to acquire for %s" % redis_type


def test_can_acquire_lock_twice(redis_type):
    b = Bullock("mylock", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b.acquire(), "failed to acquire for %s" % redis_type
    assert b.acquire(), "failed to acquire for %s" % redis_type


def test_can_acquire_lock_with_same_value(redis_type):
    b1 = Bullock("mylock", value="uniquevalue", redis_cluster=(redis_type==REDIS_CLUSTER))
    b2 = Bullock("mylock", value="uniquevalue", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b1.acquire(), "failed to acquire for %s" % redis_type
    assert b2.acquire(), "failed to acquire for %s" % redis_type

def test_can_acquire_lock_with_same_numeric_value(redis_type):
    b1 = Bullock("mylock", value=0, redis_cluster=(redis_type==REDIS_CLUSTER))
    b2 = Bullock("mylock", value=0, redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b1.acquire(), "failed to acquire for %s" % redis_type
    assert b2.acquire(), "failed to acquire for %s" % redis_type

def test_can_acquire_lock_after_it_is_released(redis_type):
    b = Bullock("mylock", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b.acquire(), "failed to acquire for %s" % redis_type
    assert b.release(), "failed to release for %s" % redis_type
    assert b.acquire(), "failed to acquire for %s" % redis_type


def test_another_instance_can_acquire_lock_after_it_is_released(redis_type):
    b1 = Bullock(key="mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b1.acquire(), "failed to acquire for %s" % redis_type
    b2 = Bullock(key="mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert not b2.acquire(), "failed to acquire for %s" % redis_type
    assert b1.release(), "failed to release for %s" % redis_type
    assert b2.acquire(), "failed to acquire for %s" % redis_type


def test_lock_cannot_be_released_if_not_locking(redis_type):
    b = Bullock("mylock", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert not b.release(), "failed to release for %s" % redis_type


def test_lock_cannot_be_released_if_locked_by_another_instance(redis_type):
    b1 = Bullock(key="mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    b1.acquire(), "failed to acquire for %s" % redis_type
    b2 = Bullock(key="mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert not b2.acquire(), "failed to acquire for %s" % redis_type
    assert not b2.release(), "failed to release for %s" % redis_type


def test_lock_expires(redis_type):
    assert Bullock("mylock", ttl=0.4, redis_cluster=(redis_type==REDIS_CLUSTER)).acquire(), "failed to acquire for %s" % redis_type
    time.sleep(0.2)
    assert not Bullock("mylock", ttl=0.4, redis_cluster=(redis_type==REDIS_CLUSTER)).acquire(), "failed to acquire for %s" % redis_type
    time.sleep(0.8)
    assert Bullock("mylock", ttl=0.4, redis_cluster=(redis_type==REDIS_CLUSTER)).acquire(), "failed to acquire for %s" % redis_type


def test_cannot_release_if_lock_has_expired(redis_type):
    b = Bullock("mylock", ttl=0.1, redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b.acquire(), "failed to acquire for %s" % redis_type
    time.sleep(0.2)
    assert not b.release(), "failed to release for %s" % redis_type


def test_can_renew_lock_to_prevent_it_from_expiring(redis_type):
    b = Bullock("mylock", ttl=0.1, redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b.acquire(), "failed to acquire for %s" % redis_type
    for i in range(10):
        time.sleep(0.05)
        assert b.renew(), "failed to renew for %s" % redis_type
    assert b.release(), "failed to release for %s" % redis_type


def test_can_acquire_locked_lock_if_blocking(redis_type):
    b1 = Bullock("mykey", ttl=0.5, redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b1.acquire(), "failed to acquire for %s" % redis_type
    b2 = Bullock("mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
    assert b2.acquire(blocking=True), "failed to acquire for %s" % redis_type


def test_with_statement(redis_type):
    with Bullock("mykey", redis_cluster=(redis_type==REDIS_CLUSTER)) as l:
        assert l.locked, "failed to lock for %s" % redis_type
        b = Bullock("mykey", redis_cluster=(redis_type==REDIS_CLUSTER))
        assert not b.acquire(), "failed to acquire for %s" % redis_type
    assert b.acquire(), "failed to acquire for %s" % redis_type


def test_can_reuse_available_regular_redis_connection():
    r = redis.StrictRedis(host='redis', port='6379')
    r.flushdb()
    b = Bullock("mylock", redis=r)
    assert b.acquire(), "failed to acquire while reusing connection"


def test_can_reuse_available_cluster_redis_connection():
    r = rediscluster.StrictRedisCluster(host='redis-cluster', port='7000')
    r.flushdb()
    b = Bullock("mylock", redis=r)
    assert b.acquire(), "failed to acquire while reusing connection"