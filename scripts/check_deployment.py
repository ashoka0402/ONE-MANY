"""Read-only check of a deployed ONE / MANY website and its FastAPI API.

Never creates accounts, sends payments, or consumes Gemini/Channel3 credits.
Run: python scripts/check_deployment.py --web-url https://... --api-url https://...
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def origin(raw: str) -> str:
    parts = urlsplit(raw.rstrip("/"))
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("Supply an http(s) site origin")
    if parts.username or parts.password or parts.path not in ("", "/") or parts.query:
        raise ValueError("Supply an origin only, without credentials or a path")
    return raw.rstrip("/")


def fetch(url: str, *, method: str = "GET", headers: dict | None = None):
    request = Request(url, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=12) as response:
            return response.status, dict(response.headers.items()), response.read(10000)
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read(10000)


def verify(web: str, api: str) -> None:
    web, api = origin(web), origin(api)
    for path in ("/", "/app"):
        code, _, body = fetch(web + path)
        if code != 200 or b"ONE" not in body:
            raise RuntimeError(f"Frontend {path} failed (HTTP {code})")
        print(f"OK web {path}: HTTP {code}")

    code, headers, body = fetch(api + "/api/v1/health")
    if code != 200 or json.loads(body).get("status") != "ok":
        raise RuntimeError(f"API health failed (HTTP {code})")
    print("OK API liveness")

    code, _, body = fetch(api + "/api/v1/ready")
    if code != 200 or json.loads(body).get("status") != "ready":
        raise RuntimeError(f"API database readiness failed (HTTP {code})")
    print("OK database and migration readiness")

    code, _, _ = fetch(api + "/api/v1/auth/me")
    if code != 401:
        raise RuntimeError(f"Protected member endpoint did not reject anonymous traffic ({code})")
    print("OK authenticated endpoint is protected")

    code, headers, _ = fetch(
        api + "/api/v1/funding/groups/00000000-0000-4000-8000-000000000000/reservation",
        method="OPTIONS",
        headers={
            "Origin": web,
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    normalized = {key.lower(): value for key, value in headers.items()}
    if code != 200 or normalized.get("access-control-allow-origin") != web:
        raise RuntimeError(f"CORS reservation preflight failed (HTTP {code})")
    if "PUT" not in normalized.get("access-control-allow-methods", ""):
        raise RuntimeError("CORS does not allow calendar reservation writes")
    print("OK authenticated reservation CORS preflight")
    print("All read-only deployment checks passed. Real provider checkout remains unverified.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-url", required=True, help="Deployed Next.js origin")
    parser.add_argument("--api-url", required=True, help="Deployed FastAPI origin")
    args = parser.parse_args()
    try:
        verify(args.web_url, args.api_url)
    except (ValueError, URLError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"Deployment check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
