"""RESP — the Redis Serialization Protocol.

Two jobs:
  parse_command(buf)  — decode ONE client command from a byte buffer
  encoders            — build replies (simple string, error, integer, bulk string)

A RESP request is an array of bulk strings. `SET name max` arrives as:
    *3\\r\\n$3\\r\\nSET\\r\\n$4\\r\\nname\\r\\n$3\\r\\nmax\\r\\n
  *3   -> "3 elements follow"
  $3   -> "the next string is 3 bytes"
We also accept plain "inline" commands (a line like `ping`) so you can test
with netcat, not just redis-cli.
"""

CRLF = b"\r\n"


def _read_line(buf: bytes, start: int):
    """Return (line_bytes, index_after_crlf), or (None, None) if no full line yet."""
    end = buf.find(CRLF, start)
    if end == -1:
        return None, None
    return buf[start:end], end + 2


def parse_command(buf: bytes):
    """Try to parse one command from the front of `buf`.

    Returns (args, consumed):
      args      list[str] of command + arguments, or None if the buffer is incomplete
      consumed  bytes to drop from the buffer once this command is parsed
    """
    if not buf:
        return None, 0

    # --- Inline command (not RESP): one line of space-separated words ---
    if buf[:1] != b"*":
        nl = buf.find(b"\n")
        if nl == -1:
            return None, 0                       # wait for a full line
        line = buf[:nl].rstrip(b"\r")
        return [p.decode() for p in line.split()], nl + 1

    # --- RESP array of bulk strings ---
    header, pos = _read_line(buf, 1)
    if header is None:
        return None, 0
    count = int(header)
    args = []
    for _ in range(count):
        if pos >= len(buf) or buf[pos:pos + 1] != b"$":
            return None, 0                       # need more bytes
        length_line, pos = _read_line(buf, pos + 1)
        if length_line is None:
            return None, 0
        length = int(length_line)
        if pos + length + 2 > len(buf):
            return None, 0                       # the string hasn't fully arrived
        args.append(buf[pos:pos + length].decode())
        pos += length + 2                        # skip the data + its CRLF
    return args, pos


# --- reply encoders ---
def simple_string(s: str) -> bytes:
    return b"+" + s.encode() + CRLF


def error(msg: str) -> bytes:
    return b"-" + msg.encode() + CRLF


def integer(n: int) -> bytes:
    return b":" + str(n).encode() + CRLF


def bulk_string(s) -> bytes:
    if s is None:
        return b"$-1\r\n"                         # null bulk string ("no value")
    data = s.encode() if isinstance(s, str) else s
    return b"$" + str(len(data)).encode() + CRLF + data + CRLF


def array(items) -> bytes:
    """RESP array of bulk strings (what KEYS returns)."""
    out = b"*" + str(len(items)).encode() + CRLF
    for item in items:
        out += bulk_string(item)
    return out
