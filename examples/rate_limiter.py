"""Rate limiting with INCR + EXPIRE — the pattern behind real API rate limits.

Each user gets a counter key that self-destructs when the window ends:
    INCR   rl:<user>          -> requests used this window
    EXPIRE rl:<user> <window> -> set the window on first use
    allowed = count <= limit

This exact pattern runs (in-process) inside my llm-gateway to cap free users
at 5 requests/week — and it's how my production app's coach message caps work.

Usage:  python server.py                    (terminal 1)
        python examples/rate_limiter.py     (terminal 2)
"""
import socket
import sys


def resp(*parts: str) -> bytes:
    out = f"*{len(parts)}\r\n"
    for p in parts:
        out += f"${len(p)}\r\n{p}\r\n"
    return out.encode()


class RedisRateLimiter:
    def __init__(self, host="localhost", port=6379, limit=5, window_seconds=10):
        self.conn = socket.create_connection((host, port))
        self.limit = limit
        self.window = window_seconds

    def _cmd(self, *parts):
        self.conn.sendall(resp(*parts))
        return self.conn.recv(256)

    def allow(self, user: str) -> tuple[bool, int]:
        """Returns (allowed, seconds_until_reset)."""
        key = f"rl:{user}"
        count = int(self._cmd("INCR", key)[1:].split(b"\r\n")[0])
        if count == 1:                                # first hit -> start the window
            self._cmd("EXPIRE", key, str(self.window))
        ttl = int(self._cmd("TTL", key)[1:].split(b"\r\n")[0])
        return count <= self.limit, max(0, ttl)


if __name__ == "__main__":
    try:
        rl = RedisRateLimiter(limit=5, window_seconds=10)
    except OSError:
        sys.exit("start the server first:  python server.py")

    print("limit: 5 requests / 10s window\n")
    for i in range(1, 9):
        allowed, reset = rl.allow("maria")
        verdict = "ALLOW" if allowed else "DENY "
        print(f"request {i}: {verdict}  (window resets in {reset}s)")
    print("\nrequests 6-8 denied -> the counter expires -> maria is allowed again.")
