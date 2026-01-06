from __future__ import annotations
import time
from typing import Dict, Optional

class DataStore:
    def __init__(self) -> None:
        self.kv: Dict[bytes, bytes] = {}
        self.expiry: Dict[bytes, float] = {}

    def _touch(self, key: bytes) -> None:
        exp = self.expiry.get(key)
        if exp is None:
            return
        if time.time() >= exp:
            self.kv.pop(key, None)
            self.expiry.pop(key, None)

    def get(self, key: bytes) -> Optional[bytes]:
        self._touch(key)
        return self.kv.get(key)

    def set(self, key: bytes, val: bytes, ex_seconds: Optional[int] = None) -> None:
        self.kv[key] = val
        self.expiry.pop(key, None)
        if ex_seconds is not None:
            self.expiry[key] = time.time() + ex_seconds

    def delete(self, key: bytes) -> bool:
        self._touch(key)
        existed = key in self.kv
        self.kv.pop(key, None)
        self.expiry.pop(key, None)
        return existed

    def expire(self, key: bytes, seconds: int) -> bool:
        self._touch(key)
        if key not in self.kv:
            return False
        self.expiry[key] = time.time() + seconds
        return True

    def ttl(self, key: bytes) -> int:
        self._touch(key)
        if key not in self.kv:
            return -2
        exp = self.expiry.get(key)
        if exp is None:
            return -1
        t = int(exp - time.time())
        return t if t >= 0 else -2

    def flushdb(self) -> None:
        self.kv.clear()
        self.expiry.clear()
