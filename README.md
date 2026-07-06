# redis-clone

A **Redis-compatible server built from scratch** — to understand TCP networking, wire protocols, and in-memory data stores. The real `redis-cli` will talk to it.

Portfolio project #2 — systems depth (the CS-fundamentals muscle).

## What it does (so far)
- Listens on port **6379** (Redis's port) and answers `PING` → `PONG`.

## Run it
```bash
python server.py
# then, in another terminal:
redis-cli -p 6379 ping        # → PONG
# (no redis-cli? use:  nc localhost 6379   then type anything)
```

## Roadmap
- [x] TCP server that responds to `PING`
- [ ] Parse the **RESP protocol** (how Redis encodes commands over the wire)
- [ ] `SET` / `GET` backed by an in-memory hash table
- [ ] `EXPIRE` / TTL
- [ ] Handle **multiple clients at once** (concurrency)

## Why build this
The single best *"I actually understand systems"* project — raw sockets, protocol parsing, and concurrency, with zero frameworks. Interviewers respect it.
