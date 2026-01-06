from __future__ import annotations
import socket
import threading
from typing import List, Optional, Tuple

from .protocol import (
    RESPParser, resp_simple, resp_error, resp_integer, resp_bulk, resp_array, encode_req_as_resp_array
)
from .datastore import DataStore
from .aof import AOF, iter_aof_commands

class MiniRedis:
    def __init__(self, store: DataStore, aof: Optional[AOF] = None) -> None:
        self.store = store
        self.aof = aof
        self._replaying = False

    def _should_log(self, cmd: bytes) -> bool:
        return cmd in {b"SET", b"DEL", b"MSET", b"FLUSHDB", b"EXPIRE"}

    def handle(self, req: List[bytes]) -> bytes:
        if not req:
            return resp_error("ERR empty command")

        cmd = req[0].upper()
        args = req[1:]

        if (not self._replaying) and self.aof and self._should_log(cmd):
            self.aof.append(encode_req_as_resp_array([cmd] + args))

        if cmd == b"PING":
            return resp_simple("PONG") if not args else resp_bulk(args[0])

        if cmd == b"ECHO":
            if len(args) != 1:
                return resp_error("ERR wrong number of arguments for 'echo'")
            return resp_bulk(args[0])

        if cmd == b"SET":
            # SET key value [EX seconds]
            if len(args) not in (2, 4):
                return resp_error("ERR wrong number of arguments for 'set'")
            key, val = args[0], args[1]
            ex = None
            if len(args) == 4:
                if args[2].upper() != b"EX":
                    return resp_error("ERR only EX option supported")
                try:
                    ex = int(args[3])
                except ValueError:
                    return resp_error("ERR invalid expire time")
            self.store.set(key, val, ex_seconds=ex)
            return resp_simple("OK")

        if cmd == b"GET":
            if len(args) != 1:
                return resp_error("ERR wrong number of arguments for 'get'")
            return resp_bulk(self.store.get(args[0]))

        if cmd == b"DEL":
            if len(args) < 1:
                return resp_error("ERR wrong number of arguments for 'del'")
            deleted = sum(1 for k in args if self.store.delete(k))
            return resp_integer(deleted)

        if cmd == b"MSET":
            if len(args) < 2 or len(args) % 2 != 0:
                return resp_error("ERR wrong number of arguments for 'mset'")
            for i in range(0, len(args), 2):
                self.store.set(args[i], args[i + 1], ex_seconds=None)
            return resp_simple("OK")

        if cmd == b"MGET":
            if len(args) < 1:
                return resp_error("ERR wrong number of arguments for 'mget'")
            return resp_array([self.store.get(k) for k in args])

        if cmd == b"EXPIRE":
            if len(args) != 2:
                return resp_error("ERR wrong number of arguments for 'expire'")
            try:
                seconds = int(args[1])
            except ValueError:
                return resp_error("ERR invalid expire time")
            return resp_integer(1 if self.store.expire(args[0], seconds) else 0)

        if cmd == b"TTL":
            if len(args) != 1:
                return resp_error("ERR wrong number of arguments for 'ttl'")
            return resp_integer(self.store.ttl(args[0]))

        if cmd == b"FLUSHDB":
            self.store.flushdb()
            return resp_simple("OK")

        return resp_error(f"ERR unknown command '{cmd.decode(errors='ignore')}'")

def client_thread(conn: socket.socket, addr: Tuple[str, int], engine: MiniRedis) -> None:
    parser = RESPParser()
    try:
        while True:
            data = conn.recv(65536)
            if not data:
                return
            parser.feed(data)
            while True:
                req = parser.get_request()
                if req is None:
                    break
                resp = engine.handle(req)
                conn.sendall(resp)
    finally:
        try:
            conn.close()
        except Exception:
            pass

def serve(host: str = "127.0.0.1", port: int = 6379, aof_path: str = "appendonly.aof") -> None:
    aof = AOF(aof_path)
    store = DataStore()
    engine = MiniRedis(store=store, aof=aof)

    # Replay
    cmds = iter_aof_commands(aof_path)
    engine._replaying = True
    for req in cmds:
        engine.handle(req)
    engine._replaying = False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(128)
        print(f"MiniRedis listening on {host}:{port} (AOF={aof_path})")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=client_thread, args=(conn, addr, engine), daemon=True)
            t.start()
