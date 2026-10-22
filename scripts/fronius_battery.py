#!/usr/bin/env python3
"""Read/write Fronius GEN24 battery config via the local web API.

  fronius_battery.py get
  fronius_battery.py set '{"HYB_EM_POWER": 2400}'
"""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HOST = "192.168.178.85"
USER = "customer"
PATH = "/api/config/batteries"
SECRETS = os.path.join(os.path.dirname(__file__), "..", "secrets.yaml")


def password():
    with open(SECRETS) as f:
        m = re.search(r'^fronius_password:\s*["\']?(.*?)["\']?\s*$', f.read(), re.M)
    if not m:
        sys.exit("fronius_password missing from secrets.yaml")
    return m.group(1)


def request(method, body=None, auth=None):
    req = urllib.request.Request(f"http://{HOST}{PATH}", data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if auth:
        req.add_header("Authorization", auth)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode()


def digest_header(method, challenge, pwd, ha1_algo):
    # Fronius sends the challenge in X-WWW-Authenticate so browsers don't pop a login dialog
    p = dict(re.findall(r'(\w+)="?([^",]+)"?', challenge))
    h = lambda s, a="sha256": hashlib.new(a, s.encode()).hexdigest()
    nc, cnonce = "00000001", os.urandom(8).hex()
    ha1 = h(f"{USER}:{p['realm']}:{pwd}", ha1_algo)
    ha2 = h(f"{method}:{PATH}")
    resp = h(f"{ha1}:{p['nonce']}:{nc}:{cnonce}:{p['qop']}:{ha2}")
    return (f'Digest username="{USER}", realm="{p["realm"]}", nonce="{p["nonce"]}", '
            f'uri="{PATH}", algorithm={p.get("algorithm", "SHA256")}, qop={p["qop"]}, '
            f'nc={nc}, cnonce="{cnonce}", response="{resp}"')


def call(method, body=None):
    pwd = password()
    # Some firmwares still hash HA1 with MD5 despite advertising SHA256
    for ha1_algo in ("sha256", "md5"):
        status, headers, _ = request(method, body)
        challenge = headers.get("X-WWW-Authenticate") or headers.get("WWW-Authenticate")
        if status != 401 or not challenge:
            break
        status, headers, text = request(method, body, digest_header(method, challenge, pwd, ha1_algo))
        if status != 401:
            return status, text
    return status, "authentication failed"


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("get", "set"):
        sys.exit(__doc__)
    if sys.argv[1] == "get":
        status, text = call("GET")
    else:
        status, text = call("POST", json.dumps(json.loads(sys.argv[2])).encode())
    print(text)
    sys.exit(0 if status == 200 else 1)
