"""
proxy.py — Public front door for the combined INFINI service.

Render only exposes ONE public port per web service (given via the $PORT
env var). This tiny ASGI app listens on that port and reverse-proxies to
the three original apps, which run as internal subprocesses started by
start.py on their original internal ports (7000, 8046, 8032) — not
reachable from the internet directly, only through this proxy.

Routing:
    /8046/*   -> http://127.0.0.1:8046/*   (ad market / reward / QR card app)
    /8032/*   -> http://127.0.0.1:8032/*   (commerce suite app)
    /*        -> http://127.0.0.1:7000/*   (main app — default / fallback)

Because the prefix is stripped before forwarding, each backend app still
sees requests exactly as if it were running standalone at its own root,
so its server-side logic ("/uploads/..." style paths it reads/writes on
disk, etc.) needs no changes.

However, the HTML each backend RETURNS to the browser typically contains
root-relative links like href="/login" or src="/static/x.png". The browser
resolves those against whatever URL is in its address bar — if the user is
looking at "/8032/login" and clicks something with href="/login", the
browser will navigate to "/login" (the root, i.e. the DEFAULT/7000 app),
not "/8032/login". To keep navigation and asset loading correct for a
proxied sub-app, this proxy rewrites:
  - the `Location` header on redirect responses, and
  - href="/...", src="/...", action="/..." attributes inside HTML bodies
so they stay prefixed with "/8046" or "/8032" as appropriate. Paths that
already start with a known prefix, or are absolute (http.../https...) or
protocol-relative (//...), are left untouched.
"""

from __future__ import annotations

import re

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.routing import Route

BACKENDS = {
    "8046": "http://127.0.0.1:8046",
    "8032": "http://127.0.0.1:8032",
}
DEFAULT_BACKEND = "http://127.0.0.1:7000"

_client = httpx.AsyncClient(timeout=60.0)

_ATTR_RE = re.compile(rb'(href|src|action)=("|\')(/[^"\']*)')
_KNOWN_PREFIXES = tuple(f"/{k}".encode() for k in BACKENDS)

# Deliberate cross-app jumps (e.g. the 8032 -> 7000 post-login auth bridge)
# generate a root-relative redirect on purpose and must NOT be re-prefixed
# back into the sub-app they're leaving.
_ROOT_ESCAPE_PREFIXES = ("/auth/bridge",)


def _rewrite_location(location: str, prefix: str) -> str:
    if not location.startswith("/") or location.startswith("//"):
        return location  # absolute or protocol-relative URL — leave alone
    if any(location.startswith(f"/{k}") for k in BACKENDS):
        return location  # already prefixed
    if any(location.startswith(p) for p in _ROOT_ESCAPE_PREFIXES):
        return location  # intentional jump to the default (7000) app
    return f"/{prefix}{location}"


def _rewrite_html(body: bytes, prefix: str) -> bytes:
    prefix_bytes = f"/{prefix}".encode()

    def repl(m: "re.Match[bytes]") -> bytes:
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        if path.startswith(_KNOWN_PREFIXES):
            return m.group(0)
        return attr + b"=" + quote + prefix_bytes + path

    return _ATTR_RE.sub(repl, body)


async def _proxy(request: Request):
    path = request.url.path
    prefix = None
    for key, base in BACKENDS.items():
        if path == f"/{key}" or path.startswith(f"/{key}/"):
            prefix = key
            base_url = base
            break
    else:
        base_url = DEFAULT_BACKEND

    forward_path = path
    if prefix:
        forward_path = path[len(f"/{prefix}"):] or "/"

    url = base_url + forward_path
    if request.url.query:
        url += f"?{request.url.query}"

    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    req = _client.build_request(
        request.method, url, headers=headers, content=body,
    )
    resp = await _client.send(req, stream=True)

    resp_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in ("content-length", "transfer-encoding", "connection")
    }
    content_type = resp.headers.get("content-type", "")

    if prefix and 300 <= resp.status_code < 400 and "location" in resp_headers:
        resp_headers["location"] = _rewrite_location(resp_headers["location"], prefix)

    if prefix and content_type.startswith("text/html"):
        # Small HTML pages only — buffer fully so we can rewrite links.
        raw = await resp.aread()
        await resp.aclose()
        rewritten = _rewrite_html(raw, prefix)
        resp_headers["content-length"] = str(len(rewritten))
        return StreamingResponse(
            iter([rewritten]),
            status_code=resp.status_code,
            headers=resp_headers,
            media_type=content_type,
        )

    async def stream():
        async for chunk in resp.aiter_raw():
            yield chunk
        await resp.aclose()

    return StreamingResponse(
        stream(),
        status_code=resp.status_code,
        headers=resp_headers,
        media_type=resp.headers.get("content-type"),
    )


app = Starlette(routes=[Route("/{path:path}", _proxy, methods=[
    "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD",
])])
