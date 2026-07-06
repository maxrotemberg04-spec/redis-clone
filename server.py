"""A tiny Redis-compatible server — work in progress.

Step 1 (this file): listen on Redis's port (6379) and answer PING with PONG.
Next steps (see README roadmap): parse the RESP protocol, then GET/SET, then
handle many clients at once.
"""
import socket


def main() -> None:
    # 1. Make a TCP socket and allow quick restarts (SO_REUSEADDR).
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 2. Bind to localhost:6379 and start listening.
    server.bind(("localhost", 6379))
    server.listen()
    print("redis-clone listening on localhost:6379  (Ctrl+C to stop)")

    # 3. Accept one client at a time (concurrency comes later).
    while True:
        conn, _addr = server.accept()
        with conn:
            while True:
                data = conn.recv(1024)   # wait for bytes from the client
                if not data:             # client hung up
                    break
                # For now, reply PONG to anything. RESP parsing is the next step.
                conn.sendall(b"+PONG\r\n")


if __name__ == "__main__":
    main()
