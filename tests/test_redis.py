"""Unit tests for the store and the RESP protocol parser."""
import pathlib
import sys
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from store import Store
from resp import parse_command, bulk_string, simple_string, integer


class TestStore(unittest.TestCase):
    def test_set_and_get(self):
        s = Store()
        s.set("k", "v")
        self.assertEqual(s.get("k"), "v")
        self.assertIsNone(s.get("missing"))

    def test_delete_and_exists(self):
        s = Store()
        s.set("a", "1")
        s.set("b", "2")
        self.assertTrue(s.exists("a"))
        self.assertEqual(s.delete("a", "b", "nope"), 2)   # only a and b existed
        self.assertFalse(s.exists("a"))

    def test_incr(self):
        s = Store()
        self.assertEqual(s.incr("n"), 1)
        self.assertEqual(s.incr("n"), 2)
        s.set("x", "not-a-number")
        with self.assertRaises(ValueError):
            s.incr("x")

    def test_lazy_expiry(self):
        s = Store()
        s.set("temp", "v", ttl=0.05)
        self.assertEqual(s.get("temp"), "v")
        self.assertGreaterEqual(s.ttl("temp"), 0)
        time.sleep(0.06)
        self.assertIsNone(s.get("temp"))                  # expired on access
        self.assertEqual(s.ttl("missing"), -2)            # no such key

    def test_expire_command(self):
        s = Store()
        s.set("k", "v")
        self.assertEqual(s.ttl("k"), -1)                  # exists, no expiry
        self.assertEqual(s.expire("k", 100), 1)
        self.assertLessEqual(s.ttl("k"), 100)
        self.assertEqual(s.expire("nope", 100), 0)        # can't expire a missing key


class TestRESP(unittest.TestCase):
    def test_parse_resp_array(self):
        args, consumed = parse_command(b"*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$3\r\nmax\r\n")
        self.assertEqual(args, ["SET", "name", "max"])
        self.assertEqual(consumed, 32)   # *3\r\n$3\r\nSET\r\n$4\r\nname\r\n$3\r\nmax\r\n

    def test_parse_incomplete_returns_none(self):
        args, _ = parse_command(b"*3\r\n$3\r\nSET\r\n")     # only part arrived
        self.assertIsNone(args)

    def test_parse_inline_command(self):
        args, _ = parse_command(b"ping\r\n")               # netcat-style
        self.assertEqual(args, ["ping"])

    def test_encoders(self):
        self.assertEqual(simple_string("OK"), b"+OK\r\n")
        self.assertEqual(integer(7), b":7\r\n")
        self.assertEqual(bulk_string("hi"), b"$2\r\nhi\r\n")
        self.assertEqual(bulk_string(None), b"$-1\r\n")    # null


if __name__ == "__main__":
    unittest.main()
