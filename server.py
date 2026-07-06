"""A concurrent, Redis-compatible server.

- Speaks the RESP protocol .......... resp.py
- Stores data in a thread-safe map ... store.py
- One thread per client (many at once) . this file

Run:  python server.py
Then: redis-cli -p 6379      (or:  nc localhost 6379  then type `ping`)
"""
import socket
import threading

from resp import parse_command
from store import Store
from commands import dispatch

HOST, PORT = "localhost", 6379


def handle_client(conn: socket.socket, addr, store: Store) -> None:
    """Serve one client until it disconnects. Runs in its own thread."""
    buffer = b""
    with conn:
        while True:
            chunk = conn.recv(4096)
            if not chunk:                       # client hung up
                return
            buffer += chunk
            # One recv can hold several commands, or only part of one.
            while True:
                args, consumed = parse_command(buffer)
                if args is None:                # incomplete — wait for more bytes
                    break
                buffer = buffer[consumed:]
                if args:                        # skip blank lines
                    conn.sendall(dispatch(store, args))


def main() -> None:
    store = Store()                             # ONE store shared by all clients
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"redis-clone listening on {HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr, store),
                             daemon=True).start()
    except KeyboardInterrupt:
        print("\nbye")
    finally:
        server.close()


if __name__ == "__main__":
    main()
