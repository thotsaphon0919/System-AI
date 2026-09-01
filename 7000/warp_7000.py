"""
INFINI Warp — connect sheets/pages, within one ID or across different IDs.

Design constraints straight from the spec:
  - Owner of the SOURCE page decides where their warp points.
  - Same-ID warp (to your own other pages) is always allowed.
  - Cross-ID warp is only allowed into something the TARGET has actually
    marked shareable — either their public poster page ("/p/...", already
    gated by clean_final_completion_v1.py's own visibility check) or a
    path they've explicitly added to their own allowlist. This is the
    "มีสิทธิ์" (only with permission) requirement: linking to someone
    else's private zone/room without their consent is not allowed.
  - If the destination isn't real (target ID doesn't exist, or isn't on
    the target's allowlist), resolution fails with a clear reason —
    it never silently guesses or redirects somewhere close-enough.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
WARPS_FILE = DATA / "warps.json"          # {owner_user_id: {warp_id: {...}}}
ALLOWLIST_FILE = DATA / "warp_allowlist.json"  # {user_id: [path, path, ...]}


def _load(path: Path, default):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, type(default)) else default
    except Exception:
        return default


def _save(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _users_index() -> dict[str, dict]:
    """Look up real registered users (by user_id OR username) so a warp
    target can be checked against reality instead of trusted blindly."""
    for p in [
        Path(__file__).resolve().parent.parent / "8032" / "data" / "users.json",
    ]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
        except Exception:
            continue
    return {}


def _resolve_target_user_id(target: str) -> str | None:
    target = (target or "").strip()
    if not target:
        return None
    users = _users_index()
    if target in users:
        return target
    for uid_, u in users.items():
        if str(u.get("username", "")).lower() == target.lower():
            return uid_
        if str(u.get("infini_id", "")).lower() == target.lower():
            return uid_
    return None


def _is_cross_id_path_allowed(target_user_id: str, path: str) -> bool:
    if path.startswith("/p/"):
        return True  # already gated by its own public/draft visibility check
    allow = _load(ALLOWLIST_FILE, {})
    return path in (allow.get(target_user_id) or [])


WARP_UI = r'''
<div id="infini-warp-box" style="border:1px solid rgba(255,174,25,.3);border-radius:16px;padding:14px;margin:14px 0;background:#0b0806">
  <b style="color:#ff9a2f;font-size:12px;letter-spacing:.08em">WARP · เชื่อมแผ่น</b>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
    <input id="warpTargetId" placeholder="ID ปลายทาง (ว่าง = แผ่นของฉันเอง)" style="border:1px solid #4a2a18;border-radius:10px;background:#040404;color:#fff;padding:9px;font:inherit">
    <input id="warpTargetPath" placeholder="เช่น /zone/private" style="border:1px solid #4a2a18;border-radius:10px;background:#040404;color:#fff;padding:9px;font:inherit">
  </div>
  <div style="display:flex;gap:8px;margin-top:8px">
    <button id="warpSaveBtn" type="button" style="flex:1;border:1px solid #754018;border-radius:10px;background:#080808;color:#ffc17d;font-weight:800;padding:9px">บันทึกปลายทาง Warp</button>
    <button id="warpGoBtn" type="button" style="flex:1;border:0;border-radius:10px;background:#ff941f;color:#140700;font-weight:900;padding:9px">🌀 Warp ไปเลย</button>
  </div>
  <div id="warpStatus" style="font-size:11px;color:#999;margin-top:6px;min-height:16px"></div>
</div>
<script>
(function(){
  const $=x=>document.getElementById(x);
  const sheetKey = location.pathname;
  async function loadWarp(){
    try{
      const d=await fetch('/api/warp/get?sheet='+encodeURIComponent(sheetKey)).then(r=>r.json());
      if(d.ok && d.warp){$('warpTargetId').value=d.warp.target_id||'';$('warpTargetPath').value=d.warp.target_path||''}
    }catch(e){}
  }
  $('warpSaveBtn')?.addEventListener('click', async ()=>{
    const body={sheet:sheetKey,target_id:$('warpTargetId').value.trim(),target_path:$('warpTargetPath').value.trim()};
    const d=await fetch('/api/warp/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json());
    $('warpStatus').textContent = d.ok ? 'บันทึกแล้ว' : (d.error||'บันทึกไม่สำเร็จ');
  });
  $('warpGoBtn')?.addEventListener('click', async ()=>{
    $('warpStatus').textContent='กำลังตรวจสอบปลายทาง...';
    try{
      const d=await fetch('/api/warp/go?sheet='+encodeURIComponent(sheetKey)).then(r=>r.json());
      if(d.ok){ sessionStorage.setItem('infini_warp_back', location.href); location.href=d.url; }
      else { $('warpStatus').textContent = d.error || 'ปลายทางนี้ไม่มีจริงหรือไม่มีสิทธิ์เข้า'; }
    }catch(e){ $('warpStatus').textContent='เกิดข้อผิดพลาด'; }
  });
  window.infiniWarpBack = function(){
    const back = sessionStorage.getItem('infini_warp_back');
    if(back){ location.href = back; } else { history.back(); }
  };
  loadWarp();
})();
</script>
'''


def install_warp_7000(app):
    if getattr(app.state, "_warp_v1", False):
        return
    app.state._warp_v1 = True

    def _uid(request: Request) -> str | None:
        try:
            from id_entry_7000 import _current_user_id
            return _current_user_id(request)
        except Exception:
            return None

    @app.get("/api/warp/get")
    async def warp_get(request: Request, sheet: str):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        all_warps = _load(WARPS_FILE, {})
        mine = all_warps.get(me, {})
        warp = next((w for w in mine.values() if w.get("source_sheet") == sheet), None)
        return JSONResponse({"ok": True, "warp": warp})

    @app.post("/api/warp/set")
    async def warp_set(request: Request):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        p = await request.json()
        source_sheet = str(p.get("sheet") or "").strip()
        target_id = str(p.get("target_id") or "").strip()
        target_path = str(p.get("target_path") or "").strip()
        if not source_sheet or not target_path:
            return JSONResponse({"ok": False, "error": "ต้องมีปลายทาง (path)"}, status_code=400)
        if not target_path.startswith("/"):
            target_path = "/" + target_path

        all_warps = _load(WARPS_FILE, {})
        mine = all_warps.setdefault(me, {})
        existing = next((wid for wid, w in mine.items() if w.get("source_sheet") == source_sheet), None)
        warp_id = existing or uuid.uuid4().hex[:12]
        mine[warp_id] = {
            "id": warp_id,
            "source_sheet": source_sheet,
            "target_id": target_id,  # empty = same ID (me)
            "target_path": target_path,
            "updated_at": int(time.time()),
        }
        _save(WARPS_FILE, all_warps)
        return JSONResponse({"ok": True, "warp": mine[warp_id]})

    @app.get("/api/warp/go")
    async def warp_go(request: Request, sheet: str):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)

        all_warps = _load(WARPS_FILE, {})
        mine = all_warps.get(me, {})
        warp = next((w for w in mine.values() if w.get("source_sheet") == sheet), None)
        if not warp:
            return JSONResponse({"ok": False, "error": "ยังไม่ได้ตั้งปลายทาง Warp สำหรับแผ่นนี้"}, status_code=404)

        target_id = str(warp.get("target_id") or "").strip()
        target_path = str(warp.get("target_path") or "").strip()

        if not target_id:
            # Same-ID warp: always allowed, just go.
            return JSONResponse({"ok": True, "url": target_path})

        real_target_id = _resolve_target_user_id(target_id)
        if not real_target_id:
            return JSONResponse({"ok": False, "error": f"ไม่พบ ID ปลายทาง '{target_id}' จริงในระบบ"}, status_code=404)

        if not _is_cross_id_path_allowed(real_target_id, target_path):
            return JSONResponse(
                {"ok": False, "error": "ปลายทางนี้เจ้าของยังไม่เปิดให้ warp เข้าถึงจากภายนอก"},
                status_code=403,
            )

        return JSONResponse({"ok": True, "url": target_path})

    @app.get("/api/warp/allowlist")
    async def get_allowlist(request: Request):
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        allow = _load(ALLOWLIST_FILE, {})
        return JSONResponse({"ok": True, "paths": allow.get(me) or []})

    @app.post("/api/warp/allowlist")
    async def set_allowlist(request: Request):
        """Let a user opt specific pages of THEIRS into being valid
        cross-ID warp targets for others — the target-side half of the
        permission check in warp_go()."""
        me = _uid(request)
        if not me:
            return JSONResponse({"ok": False}, status_code=401)
        p = await request.json()
        path = str(p.get("path") or "").strip()
        action = str(p.get("action") or "add").strip()
        if not path.startswith("/"):
            path = "/" + path
        allow = _load(ALLOWLIST_FILE, {})
        lst = allow.setdefault(me, [])
        if action == "remove":
            allow[me] = [x for x in lst if x != path]
        elif path not in lst:
            lst.append(path)
        _save(ALLOWLIST_FILE, allow)
        return JSONResponse({"ok": True, "paths": allow.get(me) or []})
