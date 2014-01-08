import redis
import uuid
import time

WAIT_DELAY = 0.01

class Bullock(object):
    def __init__(self, key=None, host='localhost', port=6379, db=0, ttl=3600):
        self.key = key if key else uuid.uuid4()
        self.ttl = ttl
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.locked = False
        self.expiration = None

    def __enter__(self):
        self.acquire(blocking=True)
        return self

    def __exit__(self, type, value, traceback):
        self.release()

    def acquire(self, blocking=False):
        expiration = self._new_expiration
        self.locked = self.redis.setnx(self.key, expiration)
        if self.locked:
            self.expiration = expiration
        elif self._expired:
            self.locked = self._update_expiration()
        if blocking:
            self.wait()
        return self.locked

    def release(self):
        if not self._locking:
            return False
        return self.redis.delete(self.key)

    def renew(self):
        if not self._locking:
            return False
        return self._update_expiration()

    def wait(self):
        while not self.locked:
            time.sleep(self._time_to_expire + WAIT_DELAY)
            self.locked = self.acquire()
        return True

    def _update_expiration(self):
        expiration = self._new_expiration
        old_expiration = float(self.redis.getset(self.key, expiration))
        if old_expiration < time.time() or old_expiration == self.expiration:
            self.expiration = expiration
            return True
        return False

    @property
    def _locking(self):
        return self.locked and time.time() < self.expiration and not self._expired

    @property
    def _time_to_expire(self):
        timestamp = self.redis.get(self.key)
        if not timestamp:
            return 0
        return max(float(timestamp) - time.time(), 0)

    @property
    def _expired(self):
        return self._time_to_expire == 0

    @property
    def _new_expiration(self):
        return time.time() + self.ttl
