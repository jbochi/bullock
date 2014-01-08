import redis
import uuid


class Bullock(object):
    def __init__(self, key=None, host='localhost', port=6379, db=0):
        self.key = key if key else uuid.uuid4()
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.locking = False

    def lock(self):
        self.locking = self.redis.setnx(self.key, "locked")
        return self.locking

    def release(self):
        if not self.locking:
            return False
        return self.redis.delete(self.key)
