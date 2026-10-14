"""Send steps to the cases21-bridge cloud flow and save the screenshot it returns.

Usage:
  python bridge/pa.py '{"steps": [{"type": "keys", "value": "ACME01{Tab}"}]}'
  python bridge/pa.py - < steps.json

Step types: keys (value: PAD send-keys text), click (x, y relative to the
window), wait (seconds). A screenshot is always taken after the last step.

Needs env vars PA_TENANT_ID, PA_CLIENT_ID, PA_CLIENT_SECRET, PA_FLOW_URL.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

FLOW_SCOPE = "https://service.flow.microsoft.com//.default"


def get_token(token_url, client_id, client_secret):
    form = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": FLOW_SCOPE,
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(token_url, data=form)) as r:
        return json.load(r)["access_token"]


def _send(req):
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def call_flow(flow_url, token, payload, timeout=900, poll_interval=5):
    """POST payload; if the flow answers 202 + Location, poll until it finishes."""
    auth = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(flow_url, data=json.dumps(payload).encode(),
                                 headers={**auth, "Content-Type": "application/json"})
    status, headers, body = _send(req)
    deadline = time.monotonic() + timeout
    while status == 202 and headers.get("Location"):
        if time.monotonic() > deadline:
            raise TimeoutError(f"flow still running after {timeout}s")
        time.sleep(int(headers.get("Retry-After", poll_interval)))
        status, headers, body = _send(urllib.request.Request(headers["Location"], headers=auth))
    if status != 200:
        raise RuntimeError(f"flow returned HTTP {status}: {body.decode(errors='replace')[:2000]}")
    return json.loads(body)


def save_screenshot(result, out_dir):
    """Replace the base64 screenshot in result with the path of a saved .jpg."""
    b64 = result.pop("screenshot", None)
    if b64:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, time.strftime("shot-%Y%m%d-%H%M%S.jpg"))
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        result["screenshot_path"] = path
    return result


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    payload = json.loads(sys.stdin.read() if sys.argv[1] == "-" else sys.argv[1])
    env = os.environ
    token = get_token(f"https://login.microsoftonline.com/{env['PA_TENANT_ID']}/oauth2/v2.0/token",
                      env["PA_CLIENT_ID"], env["PA_CLIENT_SECRET"])
    result = call_flow(env["PA_FLOW_URL"], token, payload)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    print(json.dumps(save_screenshot(result, out_dir), indent=2))


if __name__ == "__main__":
    main()
