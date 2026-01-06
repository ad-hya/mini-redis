from __future__ import annotations
import os
from typing import Optional, List

from .protocol import RESPParser

class AOF:
    def __init__(self, path: str = "appendonly.aof") -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._fh = open(self.path, "ab", buffering=0)

    def append(self, raw: bytes) -> None:
        self._fh.write(raw)

    def close(self) -> None:
        try:
            self._fh.flush()
            os.fsync(self._fh.fileno())
        except Exception:
            pass
        try:
            self._fh.close()
        except Exception:
            pass

def iter_aof_commands(path: str) -> List[List[bytes]]:
    if not os.path.exists(path):
        return []
    data = open(path, "rb").read()
    p = RESPParser()
    p.feed(data)
    cmds: List[List[bytes]] = []
    while True:
        req = p.get_request()
        if req is None:
            break
        cmds.append(req)
    return cmds
