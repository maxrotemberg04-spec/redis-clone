# redis-clone

![CI](https://github.com/maxrotemberg04-spec/redis-clone/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-2563eb)
![License](https://img.shields.io/badge/license-MIT-059669)

A **Redis-compatible server built from scratch in Python** — no frameworks, just the standard library. The real `redis-cli` talks to it, and it serves **~37,000 ops/sec** from four concurrent clients on a MacBook.

Built for systems depth: TCP networking, a wire protocol, an in-memory data store, expiration, and concurrency — every line explainable.

## Features
- **RESP protocol** — parses real Redis wire-format commands, handles partial and pipelined reads (plus plain inline commands, so `nc` works too)
- **13 commands** — `PING` `ECHO` `SET` (with `EX`/`PX`) `GET` `DEL` `EXISTS` `EXPIRE` `TTL` `PERSIST` `INCR` `KEYS` (glob) `TYPE` `FLUSHDB`
- **Expiration, both ways real Redis does it** — *lazy* (purged on touch) **and** *active* (a background sweeper purges keys nobody touches)
- **Concurrency** — thread per client, one shared lock-guarded store
- **Benchmark tool** — measure it yourself (`bench.py`)
- **Tests + CI** — protocol, store, and command-layer unit tests on every push

## Run it
```bash
python server.py
# in another terminal:
redis-cli -p 6379            # or:  nc localhost 6379  (type: ping)
```
```
127.0.0.1:6379> SET session:maria hello EX 60
OK
127.0.0.1:6379> TTL session:maria
(integer) 60
127.0.0.1:6379> KEYS session:*
1) "session:maria"
127.0.0.1:6379> INCR visits
(integer) 1
```

## Benchmark
```
$ python bench.py --threads 4 --ops 5000
clients:      4
total ops:    40,000  (SET+GET pairs: 20,000)
elapsed:      1.06s
throughput:   37,646 ops/sec
```
*(MacBook, Apple Silicon, Python 3.12 — measured, not estimated.)*

## The rate-limiter pattern (why this matters beyond the exercise)
`INCR` + `EXPIRE` is how real APIs cap usage — a counter that self-destructs when the window ends:

```bash
python examples/rate_limiter.py
```
```
limit: 5 requests / 10s window

request 1: ALLOW  (window resets in 10s)
...
request 6: DENY   (window resets in 10s)
```
This exact pattern runs inside my [llm-gateway](https://github.com/maxrotemberg04-spec/llm-gateway) to cap free-tier AI usage — and it's how **my production app** (my AI running coach) enforces coach message limits.

## How it's built
| File | Responsibility |
|---|---|
| `server.py` | TCP server; one thread per client; bytes → parse → dispatch → reply |
| `resp.py` | RESP protocol: decode commands from a byte buffer; encode replies |
| `store.py` | thread-safe store with lazy + active TTL expiry |
| `commands.py` | one handler per command + the dispatch table |
| `bench.py` | multi-client throughput benchmark |
| `examples/` | the INCR+EXPIRE rate limiter |
| `tests/` | unit tests (run in CI) |

## Run the tests
```bash
python -m unittest discover -s tests
```

## Roadmap
- [x] RESP protocol (+ inline commands)
- [x] Core commands · TTL (lazy + active) · concurrency · benchmark · CI
- [ ] Persistence (append-only file)
- [ ] More data types (lists, hashes)
- [ ] Pub/Sub
