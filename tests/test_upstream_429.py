#!/usr/bin/env python3
"""Diagnostic d'un 429 amont : transport (mémoire d'échéance) et journal MCP."""

from __future__ import annotations

import email.utils
import io
import logging
import sys
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
sys.path.insert(0, str(ROOT))

import droit_francais.transport as transport  # noqa: E402
from droit_francais.errors import LegifranceError  # noqa: E402
from droit_francais.transport import http_get_json  # noqa: E402
from mcp_server import server as mcp_app  # noqa: E402
from mcp_server.runtime import RuntimeCapacityError  # noqa: E402

URL = "https://api.example.test/dila/search?q=secret-param"


class _Ok:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return b'{"ok": true}'


def _429(headers: dict, body: bytes = b"slow   down\n now"):
    return urllib.error.HTTPError(URL, 429, "Too Many", headers, io.BytesIO(body))


@mock.patch("droit_francais.transport._sleep")
@mock.patch("droit_francais.transport.urllib.request.urlopen")
class TransportDiagnosticTests(unittest.TestCase):
    def setUp(self):
        transport.reset_backoff()
        self.addCleanup(transport.reset_backoff)

    def test_retry_after_as_http_date_is_honoured(self, urlopen, sleep):
        when = email.utils.formatdate(time.time() + 3, usegmt=True)
        urlopen.side_effect = [_429({"Retry-After": when}), _Ok()]
        self.assertTrue(http_get_json(URL, {})["ok"])
        (delay,) = sleep.call_args.args
        self.assertTrue(1.0 <= delay <= 3.5, delay)

    def test_upstream_keeps_limit_headers_and_no_query(self, urlopen, sleep):
        urlopen.side_effect = [
            _429(
                {
                    "Retry-After": "30",
                    "X-RateLimit-Remaining": "0",
                    "X-Daily-Quota": "  a   b ",
                    "Content-Type": "text/plain",
                },
                b"x" * 400,
            )
        ]
        with self.assertRaises(LegifranceError) as caught:
            http_get_json(URL, {})
        exc = caught.exception
        up = exc.upstream
        self.assertEqual(429, up["status"])
        self.assertEqual("api.example.test", up["host"])
        self.assertEqual("/dila/search", up["path"])
        self.assertEqual("30", up["retry_after_raw"])
        self.assertEqual(30, up["retry_after_s"])
        self.assertEqual(
            {"retry-after": "30", "x-ratelimit-remaining": "0", "x-daily-quota": "a b"},
            up["rate_limit_headers"],
        )
        self.assertEqual(1, up["attempts"])
        self.assertEqual(0, up["waited_s"])
        self.assertFalse(up["local_backoff"])
        self.assertEqual(200, len(up["body_excerpt"]))
        self.assertNotIn("secret-param", repr(up))
        self.assertIn("réessayer dans 30 s", str(exc))

    def test_attempts_and_wait_are_counted(self, urlopen, sleep):
        urlopen.side_effect = [_429({"Retry-After": "1"}) for _ in range(5)]
        with self.assertRaises(LegifranceError) as caught:
            http_get_json(URL, {})
        up = caught.exception.upstream
        self.assertEqual(transport.MAX_ATTEMPTS, up["attempts"])
        self.assertEqual(float(transport.MAX_ATTEMPTS - 1), up["waited_s"])

    def test_429_without_retry_after_keeps_the_generic_message(self, urlopen, sleep):
        urlopen.side_effect = [_429({}) for _ in range(5)]
        with self.assertRaises(LegifranceError) as caught:
            http_get_json(URL, {})
        self.assertIn("quelques instants", str(caught.exception))
        self.assertIsNone(caught.exception.upstream["retry_after_s"])

    def test_deadline_is_remembered_then_released(self, urlopen, sleep):
        clock = [1000.0]
        with mock.patch.object(transport, "_now", lambda: clock[0]):
            urlopen.side_effect = [_429({"Retry-After": "30"}), _Ok()]
            with self.assertRaises(LegifranceError):
                http_get_json(URL, {})
            self.assertEqual(1, urlopen.call_count)

            clock[0] += 10
            with self.assertRaises(LegifranceError) as caught:
                http_get_json(URL, {})
            self.assertEqual(1, urlopen.call_count, "aucun appel réseau pendant l'échéance")
            up = caught.exception.upstream
            self.assertTrue(up["local_backoff"])
            self.assertEqual(20, up["retry_after_s"])
            self.assertEqual(429, caught.exception.http_status)
            self.assertIn("réessayer dans 20 s", str(caught.exception))

            # Un autre chemin du même hôte n'est pas touché.
            other = "https://api.example.test/dila/other"
            urlopen.side_effect = [_Ok()]
            self.assertTrue(http_get_json(other, {})["ok"])

            clock[0] += 25
            urlopen.side_effect = [_Ok()]
            self.assertTrue(http_get_json(URL, {})["ok"])

    def test_store_is_bounded_and_purged(self, urlopen, sleep):
        clock = [0.0]
        with mock.patch.object(transport, "_now", lambda: clock[0]):
            for i in range(100):
                clock[0] += 0.001
                transport._remember_backoff("h", f"/p{i}", 100)
            self.assertLessEqual(len(transport._backoff), 64)
            clock[0] += 200
            self.assertIsNone(transport._backoff_remaining("h", "/p99"))
            self.assertEqual({}, transport._backoff)


class JournalTests(unittest.TestCase):
    def setUp(self):
        transport.reset_backoff()
        self.addCleanup(transport.reset_backoff)

    def test_retry_line_is_emitted_when_root_logger_is_warning(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("droit_francais.transport")
        root = logging.getLogger()
        previous = root.level
        root.setLevel(logging.WARNING)
        logger.addHandler(handler)
        self.addCleanup(root.setLevel, previous)
        self.addCleanup(logger.removeHandler, handler)
        with mock.patch("droit_francais.transport._sleep"), mock.patch(
            "droit_francais.transport.urllib.request.urlopen",
            side_effect=[_429({"Retry-After": "1"}), _Ok()],
        ):
            http_get_json(URL, {})
        self.assertIn("retry host=api.example.test cause=HTTP 429", stream.getvalue())

    def _fail_with_429(self):
        def operation():
            return http_get_json(URL, {})

        with mock.patch("droit_francais.transport._sleep"), mock.patch(
            "droit_francais.transport.urllib.request.urlopen",
            side_effect=[_429({"Retry-After": "30", "X-RateLimit-Remaining": "0"})],
        ), self.assertLogs("droit_francais.mcp", level="WARNING") as journal:
            with self.assertRaises(mcp_app.ToolError) as caught:
                mcp_app._safe_call(operation)
        return " | ".join(journal.output), str(caught.exception)

    def test_upstream_error_line_carries_diagnostic_without_query(self):
        line, reply = self._fail_with_429()
        for expected in (
            "outcome=upstream_error",
            "status=429",
            "host=api.example.test",
            "path=/dila/search",
            "retry_after_s=30",
            "attempts=1",
            "waited_s=0.0",
            "local_backoff=false",
            "rate_limit=retry-after:30;x-ratelimit-remaining:0",
        ):
            self.assertIn(expected, line)
        self.assertNotIn("secret-param", line)
        self.assertNotIn("q=", line)
        self.assertNotIn("slow", line)  # corps amont jamais journalisé
        self.assertIn("réessayer dans 30 s", reply)
        self.assertNotIn("x-ratelimit", reply.lower())

    def test_throttled_line_names_principal_and_limiter(self):
        for target, name, limiter in (
            (mcp_app.USER_LIMITER, "check", "user"),
            (mcp_app.GOVERNOR, "slot", "instance"),
        ):
            with mock.patch.object(target, name, side_effect=RuntimeCapacityError("trop")):
                with self.assertLogs("droit_francais.mcp", level="WARNING") as journal:
                    with self.assertRaises(mcp_app.ToolError):
                        mcp_app._safe_call(lambda: {})
            line = " | ".join(journal.output)
            self.assertIn("outcome=throttled", line)
            self.assertIn("principal=anonyme", line)
            self.assertIn(f"limiter={limiter}", line)


if __name__ == "__main__":
    unittest.main()
