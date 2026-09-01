from __future__ import annotations
from pathlib import Path
from typing import Any
import json, os, time

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
MEMORY_DB = DATA / "memory.json"
CONFIG_DB = DATA / "config.json"


def _read(path: Path, default: Any):
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj
    except Exception:
        return default


def _write(path: Path, obj: Any):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    try: os.chmod(path, 0o600)
    except Exception: pass


def get_config() -> dict[str, Any]:
    d = _read(CONFIG_DB, {})
    return d if isinstance(d, dict) else {}


def save_config(patch: dict[str, Any]) -> dict[str, Any]:
    d = get_config()
    for k, v in patch.items():
        if v is not None:
            d[k] = v
    d["updated_at"] = int(time.time())
    _write(CONFIG_DB, d)
    return d


def _default_memory() -> dict[str, Any]:
    return {
        "trader": {},
        "account": {},
        "trade_rules": {},
        "aliases": {},
        "history": [],
        "updated_at": int(time.time()),
    }


def get_memory(memory_key: str) -> dict[str, Any]:
    db = _read(MEMORY_DB, {"items": {}})
    items = db.get("items") if isinstance(db, dict) else {}
    if not isinstance(items, dict): items = {}
    item = items.get(memory_key)
    return item if isinstance(item, dict) else _default_memory()


def update_memory(memory_key: str, patch: dict[str, Any]) -> dict[str, Any]:
    db = _read(MEMORY_DB, {"items": {}})
    if not isinstance(db, dict): db = {"items": {}}
    items = db.setdefault("items", {})
    if not isinstance(items, dict): items = {}; db["items"] = items
    cur = items.get(memory_key)
    if not isinstance(cur, dict): cur = _default_memory()
    for section in ("trader", "account", "trade_rules", "aliases"):
        val = patch.get(section)
        if isinstance(val, dict):
            old = cur.get(section) if isinstance(cur.get(section), dict) else {}
            old.update(val)
            cur[section] = old
    if isinstance(patch.get("history_append"), dict):
        h = cur.get("history") if isinstance(cur.get("history"), list) else []
        h.append(patch["history_append"])
        cur["history"] = h[-200:]
    cur["updated_at"] = int(time.time())
    items[memory_key] = cur
    _write(MEMORY_DB, db)
    return cur
