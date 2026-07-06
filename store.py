"""In-memory key-value store with per-key expiry.

Thread-safe: many client threads share ONE store, so every mutation is guarded
by a single lock. Expiration is handled the way real Redis does it, twice over:
  * lazy   — an expired key is purged the moment it's touched
  * active — an optional background sweeper purges expired keys on an interval,
             so they die even if nobody ever touches them again
"""
import threading
import time


class Store:
    def __init__(self, sweep_interval: float | None = None):
        self._data = {}        # key -> value (str)
        self._expiry = {}      # key -> unix timestamp when it expires
        self._lock = threading.Lock()
        if sweep_interval:
            t = threading.Thread(target=self._sweep_loop, args=(sweep_interval,),
                                 daemon=True)
            t.start()

    def _sweep_loop(self, interval: float) -> None:
        """Active expiry: periodically purge every expired key."""
        while True:
            time.sleep(interval)
            now = time.time()
            with self._lock:
                for key in [k for k, exp in self._expiry.items() if exp <= now]:
                    self._data.pop(key, None)
                    self._expiry.pop(key, None)

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

    def keys(self):
        with self._lock:
            now = time.time()
            for key in [k for k, exp in self._expiry.items() if exp <= now]:
                self._data.pop(key, None)
                self._expiry.pop(key, None)
            return list(self._data.keys())

    def persist(self, key):
        """Remove a key's expiry. Returns 1 if an expiry was removed."""
        with self._lock:
            self._purge_if_expired(key)
            if key in self._data and key in self._expiry:
                self._expiry.pop(key)
                return 1
            return 0

    def flush(self):
        with self._lock:
            self._data.clear()
            self._expiry.clear()
