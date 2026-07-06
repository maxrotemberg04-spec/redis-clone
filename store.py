"""In-memory key-value store with optional per-key expiry.

Thread-safe: many client threads share ONE store, so every mutation is guarded
by a single lock. Expiry is *lazy* — an expired key is removed the next time
it's touched (this is how real Redis handles most expiration too).
"""
import threading
import time


class Store:
    def __init__(self):
        self._data = {}        # key -> value (str)
        self._expiry = {}      # key -> unix timestamp when it expires
        self._lock = threading.Lock()

    # --- internal; always called while the lock is held ---
    def _purge_if_expired(self, key):
        exp = self._expiry.get(key)
        if exp is not None and exp <= time.time():
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    # --- public API ---
    def set(self, key, value, ttl=None):
        with self._lock:
            self._data[key] = value
            if ttl is None:
                self._expiry.pop(key, None)
            else:
                self._expiry[key] = time.time() + ttl

    def get(self, key):
        with self._lock:
            self._purge_if_expired(key)
            return self._data.get(key)

    def delete(self, *keys):
        with self._lock:
            removed = 0
            for k in keys:
                self._purge_if_expired(k)
                if k in self._data:
                    self._data.pop(k, None)
                    self._expiry.pop(k, None)
                    removed += 1
            return removed

    def exists(self, key):
        with self._lock:
            self._purge_if_expired(key)
            return key in self._data

    def expire(self, key, seconds):
        with self._lock:
            self._purge_if_expired(key)
            if key not in self._data:
                return 0
            self._expiry[key] = time.time() + seconds
            return 1

    def ttl(self, key):
        with self._lock:
            self._purge_if_expired(key)
            if key not in self._data:
                return -2                        # no such key
            if key not in self._expiry:
                return -1                        # key exists, but never expires
            return max(0, int(round(self._expiry[key] - time.time())))

    def incr(self, key):
        with self._lock:
            self._purge_if_expired(key)
            current = self._data.get(key, "0")
            try:
                value = int(current) + 1
            except ValueError:
                raise ValueError("value is not an integer or out of range")
            self._data[key] = str(value)
            return value
