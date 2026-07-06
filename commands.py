"""Command handlers. Each takes (store, args) and returns RESP-encoded bytes.

`args[0]` is the command name; `args[1:]` are its arguments. The HANDLERS table
+ dispatch() turn a parsed command into the right handler.
"""
from resp import simple_string, error, integer, bulk_string


def _wrong_args(name):
    return error(f"ERR wrong number of arguments for '{name}' command")


def cmd_ping(store, args):
    return bulk_string(args[1]) if len(args) > 1 else simple_string("PONG")


def cmd_echo(store, args):
    return bulk_string(args[1]) if len(args) == 2 else _wrong_args("echo")


def cmd_set(store, args):
    # SET key value [EX seconds | PX milliseconds]
    if len(args) < 3:
        return _wrong_args("set")
    key, value, ttl, i = args[1], args[2], None, 3
    while i < len(args):
        opt = args[i].upper()
        if opt in ("EX", "PX") and i + 1 < len(args):
            secs = float(args[i + 1])
            ttl = secs if opt == "EX" else secs / 1000.0
            i += 2
        else:
            return error("ERR syntax error")
    store.set(key, value, ttl)
    return simple_string("OK")


def cmd_get(store, args):
    return bulk_string(store.get(args[1])) if len(args) == 2 else _wrong_args("get")


def cmd_del(store, args):
    return integer(store.delete(*args[1:])) if len(args) >= 2 else _wrong_args("del")


def cmd_exists(store, args):
    if len(args) < 2:
        return _wrong_args("exists")
    return integer(sum(1 for k in args[1:] if store.exists(k)))


def cmd_expire(store, args):
    if len(args) != 3:
        return _wrong_args("expire")
    return integer(store.expire(args[1], int(args[2])))


def cmd_ttl(store, args):
    return integer(store.ttl(args[1])) if len(args) == 2 else _wrong_args("ttl")


def cmd_incr(store, args):
    if len(args) != 2:
        return _wrong_args("incr")
    try:
        return integer(store.incr(args[1]))
    except ValueError as e:
        return error(f"ERR {e}")


def cmd_command(store, args):
    return b"*0\r\n"   # redis-cli sends COMMAND DOCS on connect; ack with empty array


HANDLERS = {
    "PING": cmd_ping, "ECHO": cmd_echo,
    "SET": cmd_set, "GET": cmd_get, "DEL": cmd_del, "EXISTS": cmd_exists,
    "EXPIRE": cmd_expire, "TTL": cmd_ttl, "INCR": cmd_incr,
    "COMMAND": cmd_command,
}


def dispatch(store, args):
    handler = HANDLERS.get(args[0].upper())
    if handler is None:
        return error(f"ERR unknown command '{args[0]}'")
    return handler(store, args)
