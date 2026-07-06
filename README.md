# redis-clone

A **Redis-compatible server built from scratch in Python** — no frameworks, just the standard library. The real `redis-cli` talks to it.

Portfolio project #2 — systems depth: TCP networking, a wire protocol, an in-memory data store, and concurrency.

## Features
- **RESP protocol** — parses real Redis wire-format commands (and plain inline commands, so `nc` works too)
- **Commands** — `PING` · `ECHO` · `SET` (with `EX`/`PX`) · `GET` · `DEL` · `EXISTS` · `EXPIRE` · `TTL` · `INCR`
- **In-memory store** — a thread-safe hash table with **lazy key expiry** (TTL)
- **Concurrency** — one thread per client; many clients at once, sharing one store
- **Tests** — unit tests for the store and the protocol parser

## Run it
```bash
python server.py
# then, in another terminal:
redis-cli -p 6379            # or without it:  nc localhost 6379  (type: ping)
```
```
127.0.0.1:6379> SET name max
OK
127.0.0.1:6379> GET name
"max"
127.0.0.1:6379> INCR visits
(integer) 1
127.0.0.1:6379> EXPIRE name 60
(integer) 1
127.0.0.1:6379> TTL name
(integer) 60
```

## How it's built
| File | Responsibility |
|---|---|
| `server.py` | TCP server; one thread per client; bytes → parse → dispatch → reply |
| `resp.py` | RESP protocol: parse a command out of a byte buffer; encode replies |
| `store.py` | thread-safe in-memory key-value store with lazy TTL expiry |
| `commands.py` | one handler per command + the dispatch table |
| `tests/` | unit tests |

## Run the tests
```bash
python -m unittest discover -s tests
```

## Roadmap
- [x] TCP server
- [x] RESP protocol parsing (+ inline commands)
- [x] `SET` / `GET` on an in-memory hash table
- [x] `EXPIRE` / `TTL` (lazy expiry)
- [x] Multiple clients at once (thread-per-connection, shared store)
- [ ] Persistence (append-only file)
- [ ] More data types (lists, hashes)

## Why build this
The best *"I actually understand systems"* project — raw sockets, protocol parsing, and concurrency with zero frameworks. Every line is explainable in an interview.
