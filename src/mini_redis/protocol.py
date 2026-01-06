from __future__ import annotations
from typing import List, Optional

CRLF = b"\r\n"

def resp_simple(s: str) -> bytes:
    return b"+" + s.encode() + CRLF

def resp_error(msg: str) -> bytes:
    return b"-" + msg.encode() + CRLF

def resp_integer(n: int) -> bytes:
    return b":" + str(n).encode() + CRLF

def resp_bulk(data: Optional[bytes]) -> bytes:
    if data is None:
        return b"$-1\r\n"
    return b"$" + str(len(data)).encode() + CRLF + data + CRLF

def resp_array(items: List[Optional[bytes]]) -> bytes:
    out = bytearray()
    out.extend(b"*" + str(len(items)).encode() + CRLF)
    for it in items:
        out.extend(resp_bulk(it))
    return bytes(out)

def encode_req_as_resp_array(parts: List[bytes]) -> bytes:
    out = bytearray()
    out.extend(b"*" + str(len(parts)).encode() + CRLF)
    for p in parts:
        out.extend(b"$" + str(len(p)).encode() + CRLF)
        out.extend(p + CRLF)
    return bytes(out)

class RESPParser:
    """Parses RESP Arrays of Bulk Strings (what redis-cli sends)."""
    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> None:
        self._buf.extend(data)

    def _readline(self) -> Optional[bytes]:
        idx = self._buf.find(CRLF)
        if idx == -1:
            return None
        line = bytes(self._buf[:idx])
        del self._buf[: idx + 2]
        return line

    def _readn(self, n: int) -> Optional[bytes]:
        if len(self._buf) < n + 2:
            return None
        data = bytes(self._buf[:n])
        if self._buf[n : n + 2] != CRLF:
            raise ValueError("Protocol error: expected CRLF after bulk string")
        del self._buf[: n + 2]
        return data

    def get_request(self) -> Optional[List[bytes]]:
        if not self._buf:
            return None
        if self._buf[:1] != b"*":
            raise ValueError("Protocol error: expected array")

        line = self._readline()
        if line is None:
            return None
        count = int(line[1:])

        parts: List[bytes] = []
        for _ in range(count):
            header = self._readline()
            if header is None:
                return None
            if not header.startswith(b"$"):
                raise ValueError("Protocol error: expected bulk string")
            size = int(header[1:])
            if size == -1:
                parts.append(b"")
                continue
            data = self._readn(size)
            if data is None:
                return None
            parts.append(data)

        return parts
