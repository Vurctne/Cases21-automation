import base64
import http.server
import json
import tempfile
import threading
import unittest

import pa

SHOT = b"\xff\xd8fake-jpeg"


class FakeFlow(http.server.BaseHTTPRequestHandler):
    polls = 0
    flow_status = 202

    def log_message(self, *args):
        pass

    def _reply(self, status, body=b"", headers=()):
        self.send_response(status)
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path == "/token":
            assert b"client_credentials" in body
            return self._reply(200, json.dumps({"access_token": "tok"}).encode())
        assert self.headers["Authorization"] == "Bearer tok"
        assert json.loads(body) == {"steps": [{"type": "wait", "value": 1}]}
        if FakeFlow.flow_status == 202:
            return self._reply(202, headers=[("Location", f"http://127.0.0.1:{self.server.server_port}/poll"),
                                             ("Retry-After", "0")])
        self._reply(FakeFlow.flow_status, b'{"error": "machine offline"}')

    def do_GET(self):
        assert self.headers["Authorization"] == "Bearer tok"
        FakeFlow.polls += 1
        if FakeFlow.polls < 2:
            return self._reply(202, headers=[("Location", f"http://127.0.0.1:{self.server.server_port}/poll"),
                                             ("Retry-After", "0")])
        self._reply(200, json.dumps({"error": "", "screenshot": base64.b64encode(SHOT).decode()}).encode())


class PaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), FakeFlow)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeFlow.polls = 0
        FakeFlow.flow_status = 202

    def test_async_flow_is_polled_and_screenshot_saved(self):
        token = pa.get_token(self.base + "/token", "id", "secret")
        result = pa.call_flow(self.base + "/flow", token, {"steps": [{"type": "wait", "value": 1}]})
        self.assertEqual(FakeFlow.polls, 2)
        with tempfile.TemporaryDirectory() as d:
            result = pa.save_screenshot(result, d)
            with open(result["screenshot_path"], "rb") as f:
                self.assertEqual(f.read(), SHOT)
        self.assertEqual(result["error"], "")
        self.assertNotIn("screenshot", result)

    def test_flow_error_is_raised(self):
        FakeFlow.flow_status = 500
        with self.assertRaisesRegex(RuntimeError, "HTTP 500.*machine offline"):
            pa.call_flow(self.base + "/flow", "tok", {"steps": [{"type": "wait", "value": 1}]})


if __name__ == "__main__":
    unittest.main()
