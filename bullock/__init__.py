import redis
import uuid


class Bullock(object):
    def __init__(self, key=None, host='localhost', port=6379, db=0):
        self.key = key if key else uuid.uuid4()
        self.redis = redis.StrictRedis(host=host, port=port, db=db)

    def lock(self):
        return self.redis.setnx(self.key, "locked")