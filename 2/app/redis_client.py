import threading
import time

import redis
from app.config import Config


class MemoryStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._strings = {}
        self._hashes = {}
        self._sets = {}
        self._zsets = {}
        self._expires = {}

    def _is_expired(self, key):
        if key in self._expires:
            if time.time() > self._expires[key]:
                self._raw_delete(key)
                return True
        return False

    def _raw_delete(self, key):
        self._strings.pop(key, None)
        self._hashes.pop(key, None)
        self._sets.pop(key, None)
        self._zsets.pop(key, None)
        self._expires.pop(key, None)

    def get(self, key):
        with self._lock:
            if self._is_expired(key):
                return None
            return self._strings.get(key)

    def set(self, key, value, ex=None):
        with self._lock:
            self._raw_delete(key)
            self._strings[key] = value
            if ex:
                self._expires[key] = time.time() + ex
            return True

    def setnx(self, key, value, ex=None):
        with self._lock:
            if self._is_expired(key):
                self._raw_delete(key)
            if key in self._strings:
                return False
            self._strings[key] = value
            if ex:
                self._expires[key] = time.time() + ex
            return True

    def delete(self, key):
        with self._lock:
            existed = key in self._strings or key in self._hashes or key in self._sets or key in self._zsets
            self._raw_delete(key)
            return 1 if existed else 0

    def exists(self, key):
        with self._lock:
            if self._is_expired(key):
                return 0
            return 1 if (key in self._strings or key in self._hashes or key in self._sets or key in self._zsets) else 0

    def incr(self, key):
        with self._lock:
            if self._is_expired(key):
                self._raw_delete(key)
            val = int(self._strings.get(key, 0)) + 1
            self._strings[key] = str(val)
            return val

    def zincrby(self, key, amount, member):
        with self._lock:
            if self._is_expired(key):
                self._raw_delete(key)
            if key not in self._zsets:
                self._zsets[key] = {}
            score = self._zsets[key].get(member, 0.0) + amount
            self._zsets[key][member] = score
            return score

    def zrange(self, key, start, end, desc=True, withscores=True):
        with self._lock:
            if self._is_expired(key):
                return []
            if key not in self._zsets:
                return []
            items = list(self._zsets[key].items())
            items.sort(key=lambda x: (-x[1] if desc else x[1], x[0]))
            if end == -1:
                end = len(items)
            else:
                end = end + 1
            items = items[start:end]
            if withscores:
                return [(m, s) for m, s in items]
            return [m for m, s in items]

    def hset(self, key, mapping):
        with self._lock:
            if self._is_expired(key):
                self._raw_delete(key)
            if key not in self._hashes:
                self._hashes[key] = {}
            self._hashes[key].update(mapping)
            return len(mapping)

    def hgetall(self, key):
        with self._lock:
            if self._is_expired(key):
                return {}
            return dict(self._hashes.get(key, {}))

    def hget(self, key, field):
        with self._lock:
            if self._is_expired(key):
                return None
            return self._hashes.get(key, {}).get(field)

    def hdel(self, key, *fields):
        with self._lock:
            if key not in self._hashes:
                return 0
            count = 0
            for f in fields:
                if f in self._hashes[key]:
                    del self._hashes[key][f]
                    count += 1
            return count

    def sadd(self, key, *values):
        with self._lock:
            if self._is_expired(key):
                self._raw_delete(key)
            if key not in self._sets:
                self._sets[key] = set()
            before = len(self._sets[key])
            self._sets[key].update(values)
            return len(self._sets[key]) - before

    def smembers(self, key):
        with self._lock:
            if self._is_expired(key):
                return set()
            return set(self._sets.get(key, set()))

    def srem(self, key, *values):
        with self._lock:
            if key not in self._sets:
                return 0
            before = len(self._sets[key])
            self._sets[key] -= set(values)
            return before - len(self._sets[key])

    def expire(self, key, seconds):
        with self._lock:
            if key in self._strings or key in self._hashes or key in self._sets or key in self._zsets:
                self._expires[key] = time.time() + seconds
                return True
            return False

    def ttl(self, key):
        with self._lock:
            if key not in self._expires:
                return -1
            remaining = self._expires[key] - time.time()
            return max(0, int(remaining))

    def flushdb(self):
        with self._lock:
            self._strings.clear()
            self._hashes.clear()
            self._sets.clear()
            self._zsets.clear()
            self._expires.clear()
        return True


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self._use_memory = False
        self._memory = MemoryStore()
        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
            self.client.ping()
        except Exception as e:
            self._use_memory = True
            print(f"[Memory] Redis 不可用 ({e})，使用内存存储（线程安全，支持原子操作）")

    def _store(self):
        return self._memory if self._use_memory else self.client

    def get(self, key):
        return self._store().get(key)

    def set(self, key, value, ex=None):
        return self._store().set(key, value, ex=ex)

    def setnx(self, key, value, ex=None):
        if self._use_memory:
            return self._memory.setnx(key, value, ex=ex)
        if ex:
            return self.client.set(key, value, ex=ex, nx=True)
        return self.client.set(key, value, nx=True)

    def delete(self, key):
        return self._store().delete(key)

    def exists(self, key):
        return self._store().exists(key)

    def incr(self, key):
        return self._store().incr(key)

    def zincrby(self, key, amount, member):
        return self._store().zincrby(key, amount, member)

    def zrange(self, key, start, end, desc=True, withscores=True):
        return self._store().zrange(key, start, end, desc=desc, withscores=withscores)

    def hset(self, key, mapping):
        return self._store().hset(key, mapping=mapping)

    def hgetall(self, key):
        return self._store().hgetall(key)

    def hget(self, key, field):
        return self._store().hget(key, field)

    def hdel(self, key, *fields):
        return self._store().hdel(key, *fields)

    def sadd(self, key, *values):
        return self._store().sadd(key, *values)

    def smembers(self, key):
        return self._store().smembers(key)

    def srem(self, key, *values):
        return self._store().srem(key, *values)

    def expire(self, key, seconds):
        return self._store().expire(key, seconds)

    def ttl(self, key):
        return self._store().ttl(key)

    def flushdb(self):
        return self._store().flushdb()


redis_client = RedisClient()
