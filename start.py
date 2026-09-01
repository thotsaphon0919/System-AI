"""
start.py — Single entry point for Render's Start Command.

Launches the three original apps as background subprocesses on their
internal ports (7000, 8046, 8032), waits for them to come up, then runs
the public proxy in the foreground on Render's assigned $PORT.

If any backend process dies, this script exits non-zero so Render
recognizes the deploy as unhealthy and restarts the service.
"""

import os
import signal
import subprocess
import sys
import time

import httpx

import backup_sync
import storage

ROOT = os.path.dirname(os.path.abspath(__file__))

BACKENDS = [
    # (name, directory, port, uvicorn app module string)
    ("7000", os.path.join(ROOT, "7000"), 7000, "main:app"),
    ("8046", os.path.join(ROOT, "8046"), 8046, "main:app"),
    ("8032", os.path.join(ROOT, "8032"), 8032, "main:app"),
    # ^ re-enabled: commerce_suite_8032.py, remote_sheet.py, member_system.py,
    #   remote_sheet_tools.py, templates/, and data/ have been restored from
    #   INFINI_8032_DEPLOY_READY.zip, so 8032 can run again.
    ("star_trand", os.path.join(ROOT, "star_trand_service"), 7050, "app:app"),
    # ^ INFINI STAR TRAND: separate AI trading-assistant service (Mission
    #   Control + 7 analysis Heads + 8 trading-style agents). Called
    #   in-process over localhost by star_trand_bridge_7000.py inside the
    #   7000 app — never exposed on the public proxy, decision-support
    #   only, never places real orders. Optional: if this fails to start,
    #   the bridge in 7000 degrades gracefully and says "STAR TRAND offline"
    #   rather than breaking voice commands, so it's still listed here
    #   (not skipped) to keep behavior consistent with the other backends.
]

processes = []


def start_backend(name: str, cwd: str, port: int, app_module: str = "main:app") -> subprocess.Popen:
    print(f"[start.py] launching {name} on internal port {port} ...", flush=True)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app_module,
         "--host", "127.0.0.1", "--port", str(port)],
        cwd=cwd,
    )


def wait_healthy(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/", timeout=2.0)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def shutdown(*_):
    print("[start.py] shutting down backends ...", flush=True)
    for p in processes:
        p.terminate()
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        print("[start.py] initializing Neon database (create app_state table if missing) ...", flush=True)
        storage.init_db()
    except Exception as e:
        print(f"[start.py] WARNING: could not init Neon DB, storage/backup will fail: {e}", flush=True)

    cloudinary_ok = False
    try:
        cloudinary_ok = storage.check_cloudinary_credentials()
    except Exception as e:
        print(f"[start.py] WARNING: could not verify Cloudinary credentials: {e}", flush=True)

    try:
        print("[start.py] restoring previous data from Neon/Cloudinary (if any) ...", flush=True)
        backup_sync.restore_once()
    except Exception as e:
        # Never let a restore failure block the app from starting — worst
        # case we start with whatever's already on disk (e.g. from git-lfs).
        print(f"[start.py] restore skipped/failed (continuing anyway): {e}", flush=True)

    for name, cwd, port, app_module in BACKENDS:
        processes.append(start_backend(name, cwd, port, app_module))

    for name, _, port, _ in BACKENDS:
        healthy = wait_healthy(port)
        if not healthy and name == "star_trand":
            # Optional service — voice commands still work without it,
            # the bridge just reports "STAR TRAND offline". Don't take
            # the whole deploy down over it.
            print(f"[start.py] WARNING: star_trand did not come up on port {port} — "
                  f"voice/trading assistant will report offline, everything else still works", flush=True)
            continue
        if not healthy:
            print(f"[start.py] ERROR: {name} did not become healthy on port {port}", flush=True)
            shutdown()

    try:
        # Always start the periodic backup loop, even if Cloudinary is
        # currently broken. Reasoning: this loop backs up TWO independent
        # things — JSON state (users.json, etc.) to Neon, and media files
        # (images/videos) to Cloudinary. Each file is backed up in its own
        # try/except inside backup_sync.backup_once(), so a Cloudinary
        # failure only skips that one media file and logs it — it does NOT
        # stop JSON files from being backed up to Neon. Gating the entire
        # loop on cloudinary_ok was a bug: it silently stopped users.json
        # (and all other JSON state) from being backed up too, even though
        # Neon was working the whole time. That's how registered users
        # were getting lost on redeploy while Cloudinary was down.
        backup_sync.start_background_backup(interval_seconds=600)
        if cloudinary_ok:
            print("[start.py] background backup loop started (every 10min — keeps Neon's free-tier compute scaling to zero between runs so it doesn't burn the monthly CU-hour quota)", flush=True)
        else:
            print("[start.py] background backup loop started (JSON/user data -> Neon only; "
                  "media uploads -> Cloudinary will be SKIPPED per-file and logged until "
                  "CLOUDINARY_URL is fixed in Render — this does not affect user/account data)", flush=True)
    except Exception as e:
        print(f"[start.py] could not start background backup: {e}", flush=True)

    public_port = os.environ.get("PORT", "10000")
    print(f"[start.py] all backends up — starting public proxy on 0.0.0.0:{public_port}", flush=True)

    proxy = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "proxy:app",
         "--host", "0.0.0.0", "--port", public_port],
        cwd=ROOT,
    )
    processes.append(proxy)
    proxy.wait()
    shutdown()


if __name__ == "__main__":
    main()
