"""
backup_sync.py — Generic, endpoint-agnostic durability layer.

Runs alongside the 3 apps and periodically:
  1. Scans the 7000/ and 8046/ folders for JSON state files and media
     files (images/videos), and backs up anything new/changed to
     Neon (JSON content) and Cloudinary (media files) — WITHOUT needing
     to modify any of the ~25 individual upload routes in main.py and
     friends. It works purely at the filesystem level.
  2. On startup, restores everything from the last backup BEFORE the
     three apps launch, so a fresh Render disk (after every redeploy or
     restart) comes back with all previously uploaded content intact.

This is intentionally decoupled from the app code: it's a safety net,
not a replacement for the apps' own read/write logic. The apps keep
reading and writing local files exactly as they always have; this
script just makes sure those local files survive a redeploy.
"""

from __future__ import annotations

import hashlib
import json
import time
import threading
from pathlib import Path

import httpx

import storage

ROOT = Path(__file__).parent
APPS = ["7000", "8046", "8032", "star_trand_service"]

MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov"}
EXCLUDE_MARKERS = (
    "before_", ".safe_", ".bak", "__pycache__", "backup_before",
    "node_modules",
)

MANIFEST_KEY = "backup_manifest_v1"


def _iter_candidate_files():
    for app in APPS:
        base = ROOT / app
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = str(p.relative_to(ROOT))
            if any(m in rel for m in EXCLUDE_MARKERS):
                continue
            if p.suffix.lower() in MEDIA_EXT or p.suffix.lower() == ".json":
                yield p, rel


def _file_hash(p: Path) -> str:
    h = hashlib.sha1()
    h.update(p.read_bytes())
    return h.hexdigest()


CLOUD_ACCOUNT_MARKER_KEY = "backup_cloudinary_account_v1"


def _reset_media_manifest_if_cloudinary_account_changed(manifest: dict) -> dict:
    """
    The manifest remembers each file's hash -> {kind, url, ...} so unchanged
    files are never re-uploaded. That's efficient, but it breaks silently if
    someone switches to a DIFFERENT Cloudinary account: files that were
    already uploaded to the OLD account still "match" by hash, so they get
    skipped forever — even though their stored url now points at an account
    that's disabled/gone. This checks the currently configured cloud_name
    against the last one we backed up to; if it changed, every "media" kind
    manifest entry is dropped (JSON entries are untouched, Neon doesn't
    care about Cloudinary accounts) so the next cycle re-uploads all media
    fresh to the new account.
    """
    current = None
    try:
        current = storage.current_cloud_name()
    except Exception:
        pass
    if not current:
        return manifest  # Cloudinary not configured/working — nothing to compare

    try:
        marker = storage.get_json(CLOUD_ACCOUNT_MARKER_KEY, default={}) or {}
    except Exception:
        marker = {}
    last = marker.get("cloud_name")

    if last == current:
        return manifest  # same account as last time — no action needed

    media_count = sum(1 for v in manifest.values() if isinstance(v, dict) and v.get("kind") == "media")
    if last is not None and media_count:
        print(
            f"[backup_sync] Cloudinary account changed ({last!r} -> {current!r}) — "
            f"clearing {media_count} cached media backup record(s) so they "
            f"re-upload to the new account on the next cycle(s)",
            flush=True,
        )
        manifest = {k: v for k, v in manifest.items()
                    if not (isinstance(v, dict) and v.get("kind") == "media")}

    try:
        storage.set_json(CLOUD_ACCOUNT_MARKER_KEY, {"cloud_name": current, "updated_at": time.time()})
    except Exception as e:
        print(f"[backup_sync] could not save cloud account marker: {e}", flush=True)

    return manifest


def backup_once() -> int:
    """Scan for new/changed files and push them to Neon/Cloudinary. Returns count changed."""
    manifest = storage.get_json(MANIFEST_KEY, default={})
    manifest = _reset_media_manifest_if_cloudinary_account_changed(manifest)
    changed = 0

    for p, rel in _iter_candidate_files():
        try:
            digest = _file_hash(p)
        except Exception:
            continue

        prev = manifest.get(rel)
        if prev and prev.get("hash") == digest:
            continue  # unchanged since last backup, skip

        if p.suffix.lower() == ".json":
            try:
                content = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue  # skip unparseable/incomplete json rather than crash
            try:
                storage.set_json(f"jsonfile:{rel}", content)
            except Exception as e:
                # Don't let one failed write (e.g. a transient Neon hiccup)
                # abort the whole cycle — the rest of the files (including
                # other JSON state and media) still deserve a chance to
                # back up. This file will simply be retried next cycle.
                print(f"[backup_sync] failed to back up {rel} to Neon: {e}", flush=True)
                continue
            manifest[rel] = {"hash": digest, "kind": "json"}
        else:
            try:
                url = storage.upload_bytes(
                    p.read_bytes(),
                    folder="infini-backup/" + str(Path(rel).parent).replace("\\", "/"),
                    public_id=Path(rel).stem,
                )
            except Exception as e:
                print(f"[backup_sync] failed to upload {rel}: {e}", flush=True)
                continue
            manifest[rel] = {"hash": digest, "kind": "media", "url": url}

        changed += 1

    if changed:
        try:
            storage.set_json(MANIFEST_KEY, manifest)
            print(f"[backup_sync] backed up {changed} changed file(s)", flush=True)
        except Exception as e:
            print(f"[backup_sync] backed up {changed} file(s) but failed to save manifest index: {e} "
                  f"(these files will be re-uploaded next cycle, which is harmless)", flush=True)

    return changed


def restore_once() -> int:
    """Pull the last backup down into local disk. Call this BEFORE the apps start."""
    manifest = storage.get_json(MANIFEST_KEY, default={})
    if not manifest:
        print("[backup_sync] no previous backup found in Neon, starting fresh", flush=True)
        return 0

    restored = 0
    with httpx.Client(timeout=30.0) as client:
        for rel, meta in manifest.items():
            dest = ROOT / rel
            if dest.exists():
                try:
                    if _file_hash(dest) == meta.get("hash"):
                        continue  # already correct (e.g. came in via git-lfs), skip
                except Exception:
                    pass

            dest.parent.mkdir(parents=True, exist_ok=True)

            if meta.get("kind") == "json":
                content = storage.get_json(f"jsonfile:{rel}")
                if content is not None:
                    dest.write_text(
                        json.dumps(content, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    restored += 1
            else:
                url = meta.get("url")
                if not url:
                    continue
                try:
                    r = client.get(url)
                    r.raise_for_status()
                    dest.write_bytes(r.content)
                    restored += 1
                except Exception as e:
                    print(f"[backup_sync] failed to restore {rel}: {e}", flush=True)

    print(f"[backup_sync] restored {restored} file(s) from previous backup", flush=True)
    return restored


def backup_file_now(rel_path: str) -> bool:
    """
    Immediately back up ONE specific file (by path relative to ROOT), without
    waiting for the next periodic scan. Use this right after writing a file
    whose loss would actually hurt (e.g. users.json right after a new
    registration) — the 10-minute periodic loop is fine for everything else,
    but new-user data shouldn't have to wait up to 10 minutes to be safe.
    """
    p = ROOT / rel_path
    if not p.exists() or not p.is_file():
        return False
    try:
        digest = _file_hash(p)
        manifest = storage.get_json(MANIFEST_KEY, default={})
        if p.suffix.lower() == ".json":
            content = json.loads(p.read_text(encoding="utf-8"))
            storage.set_json(f"jsonfile:{rel_path}", content)
            manifest[rel_path] = {"hash": digest, "kind": "json"}
        else:
            url = storage.upload_bytes(
                p.read_bytes(),
                folder="infini-backup/" + str(Path(rel_path).parent).replace("\\", "/"),
                public_id=Path(rel_path).stem,
            )
            manifest[rel_path] = {"hash": digest, "kind": "media", "url": url}
        storage.set_json(MANIFEST_KEY, manifest)
        return True
    except Exception as e:
        print(f"[backup_sync] immediate backup of {rel_path} failed: {e}", flush=True)
        return False


def backup_loop(interval_seconds: int = 600):
    while True:
        try:
            backup_once()
        except Exception as e:
            print(f"[backup_sync] backup cycle error: {e}", flush=True)
        time.sleep(interval_seconds)


def start_background_backup(interval_seconds: int = 600) -> threading.Thread:
    t = threading.Thread(target=backup_loop, args=(interval_seconds,), daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_once()
    else:
        backup_once()
