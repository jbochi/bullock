import redis
import rediscluster
import time
import uuid


WAIT_DELAY = 0.01

class Bullock(object):
    def __init__(self, key, value=None, host='localhost', port=6379, db=0, password=None, ttl=3600, redis_cluster=False):
        self.key = key
        self.ttl = ttl
        self.value = value if value is not None else str(uuid.uuid4())
        if redis_cluster:
            self.redis = rediscluster.StrictRedisCluster(host=host, port=port, password=password)
        else:
            self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        self._acquire_lock = self.redis.register_script("""
            local key = KEYS[1]
            local value = ARGV[1]
            local ttl = ARGV[2]
            local current_value = redis.call('GET', key)
            if current_value == value or current_value == false then
                redis.call('PSETEX', key, ttl, value)
                return 1
            end
            return 0
        """)
        self._release = self.redis.register_script("""
            local key = KEYS[1]
            local value = ARGV[1]
            if redis.call("GET", key) == value then
                return redis.call("DEL", key)
            else
                return 0
            end
        """)
        self.locked = False
        self.expiration = None

    def __enter__(self):
        self.acquire(blocking=True)
        return self

    def __exit__(self, type, value, traceback):
        self.release()

    def acquire(self, blocking=False):
        expiration = time.time() + self.ttl
        self.locked = bool(self._acquire_lock(keys=[self.key], args=[self.value, int(self.ttl * 1000)]))
        if self.locked:
            self.expiration = expiration
        if blocking:
            self.wait()
        return self.locked

    def release(self):
        return bool(self._release(keys=[self.key], args=[self.value]))

    def renew(self):
        return self.acquire(blocking=False)

    def wait(self):
        while not self.locked:
            time.sleep(self._time_to_expire + WAIT_DELAY)
            self.locked = self.acquire()
        return True

    @property
    def _time_to_expire(self):
        return float(self.redis.pttl(self.key) or 0) / 1000
