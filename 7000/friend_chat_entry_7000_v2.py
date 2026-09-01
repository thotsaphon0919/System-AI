from __future__ import annotations

from fastapi import UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from pathlib import Path
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from itsdangerous import BadSignature, URLSafeSerializer
from typing import Any
import json
import os
import shutil
import time
import uuid

MARKER = "INFINI_FRIEND_CHAT_PER_USER_V3"

BASE_DIR = Path(__file__).resolve().parent
INFINI_8032_ROOT = Path(
    os.getenv("INFINI_8032_ROOT", str(BASE_DIR.parent / "8032"))
).expanduser().resolve()
USERS_FILE = Path(
    os.getenv("INFINI_USERS_FILE", str(INFINI_8032_ROOT / "data" / "users.json"))
).expanduser().resolve()
SESSION_SECRET_FILE = Path(
    os.getenv(
        "INFINI_SESSION_SECRET_FILE",
        str(INFINI_8032_ROOT / "data" / "infini_session_secret.txt"),
    )
).expanduser().resolve()
LOGIN_URL = os.getenv("INFINI_LOGIN_URL", "/8032/login")

INJECT = r"""
<!-- INFINI_FRIEND_CHAT_PER_USER_V3 -->
<style>
#infini-friend-entry{position:relative;min-height:150px;margin-top:14px;border:1.5px solid rgba(255,145,0,.65);border-radius:25px;overflow:hidden;background:linear-gradient(90deg,rgba(0,0,0,.92),rgba(0,0,0,.28)),url('/friend-chat/card-image?v=4') center/cover,radial-gradient(circle at right,#512000,#080402 68%);box-shadow:0 15px 38px rgba(0,0,0,.42);cursor:pointer;touch-action:manipulation}
#infini-friend-entry:active{transform:scale(.988)}
.ifc-copy{position:relative;z-index:2;padding:23px 70px 23px 20px;color:#fff}.ifc-kicker{color:#ff9d2d;font-size:12px;font-weight:950;letter-spacing:1.2px}.ifc-title{margin-top:4px;font-size:26px;font-weight:1000}.ifc-sub{margin-top:6px;color:#ffd09a;font-size:13px}.ifc-open{display:inline-flex;margin-top:11px;padding:6px 10px;border:1px solid rgba(255,181,69,.45);border-radius:999px;color:#ffd18a;background:rgba(255,145,0,.10);font-size:11px;font-weight:900}#ifc-upload{position:absolute;top:12px;right:12px;z-index:5;width:45px;height:45px;border:1px solid rgba(255,181,69,.72);border-radius:999px;background:rgba(0,0,0,.75);color:#ffd18a;font-size:20px;font-weight:950}
</style>
<script>
(function(){
 if(window.__IFC_V3__)return;window.__IFC_V3__=true;
 const clean=v=>String(v||"").replace(/\s+/g," ").trim().toUpperCase();
 function label(n){return [...document.querySelectorAll("body *")].find(e=>!e.children.length&&clean(e.textContent)==="ZONE "+n)||null}
 function card(e){if(!e)return null;return e.closest("a,button,[role='link'],[role='button'],.zone-card,.zoneCard,.zone,.card,.tile")||e.parentElement}
 function parent(cards){let n=cards[0]&&cards[0].parentElement;while(n&&n!==document.body){if(cards.every(c=>n.contains(c)))return n;n=n.parentElement}return null}
 function add(){
  if(document.getElementById("infini-friend-entry"))return true;
  const cards=[1,2,3,4].map(label).map(card).filter(Boolean);if(cards.length<4)return false;
  const holder=parent(cards);if(!holder||!holder.parentElement)return false;
  const box=document.createElement("div");box.id="infini-friend-entry";box.tabIndex=0;box.setAttribute("role","link");
  box.innerHTML='<div class="ifc-copy"><div class="ifc-kicker">CONNECTION</div><div class="ifc-title">FRIEND / CHAT</div><div class="ifc-sub">เพื่อนของแต่ละบัญชีแยกกัน</div><div class="ifc-open">กดเพื่อเปิด</div></div><button id="ifc-upload" type="button">⇧</button><input id="ifc-file" type="file" accept="image/jpeg,image/png,image/webp" hidden>';
  holder.insertAdjacentElement("afterend",box);box.onclick=e=>{if(!e.target.closest("#ifc-upload"))location.href="/friend-chat"};box.onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();location.href="/friend-chat"}};
  const b=box.querySelector("#ifc-upload"),f=box.querySelector("#ifc-file");b.onclick=e=>{e.preventDefault();e.stopPropagation();f.click()};f.onchange=async()=>{const x=f.files&&f.files[0];if(!x)return;const d=new FormData();d.append("file",x);b.textContent="…";const r=await fetch("/friend-chat/card-upload",{method:"POST",body:d});if(r.ok)location.reload();else{b.textContent="!";alert("อัปโหลดไม่สำเร็จ")}};return true;
 }
 function start(){if(add())return;let i=0,t=setInterval(()=>{i++;if(add()||i>14)clearInterval(t)},300)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",start):start();
})();
</script>
"""


class FriendChatMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "text/html" not in response.headers.get("content-type", "").lower():
            return response
        path = request.url.path
        allowed = (
            path == "/id-home" or path.startswith("/id-home/")
            or path == "/id" or path.startswith("/id/")
            or path == "/member/id" or path.startswith("/member/id/")
        )
        if not allowed:
            return response
        iterator = getattr(response, "body_iterator", None)
        if iterator is None:
            return response
        chunks = []
        async for chunk in iterator:
            chunks.append(chunk)
        raw = b"".join(chunks)
        try:
            page_html = raw.decode("utf-8")
        except UnicodeDecodeError:
            return Response(raw, status_code=response.status_code, headers=dict(response.headers), media_type="text/html")
        if MARKER not in page_html:
            page_html = page_html.replace("</body>", INJECT + "\n</body>", 1) if "</body>" in page_html else page_html + INJECT
        headers = dict(response.headers)
        headers.pop("content-length", None)
        headers.pop("content-encoding", None)
        return Response(page_html, status_code=response.status_code, headers=headers, media_type="text/html")


class FriendRequestIn(BaseModel):
    target: str = ""


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load_users() -> dict[str, dict]:
    raw = _read_json(USERS_FILE, {})
    return raw if isinstance(raw, dict) else {}


def _session_signer() -> URLSafeSerializer | None:
    try:
        secret = SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        secret = os.getenv("INFINI_SESSION_SECRET", "").strip()
    if not secret:
        return None
    return URLSafeSerializer(secret, salt="infini-session")


def _current_user_id(request: Request) -> str | None:
    signer = _session_signer()
    token = request.cookies.get("infini_session")
    if not signer or not token:
        return None
    try:
        payload = signer.loads(token)
    except BadSignature:
        return None
    user_id = str((payload or {}).get("user_id") or "").strip()
    return user_id if user_id in _load_users() else None


def _require_user_id(request: Request) -> str:
    user_id = _current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบผ่าน INFINI")
    return user_id


def _derived_infini_id(user_id: str) -> str:
    raw = str(user_id).removeprefix("user_").replace("-", "").replace("_", "")
    return "INF-" + (raw[:8] or "00000001").upper()


def _member(user_id: str) -> dict[str, str]:
    raw = _load_users().get(user_id, {})
    username = str(raw.get("username") or raw.get("name") or "INFINI MEMBER").strip()
    infini_id = str(raw.get("infini_id") or _derived_infini_id(user_id)).strip()
    return {
        "user_id": user_id,
        "name": username,
        "username": username,
        "infini_id": infini_id,
        "public_url": f"/id-hub/member/{user_id}",
    }


def _resolve_target(query: str) -> str | None:
    q = str(query or "").strip().casefold()
    if not q:
        return None
    matches = []
    for key, raw in _load_users().items():
        if not isinstance(raw, dict):
            continue
        user_id = str(raw.get("id") or (key if str(key).startswith("user_") else "")).strip()
        if not user_id:
            continue
        m = _member(user_id)
        values = {user_id.casefold(), m["name"].casefold(), m["username"].casefold(), m["infini_id"].casefold()}
        if q in values:
            matches.append(user_id)
    return matches[0] if len(matches) == 1 else None


def install_friend_chat_entry_7000(app):
    base = Path(__file__).resolve().parent
    data_dir = base / "data" / "friend_chat_entry"
    card_root = data_dir / "cards"
    request_file = data_dir / "friend_requests.json"
    card_root.mkdir(parents=True, exist_ok=True)

    def load_store() -> dict:
        raw = _read_json(request_file, {"version": 3, "requests": []})
        if not isinstance(raw, dict):
            raw = {"version": 3, "requests": []}
        rows = raw.get("requests") if isinstance(raw.get("requests"), list) else []
        valid = [r for r in rows if isinstance(r, dict) and r.get("from_user_id") and r.get("to_user_id")]
        # V2 stored one global list without account IDs. Keep a backup and reset it,
        # otherwise every newly registered member appears to share the same friends.
        if len(valid) != len(rows):
            if request_file.exists() and rows:
                backup = request_file.with_name(f"friend_requests.global_legacy_{int(time.time())}.json")
                if not backup.exists():
                    shutil.copy2(request_file, backup)
            raw = {"version": 3, "requests": valid}
            _write_json(request_file, raw)
        raw["version"] = 3
        raw["requests"] = valid
        return raw

    def save_store(data: dict) -> dict:
        data["version"] = 3
        data["requests"] = list(data.get("requests") or [])[-1000:]
        _write_json(request_file, data)
        return data

    def card_dir(user_id: str) -> Path:
        safe = "".join(ch for ch in user_id if ch.isalnum() or ch in "-_")[:80] or "member"
        path = card_root / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def latest(user_id: str):
        files = [p for p in card_dir(user_id).iterdir() if p.is_file()]
        return max(files, key=lambda p: p.stat().st_mtime) if files else None

    def view_for(user_id: str) -> dict:
        data = load_store()
        friends = []
        received = []
        sent = []
        seen = set()
        for row in data["requests"]:
            from_id = str(row.get("from_user_id") or "")
            to_id = str(row.get("to_user_id") or "")
            status = str(row.get("status") or "pending")
            if user_id not in {from_id, to_id}:
                continue
            if status == "accepted":
                other = to_id if from_id == user_id else from_id
                if other and other not in seen:
                    friends.append(_member(other))
                    seen.add(other)
            elif status == "pending" and to_id == user_id:
                m = _member(from_id)
                m["request_id"] = str(row.get("id") or "")
                received.append(m)
            elif status == "pending" and from_id == user_id:
                m = _member(to_id)
                m["request_id"] = str(row.get("id") or "")
                sent.append(m)
        return {
            "ok": True,
            "current_user": _member(user_id),
            "friends": friends,
            "pending_received": received,
            "pending_sent": sent,
        }

    @app.get("/friend-chat", response_class=HTMLResponse)
    def friend_chat(request: Request):
        if not _current_user_id(request):
            return RedirectResponse(LOGIN_URL, status_code=303)
        return HTMLResponse(r'''<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>FRIEND / CHAT</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}body{margin:0;min-height:100vh;padding:14px;background:radial-gradient(circle at top right,#321500,#080402 44%,#000);color:#fff;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}.wrap{max-width:900px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.brand{color:#ff9d2d;font-size:20px;font-weight:1000}.back{padding:10px 14px;border:1px solid rgba(255,154,20,.5);border-radius:14px;background:#080402;color:#ffd09a;text-decoration:none;font-weight:900}.cover{position:relative;min-height:175px;margin-bottom:14px;border:1px solid rgba(255,145,0,.48);border-radius:25px;overflow:hidden;background:linear-gradient(90deg,rgba(0,0,0,.92),rgba(0,0,0,.28)),url('/friend-chat/card-image?v=4') center/cover,radial-gradient(circle at right,#5a2400,#080402 65%)}.copy{padding:27px 70px 27px 21px}.copy h1{margin:0;font-size:32px}.copy p{margin:7px 0 0;color:#ffd09a}.upload{position:absolute;top:12px;right:12px}.upload label{width:46px;height:46px;display:grid;place-items:center;border:1px solid rgba(255,181,69,.7);border-radius:999px;background:rgba(0,0,0,.76);color:#ffd18a;font-size:20px;font-weight:950}.upload input{display:none}.friendActions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}.actionBtn{min-height:52px;border:1px solid rgba(255,159,45,.58);border-radius:17px;background:#100805;color:#ffd09a;font:inherit;font-weight:950}.actionBtn.primary{background:linear-gradient(135deg,#ffb22f,#ff7b00);color:#1a0800}.requestPanel{display:none;margin-bottom:14px;padding:10px;border:1px solid rgba(255,145,0,.35);border-radius:20px;background:rgba(12,6,3,.82)}.requestPanel.show{display:block}.requestRow{display:flex;align-items:center;justify-content:space-between;gap:9px;padding:10px;border-bottom:1px solid rgba(255,145,0,.18)}.requestRow:last-child{border-bottom:0}.requestName{font-weight:900;overflow-wrap:anywhere}.requestMeta{font-size:11px;color:#a88e78;margin-top:3px}.acceptBtn{border:1px solid rgba(255,181,69,.65);border-radius:13px;background:#ff9820;color:#190900;padding:9px 11px;font-weight:950}.layout{display:grid;grid-template-columns:minmax(116px,32%) 1fr;gap:10px}.panel{min-width:0;border:1px solid rgba(255,145,0,.35);border-radius:21px;overflow:hidden;background:rgba(12,6,3,.82)}.head{padding:13px;border-bottom:1px solid rgba(255,145,0,.24);color:#ffac48;font-size:12px;font-weight:950}.list{min-height:290px;padding:9px}.empty{min-height:270px;display:grid;place-items:center;padding:10px;color:#a88e78;text-align:center;font-size:12px;line-height:1.5}.friendItem{display:block;padding:11px;border:1px solid rgba(255,145,0,.22);border-radius:14px;margin-bottom:8px;background:rgba(255,145,0,.06);font-weight:900;color:#fff;text-decoration:none;user-select:none}.friendItem:active{transform:scale(.985);background:rgba(255,145,0,.13)}.friendId{display:block;margin-top:3px;color:#a88e78;font-size:10px;font-weight:700}.search{padding:9px;border-bottom:1px solid rgba(255,145,0,.2)}.search input{width:100%;padding:11px;border:1px solid rgba(255,145,0,.34);border-radius:13px;background:#080402;color:#fff;outline:none}.note{margin-top:12px;padding:12px;border:1px dashed rgba(255,145,0,.3);border-radius:15px;color:#a88e78;font-size:12px;line-height:1.5}.toast{position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:99;display:none;padding:10px 14px;border:1px solid rgba(255,145,0,.5);border-radius:999px;background:#170a03;color:#ffd09a;font-weight:900}.toast.show{display:block}@media(max-width:420px){.layout{grid-template-columns:118px minmax(0,1fr)}.friendActions{grid-template-columns:1fr}}
</style></head><body><div class="toast" id="toast"></div><div class="wrap">
<div class="top"><div class="brand">FRIEND / CHAT</div><a class="back" href="/id-home">กลับ</a></div>
<div class="cover"><form class="upload" method="post" action="/friend-chat/card-upload" enctype="multipart/form-data"><label for="fc">⇧</label><input id="fc" type="file" name="file" accept="image/jpeg,image/png,image/webp" onchange="this.form.submit()"></form><div class="copy"><h1>เพื่อนและแชท</h1><p id="accountName">กำลังโหลดบัญชี...</p></div></div>
<div class="friendActions"><button class="actionBtn primary" id="requestFriendBtn">ขอเป็นเพื่อน</button><button class="actionBtn" id="openRequestsBtn">เปิดคำขอเป็นเพื่อน</button></div>
<div class="requestPanel" id="requestPanel"></div>
<div class="layout"><section class="panel"><div class="head">ข้อความใหม่</div><div class="list"><div class="empty">ยังไม่มีข้อความจากแผ่น</div></div></section><section class="panel"><div class="head">เพื่อนของฉัน</div><div class="search"><input id="friendSearch" type="search" placeholder="ค้นหาชื่อเพื่อน"></div><div class="list" id="friendsList"></div></section></div>
<div class="note">รายชื่อเพื่อนแยกตาม INFINI ID แล้ว กดชื่อเพื่อนเพื่อเปิดหน้า Public ID ได้ทันที แม้อีกฝ่ายออฟไลน์</div>
</div><script>
const $=id=>document.getElementById(id);function toast(message){const t=$("toast");t.textContent=message;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),1900)}async function api(url,opt={}){const res=await fetch(url,{headers:{"Content-Type":"application/json",...(opt.headers||{})},...opt});const data=await res.json().catch(()=>({}));if(!res.ok)throw new Error(data.detail||data.error||"ทำรายการไม่สำเร็จ");return data}
async function requestFriend(){const target=(prompt("พิมพ์ชื่อ Username หรือเลข INFINI ID ของคนที่ต้องการขอเป็นเพื่อน","")||"").trim();if(!target)return;const data=await api("/friend-chat/api/request",{method:"POST",body:JSON.stringify({target})});toast(data.message||"ส่งคำขอแล้ว");await loadAll()}
function friendRows(friends){const list=$("friendsList");list.innerHTML="";if(!friends.length){list.innerHTML='<div class="empty">ยังไม่มีเพื่อนในบัญชีนี้</div>';return}friends.forEach(friend=>{const row=document.createElement("a");row.className="friendItem";row.href=friend.public_url;row.textContent=friend.name||"เพื่อน";const id=document.createElement("span");id.className="friendId";id.textContent=friend.infini_id||"";row.appendChild(id);list.appendChild(row)});filterFriends()}
function filterFriends(){const q=($("friendSearch").value||"").trim().toLowerCase();document.querySelectorAll(".friendItem").forEach(el=>{el.style.display=!q||el.textContent.toLowerCase().includes(q)?"block":"none"})}
async function acceptRequest(id){const data=await api("/friend-chat/api/requests/"+encodeURIComponent(id)+"/accept",{method:"POST"});toast(data.message||"รับเป็นเพื่อนแล้ว");await loadAll()}
function pendingRows(rows){const panel=$("requestPanel");panel.innerHTML="";if(!rows.length){panel.innerHTML='<div class="requestRow"><div class="requestName">ยังไม่มีคำขอเป็นเพื่อนของบัญชีนี้</div></div>';return}rows.forEach(friend=>{const row=document.createElement("div");row.className="requestRow";const wrap=document.createElement("div");const name=document.createElement("div");name.className="requestName";name.textContent=friend.name||"สมาชิก";const meta=document.createElement("div");meta.className="requestMeta";meta.textContent=friend.infini_id||"";wrap.append(name,meta);const accept=document.createElement("button");accept.className="acceptBtn";accept.textContent="รับเป็นเพื่อน";accept.onclick=()=>acceptRequest(friend.request_id).catch(e=>toast(e.message));row.append(wrap,accept);panel.appendChild(row)})}
async function loadAll(){const data=await api("/friend-chat/api/requests");const me=data.current_user||{};$("accountName").textContent=(me.name||"INFINI MEMBER")+" · "+(me.infini_id||"");friendRows(data.friends||[]);pendingRows(data.pending_received||[]);$("openRequestsBtn").textContent=(data.pending_received||[]).length?"คำขอเป็นเพื่อน ("+(data.pending_received||[]).length+")":"เปิดคำขอเป็นเพื่อน";$("requestFriendBtn").textContent="ขอเป็นเพื่อน"}
$("requestFriendBtn").onclick=()=>requestFriend().catch(e=>toast(e.message));$("openRequestsBtn").onclick=()=>{$("requestPanel").classList.toggle("show");if($("requestPanel").classList.contains("show"))loadAll().catch(e=>toast(e.message))};$("friendSearch").oninput=filterFriends;loadAll().catch(e=>toast(e.message));
</script></body></html>''')

    @app.post("/friend-chat/card-upload")
    async def upload_card(request: Request, file: UploadFile = File(...)):
        user_id = _require_user_id(request)
        ext = Path(file.filename or "").suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(400, "รองรับเฉพาะ JPG PNG WEBP")
        raw = await file.read()
        if not raw or len(raw) > 15 * 1024 * 1024:
            raise HTTPException(400, "รูปต้องไม่เกิน 15 MB")
        target_dir = card_dir(user_id)
        for old in target_dir.iterdir():
            if old.is_file():
                try: old.unlink()
                except Exception: pass
        (target_dir / f"friend_chat_{int(time.time())}{ext}").write_bytes(raw)
        return RedirectResponse("/friend-chat", status_code=303)

    @app.get("/friend-chat/card-image")
    def card_image(request: Request):
        user_id = _require_user_id(request)
        target = latest(user_id)
        if target is None:
            return Response(status_code=404)
        return FileResponse(target, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})

    @app.get("/friend-chat/api/requests")
    def get_friend_requests(request: Request):
        return JSONResponse(view_for(_require_user_id(request)))

    @app.post("/friend-chat/api/request")
    def create_friend_request(request: Request, payload: FriendRequestIn):
        from_user_id = _require_user_id(request)
        to_user_id = _resolve_target(payload.target)
        if not to_user_id:
            raise HTTPException(404, "ไม่พบสมาชิกจากชื่อหรือ INFINI ID นี้")
        if to_user_id == from_user_id:
            raise HTTPException(400, "ไม่สามารถขอเป็นเพื่อนกับบัญชีตัวเองได้")
        data = load_store()
        pair = [r for r in data["requests"] if {str(r.get("from_user_id")), str(r.get("to_user_id"))} == {from_user_id, to_user_id}]
        accepted = next((r for r in pair if r.get("status") == "accepted"), None)
        if accepted:
            return JSONResponse({"ok": True, "status": "accepted", "message": "เป็นเพื่อนกันอยู่แล้ว"})
        incoming = next((r for r in pair if r.get("status") == "pending" and r.get("to_user_id") == from_user_id), None)
        if incoming:
            return JSONResponse({"ok": True, "status": "incoming", "message": "อีกฝ่ายส่งคำขอมาแล้ว เปิดคำขอเพื่อรับเป็นเพื่อน"})
        outgoing = next((r for r in pair if r.get("status") == "pending" and r.get("from_user_id") == from_user_id), None)
        if outgoing:
            return JSONResponse({"ok": True, "status": "pending", "message": "ส่งคำขอไปแล้ว กำลังรออีกฝ่ายรับ"})
        current = int(time.time())
        row = {"id": "friend_" + uuid.uuid4().hex[:12], "from_user_id": from_user_id, "to_user_id": to_user_id, "status": "pending", "created_at": current, "updated_at": current}
        data["requests"].append(row)
        save_store(data)
        return JSONResponse({"ok": True, "status": "pending", "message": "ส่งคำขอเป็นเพื่อนแล้ว"})

    @app.post("/friend-chat/api/requests/{request_id}/accept")
    def accept_friend_request(request: Request, request_id: str):
        current_user_id = _require_user_id(request)
        data = load_store()
        row = next((r for r in data["requests"] if r.get("id") == request_id), None)
        if row is None:
            raise HTTPException(404, "ไม่พบคำขอเป็นเพื่อน")
        if str(row.get("to_user_id")) != current_user_id:
            raise HTTPException(403, "บัญชีนี้ไม่มีสิทธิ์รับคำขอนี้")
        row["status"] = "accepted"
        row["updated_at"] = int(time.time())
        save_store(data)
        return JSONResponse({"ok": True, "message": "รับเป็นเพื่อนแล้ว"})

    marker = "_friend_chat_per_user_v3_installed"
    if not getattr(app.state, marker, False):
        app.add_middleware(FriendChatMiddleware)
        setattr(app.state, marker, True)
