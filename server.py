#!/usr/bin/env python3
import base64
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ORDERS = []
USERS = [
    {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"},
    {"id": 2, "name": "Alan Turing", "email": "alan@example.com"},
    {"id": 3, "name": "Grace Hopper", "email": "grace@example.com"},
]
STATS = {"api_requests": 0, "tokens": set()}
LOCK = threading.Lock()


def b64url_decode(value):
    value += "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value.encode())


def read_token(headers):
    header = headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None, "Missing Authorization: Bearer <token>"

    token = token.strip()
    try:
        claims = json.loads(b64url_decode(token.split(".")[1]))
    except Exception:
        return None, "Malformed JWT"

    now = int(time.time())
    if int(claims.get("exp", 0)) <= now:
        return None, "Token expired"
    if "fosite" not in (claims.get("scp") or []):
        return None, "Token is missing the fosite scope"

    return claims, None


def auth_info(claims):
    now = int(time.time())
    return {
        "jti": claims.get("jti"),
        "scope": claims.get("scope") or claims.get("scp"),
        "audience": claims.get("aud"),
        "expires_at": claims.get("exp"),
        "expires_in_seconds": max(0, int(claims.get("exp", 0)) - now),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "oauth-demo-api/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorize(self):
        claims, error = read_token(self.headers)
        if error:
            self.send_json(401, {"error": error})
            return None
        with LOCK:
            STATS["api_requests"] += 1
            STATS["tokens"].add(claims.get("jti"))
        return claims

    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"status": "ok"})

        if self.path == "/stats":
            with LOCK:
                return self.send_json(
                    200,
                    {
                        "api_requests": STATS["api_requests"],
                        "unique_tokens_seen": len(STATS["tokens"]),
                        "orders": len(ORDERS),
                    },
                )

        if self.path == "/token-info":
            claims = self.authorize()
            if claims:
                return self.send_json(200, auth_info(claims))

        if self.path == "/users":
            claims = self.authorize()
            if claims:
                with LOCK:
                    users = list(USERS)
                return self.send_json(200, {"auth": auth_info(claims), "users": users})

        if self.path == "/orders":
            claims = self.authorize()
            if claims:
                return self.send_json(200, {"auth": auth_info(claims), "orders": ORDERS})

        return self.send_json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""

        if self.path == "/reset":
            with LOCK:
                ORDERS.clear()
                STATS["api_requests"] = 0
                STATS["tokens"].clear()
            return self.send_json(200, {"status": "reset"})

        if self.path == "/orders":
            claims = self.authorize()
            if not claims:
                return

            try:
                data = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self.send_json(400, {"error": "Body must be valid JSON"})

            order = {
                "id": str(uuid.uuid4()),
                "item": data.get("item", "coffee"),
                "quantity": int(data.get("quantity", 1)),
                "status": "created",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            with LOCK:
                ORDERS.append(order)
            return self.send_json(201, {"auth": auth_info(claims), "order": order})

        return self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("API listening on :8000", flush=True)
    server.serve_forever()
