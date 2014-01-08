import redis
import uuid
import time


class Bullock(object):
    def __init__(self, key=None, host='localhost', port=6379, db=0, ttl=3600):
        self.key = key if key else uuid.uuid4()
        self.ttl = ttl
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.locking = False

    def lock(self):
        expiration = time.time() + self.ttl
        self.locking = self.redis.setnx(self.key, expiration)
        if not self.locking and self._expired():
            self.locking = float(self.redis.getset(self.key, expiration)) < time.time()
        return self.locking

    def release(self):
        if not self.locking:
            return False
        return self.redis.delete(self.key)

    def _expired(self):
        return float(self.redis.get(self.key)) < time.time()
