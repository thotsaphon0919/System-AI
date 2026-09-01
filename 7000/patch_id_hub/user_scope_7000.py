from __future__ import annotations

from contextvars import ContextVar
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any
import json
import os
import re
import shutil

try:
    from itsdangerous import BadSignature, URLSafeSerializer
except Exception:  # pragma: no cover
    BadSignature = Exception
    URLSafeSerializer = None

_SCOPE_KEY: ContextVar[str] = ContextVar("infini_7000_scope_key", default="guest")
_SCOPE_AUTH: ContextVar[bool] = ContextVar("infini_7000_scope_auth", default=False)
_SCOPE_LOCK = Lock()


def _safe_key(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(value or "").strip())
    return value[:100] or "guest"


def _secret_candidates(base: Path) -> list[str]:
    values: list[str] = []
    env_secret = os.getenv("INFINI_SESSION_SECRET", "").strip()
    if env_secret:
        values.append(env_secret)

    paths = [
        base / "data" / "infini_session_secret.txt",
        base.parent / "data" / "infini_session_secret.txt",
        Path.home() / "downloads" / "data" / "infini_session_secret.txt",
    ]
    for path in paths:
        try:
            secret = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if secret and secret not in values:
            values.append(secret)
    return values


def resolve_request_scope(request: Any, base: Path) -> tuple[str, bool]:
    token = str(request.cookies.get("infini_session") or "").strip()
    if not token:
        return "guest", False

    if URLSafeSerializer is not None:
        for secret in _secret_candidates(base):
            try:
                payload = URLSafeSerializer(secret, salt="infini-session").loads(token)
            except Exception:
                continue
            if isinstance(payload, dict) and payload.get("user_id"):
                return _safe_key(str(payload["user_id"])), True

    # Fallback keeps two different session cookies isolated even if the shared
    # secret cannot be found. Normally the decoded user_id path above is used.
    return "token_" + sha256(token.encode("utf-8")).hexdigest()[:32], True


def install_user_scope_7000(app: Any, base_dir: Path) -> None:
    base = Path(base_dir).resolve()

    @app.middleware("http")
    async def infini_7000_user_scope(request, call_next):
        key, authenticated = resolve_request_scope(request, base)
        key_token = _SCOPE_KEY.set(key)
        auth_token = _SCOPE_AUTH.set(authenticated)
        try:
            response = await call_next(request)
            response.headers["X-INFINI-Space"] = key
            return response
        finally:
            _SCOPE_KEY.reset(key_token)
            _SCOPE_AUTH.reset(auth_token)


def current_user_key() -> str:
    return _safe_key(_SCOPE_KEY.get())


def current_user_authenticated() -> bool:
    return bool(_SCOPE_AUTH.get())


def registry_path(base_dir: Path) -> Path:
    return Path(base_dir).resolve() / "data" / "user_spaces_registry.json"


def load_registry(base_dir: Path) -> dict[str, Any]:
    path = registry_path(base_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("version", 1)
    data.setdefault("owner_key", "")
    return data


def save_registry(base_dir: Path, data: dict[str, Any]) -> dict[str, Any]:
    path = registry_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return data


def user_space_dir(base_dir: Path, key: str | None = None) -> Path:
    base = Path(base_dir).resolve()
    user_key = _safe_key(key or current_user_key())
    path = base / "data" / "user_spaces" / user_key
    path.mkdir(parents=True, exist_ok=True)
    return path


def scoped_data_file(
    base_dir: Path,
    filename: str,
    legacy_path: Path | None = None,
    *,
    key: str | None = None,
) -> Path:
    """Return this request's private data file.

    The configured owner receives a one-time copy of the old shared file.
    Every other INFINI ID starts with a missing file so the caller can create
    a clean default. The old shared file is never deleted.
    """
    base = Path(base_dir).resolve()
    user_key = _safe_key(key or current_user_key())
    target = user_space_dir(base, user_key) / Path(filename).name

    registry = load_registry(base)
    owner_key = _safe_key(registry.get("owner_key")) if registry.get("owner_key") else ""
    legacy = Path(legacy_path).resolve() if legacy_path else base / "data" / Path(filename).name

    if owner_key and user_key == owner_key and not target.exists() and legacy.exists():
        with _SCOPE_LOCK:
            if not target.exists() and legacy.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(legacy, target)
    return target


def scoped_upload_dir(base_dir: Path) -> Path:
    path = Path(base_dir).resolve() / "uploads" / current_user_key()
    path.mkdir(parents=True, exist_ok=True)
    return path


def scoped_upload_url(filename: str) -> str:
    return f"/uploads/{current_user_key()}/{Path(filename).name}"


def scope_debug(base_dir: Path) -> dict[str, Any]:
    registry = load_registry(base_dir)
    return {
        "user_key": current_user_key(),
        "authenticated": current_user_authenticated(),
        "owner_key": registry.get("owner_key", ""),
        "is_owner": current_user_key() == registry.get("owner_key", ""),
        "space_dir": str(user_space_dir(base_dir)),
    }
