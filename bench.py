"""Benchmark the server: N threads hammer SET+GET pairs, report ops/sec.

Usage:  python server.py            (terminal 1)
        python bench.py             (terminal 2)
        python bench.py --threads 8 --ops 5000
"""
import argparse
import socket
import threading
import time


def resp(*parts: str) -> bytes:
    out = f"*{len(parts)}\r\n"
    for p in parts:
        out += f"${len(p)}\r\n{p}\r\n"
    return out.encode()


def worker(host, port, ops, tid, results):
    conn = socket.create_connection((host, port))
    for i in range(ops):
        conn.sendall(resp("SET", f"bench:{tid}:{i % 100}", "x" * 32))
        conn.recv(64)
        conn.sendall(resp("GET", f"bench:{tid}:{i % 100}"))
        conn.recv(128)
    conn.close()
    results[tid] = ops * 2                       # each loop = SET + GET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=6379)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--ops", type=int, default=5000, help="SET+GET pairs per thread")
    args = ap.parse_args()

    results = {}
    threads = [threading.Thread(target=worker,
                                args=(args.host, args.port, args.ops, t, results))
               for t in range(args.threads)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    total = sum(results.values())
    print(f"clients:      {args.threads}")
    print(f"total ops:    {total:,}  (SET+GET pairs: {total // 2:,})")
    print(f"elapsed:      {elapsed:.2f}s")
    print(f"throughput:   {total / elapsed:,.0f} ops/sec")


if __name__ == "__main__":
    main()
