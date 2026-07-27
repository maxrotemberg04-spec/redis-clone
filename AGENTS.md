# redis-clone — agent instructions

A Redis-compatible server built from scratch in Python — no frameworks, just the standard library. The real `redis-cli` talks to it (~37,000 ops/sec from four concurrent clients). Built for systems depth: TCP networking, the RESP wire protocol, an in-memory store, expiration, concurrency.

**Public portfolio repo — this code is part of Max's pitch; keep it interview-clean.** Python 3.12, stdlib only in the server — don't add dependencies. Tests: `python -m unittest discover -s tests -v` (same as CI).

## Hard rules

1. **Commits are 100% Max.** Never add AI co-author trailers or AI attribution to commits, code comments, or docs.
2. **Evidence before "done"** — run the tests and show the output.
3. **No secrets in git**; `.env` stays local.
4. **Teach while doing** — Max is learning; explain the why in plain terms as you work.
5. **Cross-model review before merge** on non-trivial changes — whichever model wrote it, the other reviews.

Keep diffs small and readable — every line in this repo should be explainable in an interview.
