import redis
import uuid
import time


class Bullock(object):
    def __init__(self, key=None, host='localhost', port=6379, db=0, ttl=3600):
        self.key = key if key else uuid.uuid4()
        self.ttl = ttl
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.locked = False
        self.expiration = None

    def acquire(self):
        expiration = self._new_expiration
        self.locked = self.redis.setnx(self.key, expiration)
        if self.locked:
            self.expiration = expiration
        elif self._expired:
            self.locked = self._update_expiration()
        return self.locked

    def release(self):
        if not self._locking:
            return False
        return self.redis.delete(self.key)

    def renew(self):
        if not self._locking:
            return False
        return self._update_expiration()

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
    def _expired(self):
        return float(self.redis.get(self.key)) < time.time()

    @property
    def _new_expiration(self):
        return time.time() + self.ttl
