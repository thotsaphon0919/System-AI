"""
INFINI Knowledge base.

Two tiers, kept in separate files on purpose:
  - SYSTEM knowledge: shared, read-only to normal users, seeded/managed
    by the platform itself (e.g. how INFINI features work). Always
    eligible to be searched.
  - OWNER knowledge: each user's own entries about their own business/
    products/policies — private by default, but the owner can flip
    individual entries to "public" so visitors browsing their public
    pages (poster, etc.) can have those specific facts used to answer
    questions, without exposing everything else.

Search is a simple keyword-overlap ranker (title/category matches count
extra) — good enough to surface relevant entries without needing an
embeddings pipeline/external vector DB for this pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re
import time
import uuid

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
SYSTEM_KB_FILE = DATA / "knowledge_system.json"     # [entry, entry, ...]
OWNER_KB_DIR = DATA / "knowledge_owners"
OWNER_KB_DIR.mkdir(parents=True, exist_ok=True)


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(s or ""))[:100] or "owner"


def _owner_kb_path(owner_id: str) -> Path:
    return OWNER_KB_DIR / f"{_safe(owner_id)}.json"


def _load_list(path: Path) -> list[dict]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save_list(path: Path, items: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _tokenize(text: str) -> list[str]:
    # Thai has no spaces between words, so naive whole-run tokenizing
    # would treat "ต้นทุนเสื้อยืดตัวละ" as one indivisible token — a
    # search for "ต้นทุนเสื้อยืด" would then never exact-match it even
    # though it's clearly the right entry. Splitting on non-alphanumeric
    # separators (spaces, punctuation) still gives us query "words" to
    # test, but matching happens via substring containment below rather
    # than exact set equality, which works for Thai compounds too.
    return [t for t in re.split(r"[^a-zA-Z0-9ก-๙]+", (text or "").lower()) if t]


def _score(entry: dict, query_terms: list[str]) -> int:
    title = (entry.get("title") or "").lower()
    body = (entry.get("content") or "").lower()
    cat = (entry.get("category") or "").lower()
    score = 0
    for term in query_terms:
        if not term:
            continue
        if term in title:
            score += 3
        if term in cat:
            score += 2
        if term in body:
            score += 1
    return score


def search_knowledge(owner_id: str | None, query: str, *, include_owner_private: bool, limit: int = 5) -> list[dict]:
    """
    Reusable by any other module (AI chat, STAR TRAND, voice, etc.) —
    not just the HTTP endpoint below. `include_owner_private=True` only
    when the requester IS the owner (or an authenticated internal call
    acting on the owner's behalf); visitors/public callers must pass
    False so private entries never leak into answers shown to them.
    """
    q_terms = _tokenize(query)
    if not q_terms:
        return []

    candidates: list[dict] = []
    for e in _load_list(SYSTEM_KB_FILE):
        e = dict(e)
        e["source"] = "system"
        candidates.append(e)

    if owner_id:
        for e in _load_list(_owner_kb_path(owner_id)):
            if not include_owner_private and e.get("visibility") != "public":
                continue
            e = dict(e)
            e["source"] = "owner"
            candidates.append(e)

    scored = [(_score(e, q_terms), e) for e in candidates]
    scored = [(s, e) for s, e in scored if s > 0]
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:limit]]


def install_knowledge_7000(app):
    if getattr(app.state, "_knowledge_v1", False):
        return
    app.state._knowledge_v1 = True

    def _uid(request: Request) -> str | None:
        try:
            from id_entry_7000 import _current_user_id
            return _current_user_id(request)
        except Exception:
            return None

    @app.get("/api/knowledge")
    async def list_knowledge(request: Request, category: str = ""):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        items = _load_list(_owner_kb_path(me))
        if category:
            items = [i for i in items if i.get("category") == category]
        return JSONResponse({"ok": True, "items": items})

    @app.post("/api/knowledge")
    async def add_knowledge(request: Request):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        p = await request.json()
        title = str(p.get("title") or "").strip()[:200]
        content = str(p.get("content") or "").strip()[:8000]
        category = str(p.get("category") or "ทั่วไป").strip()[:80]
        visibility = str(p.get("visibility") or "private").strip()
        if visibility not in ("private", "public"):
            visibility = "private"
        if not title or not content:
            return JSONResponse({"ok": False, "error": "ต้องมีหัวข้อและเนื้อหา"}, status_code=400)

        items = _load_list(_owner_kb_path(me))
        entry = {
            "id": uuid.uuid4().hex[:12],
            "title": title,
            "content": content,
            "category": category,
            "visibility": visibility,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }
        items.append(entry)
        _save_list(_owner_kb_path(me), items)
        return JSONResponse({"ok": True, "item": entry})

    @app.patch("/api/knowledge/{entry_id}")
    async def edit_knowledge(request: Request, entry_id: str):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        p = await request.json()
        items = _load_list(_owner_kb_path(me))
        entry = next((i for i in items if i.get("id") == entry_id), None)
        if not entry:
            return JSONResponse({"ok": False, "error": "ไม่พบข้อมูลนี้"}, status_code=404)
        for k in ("title", "content", "category"):
            if k in p:
                entry[k] = str(p[k]).strip()
        if "visibility" in p and p["visibility"] in ("private", "public"):
            entry["visibility"] = p["visibility"]
        entry["updated_at"] = int(time.time())
        _save_list(_owner_kb_path(me), items)
        return JSONResponse({"ok": True, "item": entry})

    @app.delete("/api/knowledge/{entry_id}")
    async def delete_knowledge(request: Request, entry_id: str):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        items = _load_list(_owner_kb_path(me))
        items = [i for i in items if i.get("id") != entry_id]
        _save_list(_owner_kb_path(me), items)
        return JSONResponse({"ok": True})

    @app.get("/api/knowledge/search")
    async def search(request: Request, q: str, owner_id: str = "", public_only: bool = False):
        """
        Used by AI features to pull relevant facts. `owner_id` scopes the
        search to one owner's knowledge (plus system knowledge); omit it
        to search system knowledge only. `public_only=true` must be set
        by any caller answering a VISITOR (not the owner) so private
        entries never leak — e.g. the public poster page's AI widget.
        """
        me = _uid(request)
        include_private = bool(owner_id) and (me == owner_id) and not public_only
        results = search_knowledge(owner_id or None, q, include_owner_private=include_private)
        return JSONResponse({"ok": True, "results": results})
