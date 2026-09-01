"""
storage.py — Shared persistence layer for the combined INFINI app (7000 + 8046 + 8032).

Replaces:
  - local JSON files (e.g. Path("data/xxx.json")) -> Neon Postgres (table: app_state)
  - local file uploads (e.g. uploads/xxx.png)      -> Cloudinary

Usage in existing code:

    # OLD:
    STATE = DATA / "point_card_system.json"
    data = json.loads(STATE.read_text())
    STATE.write_text(json.dumps(data))

    # NEW:
    import storage
    data = storage.get_json("point_card_system", default={})
    storage.set_json("point_card_system", data)

    # OLD:
    dest = UPLOADS / filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    url = f"/uploads/{filename}"

    # NEW:
    import storage
    url = await storage.upload_file(file, folder="point_cards")

Environment variables required (set these in Render's dashboard, never commit real values):
    NEON_DATABASE_URL   e.g. postgresql://user:pass@ep-xxxx.neon.tech/dbname?sslmode=require
    CLOUDINARY_URL      e.g. cloudinary://<api_key>:<api_secret>@<cloud_name>
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import psycopg2
import psycopg2.extras

# The cloudinary SDK validates os.environ["CLOUDINARY_URL"] the moment it's
# imported, and raises an unhandled ValueError (crashing the whole process)
# if the value doesn't start with "cloudinary://". We check it ourselves
# FIRST so a bad/misconfigured env var produces a clear log message and a
# disabled-but-alive app, instead of a hard crash loop.
_raw_cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
_cloudinary_url_valid = _raw_cloudinary_url.strip().startswith("cloudinary://")
if _raw_cloudinary_url and not _cloudinary_url_valid:
    print(
        f"[storage] CLOUDINARY_URL is set but malformed (must start with "
        f"'cloudinary://'). Got: {_raw_cloudinary_url[:20]!r}... "
        f"Disabling Cloudinary for this run so the app can still start.",
        flush=True,
    )
    # Temporarily hide it from the SDK's own auto-config-on-import so
    # `import cloudinary` below doesn't crash the whole process.
    os.environ.pop("CLOUDINARY_URL", None)

import cloudinary
import cloudinary.uploader
import cloudinary.api

# ---------------------------------------------------------------------------
# Postgres (Neon) — JSON state store
# ---------------------------------------------------------------------------

_DB_URL = os.getenv("NEON_DATABASE_URL")

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_state (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _get_conn():
    if not _DB_URL:
        raise RuntimeError(
            "NEON_DATABASE_URL is not set. Add it as an environment variable "
            "in Render (or your local .env) before calling storage.get_json/set_json."
        )
    return psycopg2.connect(_DB_URL)


def init_db() -> None:
    """Call once at startup to make sure the app_state table exists."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_TABLE_SQL)
        conn.commit()


def get_json(key: str, default: Any = None) -> Any:
    """Fetch a JSON blob by key. Returns `default` if the key doesn't exist yet."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM app_state WHERE key = %s", (key,))
            row = cur.fetchone()
            if row is None:
                return default
            return row[0]


def set_json(key: str, value: Any) -> None:
    """Upsert a JSON blob by key."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_state (key, value, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = now()
                """,
                (key, psycopg2.extras.Json(value)),
            )
        conn.commit()


def delete_json(key: str) -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM app_state WHERE key = %s", (key,))
        conn.commit()


def list_keys(prefix: str = "") -> list[str]:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT key FROM app_state WHERE key LIKE %s", (f"{prefix}%",))
            return [r[0] for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Cloudinary — file uploads
# ---------------------------------------------------------------------------

_CLOUDINARY_URL = _raw_cloudinary_url if _cloudinary_url_valid else None
if _CLOUDINARY_URL:
    # The cloudinary SDK auto-configures from the CLOUDINARY_URL env var,
    # but we call config() explicitly so failures surface early and clearly.
    cloudinary.config(cloudinary_url=_CLOUDINARY_URL, secure=True)


def current_cloud_name() -> Optional[str]:
    """Return the cloud_name Cloudinary is currently configured with, or
    None if CLOUDINARY_URL isn't set/valid. Used to detect when someone
    switches to a different Cloudinary account between deploys."""
    cfg = cloudinary.config()
    return getattr(cfg, "cloud_name", None) or None


def check_cloudinary_credentials() -> bool:
    """
    Call this once at startup. Verifies the CLOUDINARY_URL actually works
    by pinging Cloudinary's API, and prints a clear diagnostic instead of
    letting every single upload fail silently with 'Invalid Signature'.
    """
    cfg = cloudinary.config()
    cloud_name = getattr(cfg, "cloud_name", None)
    api_key = getattr(cfg, "api_key", None)

    if not cloud_name or not api_key:
        if _raw_cloudinary_url and not _cloudinary_url_valid:
            print(
                "[storage] CLOUDINARY_URL is set but malformed — it must start "
                "with 'cloudinary://'. Re-copy the full value from Cloudinary's "
                "API Keys page and re-paste it into Render's environment variable.",
                flush=True,
            )
        else:
            print(
                "[storage] CLOUDINARY_URL is missing or could not be parsed "
                "(no cloud_name/api_key found). Check the env var in Render.",
                flush=True,
            )
        return False

    print(f"[storage] Cloudinary configured for cloud_name='{cloud_name}', "
          f"api_key='{api_key[:4]}...{api_key[-2:]}' — verifying credentials...", flush=True)

    try:
        cloudinary.api.ping()
        print("[storage] Cloudinary credentials OK (ping succeeded)", flush=True)
        return True
    except Exception as e:
        print(
            f"[storage] Cloudinary credentials REJECTED: {e}\n"
            f"[storage] -> Go to Cloudinary Dashboard > API Keys, copy the FULL "
            f"CLOUDINARY_URL value again (watch for extra spaces/newlines), "
            f"and re-paste it into Render's environment variable.",
            flush=True,
        )
        return False


async def upload_file(file, folder: str = "misc", public_id: Optional[str] = None) -> str:
    """
    Upload a FastAPI UploadFile (or any file-like object with .read()) to Cloudinary.
    Returns the public HTTPS URL of the uploaded asset.
    """
    if not _CLOUDINARY_URL:
        raise RuntimeError(
            "CLOUDINARY_URL is not set. Add it as an environment variable "
            "in Render (or your local .env) before calling storage.upload_file."
        )

    content = await file.read()
    result = cloudinary.uploader.upload(
        content,
        folder=folder,
        public_id=public_id,
        resource_type="auto",  # handles images and videos
        overwrite=True,
    )
    return result["secure_url"]


def upload_bytes(data: bytes, folder: str = "misc", public_id: Optional[str] = None,
                  resource_type: str = "auto") -> str:
    """Synchronous variant for raw bytes (e.g. generated QR codes)."""
    if not _CLOUDINARY_URL:
        raise RuntimeError("CLOUDINARY_URL is not set.")
    result = cloudinary.uploader.upload(
        data,
        folder=folder,
        public_id=public_id,
        resource_type=resource_type,
        overwrite=True,
    )
    return result["secure_url"]
