"""HTTP tests for the calculator service.

The server exists only inside this test process, on an ephemeral port,
and is stopped in tearDownClass. A permanent background server is not used.
"""

import json
import threading
import unittest
import urllib.error
import urllib.request

from src.server import make_server

# Ignore http_proxy: the service under test is on localhost.
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class TestHttpApi(unittest.TestCase):
    """Requests against a short-lived in-process HTTP server."""

    @classmethod
    def setUpClass(cls):
        cls.httpd = make_server("127.0.0.1", 0)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(
            target=cls.httpd.serve_forever,
            daemon=True,
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def _get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        try:
            with _OPENER.open(url, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return response.status, payload
        except urllib.error.HTTPError as error:
            payload = json.loads(error.read().decode("utf-8"))
            return error.code, payload

    def test_health(self):
        """GET /health returns HTTP 200 and status ok."""
        status, payload = self._get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok"})

    def test_add(self):
        """GET /add?a=2&b=3 returns result 5."""
        status, payload = self._get("/add?a=2&b=3")
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"], 5)
        self.assertEqual(payload["a"], 2)
        self.assertEqual(payload["b"], 3)

    def test_add_invalid_number(self):
        """A non-numeric operand returns HTTP 400."""
        status, payload = self._get("/add?a=2&b=nope")
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_add_missing_parameter(self):
        """A missing operand returns HTTP 400."""
        status, payload = self._get("/add?a=2")
        self.assertEqual(status, 400)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
