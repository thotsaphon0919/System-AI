from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer
from pathlib import Path
from typing import Any
from urllib.parse import quote
import html
import json
import os

BASE_DIR = Path(__file__).resolve().parent
INFINI_8032_ROOT = Path(os.getenv("INFINI_8032_ROOT", str(BASE_DIR.parent / "8032"))).expanduser().resolve()
USERS_FILE = Path(os.getenv("INFINI_USERS_FILE", str(INFINI_8032_ROOT / "data" / "users.json"))).expanduser().resolve()
SESSION_SECRET_FILE = Path(os.getenv("INFINI_SESSION_SECRET_FILE", str(INFINI_8032_ROOT / "data" / "infini_session_secret.txt"))).expanduser().resolve()
ID_STATE_DIR = BASE_DIR / "data" / "id_users"
LOGIN_URL = os.getenv("INFINI_LOGIN_URL", "/8032/login")


def _read_json(path: Path, default: Any) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default


def _load_users() -> dict[str, dict]:
    raw = _read_json(USERS_FILE, {})
    return raw if isinstance(raw, dict) else {}


def _safe_user_id(user_id: str) -> str:
    return "".join(ch for ch in str(user_id) if ch.isalnum() or ch in "-_")[:80] or "member"


def _derived_infini_id(user_id: str) -> str:
    raw = str(user_id).removeprefix("user_").replace("-", "").replace("_", "")
    return "INF-" + (raw[:8] or "00000001").upper()


def _session_signer() -> URLSafeSerializer | None:
    try: secret = SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()
    except Exception: secret = os.getenv("INFINI_SESSION_SECRET", "").strip()
    return URLSafeSerializer(secret, salt="infini-session") if secret else None


def _current_user_id(request: Request) -> str | None:
    signer = _session_signer(); token = request.cookies.get("infini_session")
    if not signer or not token: return None
    try: payload = signer.loads(token)
    except BadSignature: return None
    uid = str((payload or {}).get("user_id") or "").strip()
    return uid if uid in _load_users() else None


def _state_for(user_id: str) -> dict:
    data = _read_json(ID_STATE_DIR / f"{_safe_user_id(user_id)}.json", {})
    return data if isinstance(data, dict) else {}


def _media_obj(value: Any) -> dict[str, str]:
    if not isinstance(value, dict): return {"src": "", "type": ""}
    return {"src": str(value.get("src") or value.get("url") or "").strip(), "type": str(value.get("type") or value.get("media_type") or "").strip()}


def _creative_rooms(state: dict) -> list[dict]:
    rows = state.get("creativeRooms") if isinstance(state.get("creativeRooms"), list) else []
    if not rows:
        rows = [{"id": "room_1", "title": "CREATIVE ROOM 1", "cover": state.get("creativeCover") or {}}]
    out = []
    for i, raw in enumerate(rows, 1):
        if not isinstance(raw, dict): continue
        rid = str(raw.get("id") or f"room_{i}")
        cover = _media_obj(raw.get("cover") or (state.get("creativeCover") if i == 1 else {}))
        gate = _media_obj(raw.get("gate") or (state.get("gate") if i == 1 else {}))
        out.append({"id": rid, "title": str(raw.get("title") or f"CREATIVE ROOM {i}"), "cover": cover, "gate": gate})
    return out or [{"id":"room_1","title":"CREATIVE ROOM 1","cover":_media_obj(state.get("creativeCover")),"gate":_media_obj(state.get("gate"))}]


def _member_record(user_id: str, member: dict) -> dict:
    state = _state_for(user_id)
    username = str(member.get("username") or state.get("username") or "INFINI MEMBER").strip()
    display_name = str(state.get("displayName") or username or "INFINI MEMBER").strip()
    infini_id = str(member.get("infini_id") or state.get("infiniId") or _derived_infini_id(user_id)).strip()
    zones = state.get("zoneCovers") if isinstance(state.get("zoneCovers"), dict) else {}
    rooms = _creative_rooms(state)
    room1 = rooms[0]
    gallery = []
    for item in (state.get("gallery") if isinstance(state.get("gallery"), list) else [])[-18:]:
        media = _media_obj(item)
        if not media["src"]: continue
        media["source_url"] = str(item.get("source_url") or f"/id-hub/member/{quote(user_id)}/creative/{quote(room1['id'])}") if isinstance(item, dict) else f"/id-hub/member/{quote(user_id)}/creative/{quote(room1['id'])}"
        gallery.append(media)
    return {
        "user_id": user_id, "display_name": display_name, "username": username, "infini_id": infini_id,
        "level": str(state.get("level") or "MEMBER"), "bio": str(state.get("bio") or "").strip(),
        "cover": _media_obj(state.get("idCover")), "creative_rooms": rooms,
        "shop_cover": _media_obj(zones.get("shop")), "community_cover": _media_obj(zones.get("showcase") or zones.get("community")),
        "gallery": gallery, "created_at": str(member.get("created_at") or member.get("created") or ""),
    }


def _all_members() -> list[dict]:
    rows=[]
    for idx,(key,member) in enumerate(_load_users().items()):
        if not isinstance(member,dict): continue
        uid=str(member.get("id") or (key if str(key).startswith("user_") else "")).strip()
        if uid: rows.append((idx,_member_record(uid,member)))
    rows.sort(key=lambda x:(x[1].get("created_at") or "9999",x[0]))
    return [r for _,r in rows]


BASE_STYLE = '''<style>:root{--a:#ff8b1f;--line:rgba(255,139,31,.34);--muted:#9b9ba2}*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;background:#000;color:#fff;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}body{background:radial-gradient(circle at 70% 0,rgba(255,120,0,.13),transparent 30%),#000}a{color:inherit;text-decoration:none}.top{position:sticky;top:0;z-index:20;height:62px;display:flex;align-items:center;justify-content:space-between;padding:0 15px;background:rgba(0,0,0,.9);border-bottom:1px solid rgba(255,255,255,.08)}.btn{border:1px solid var(--line);border-radius:999px;padding:9px 13px;color:#ffc78f}.wrap{max-width:820px;margin:auto;padding:16px 14px 110px}.hero{position:relative;min-height:380px;border:1px solid var(--line);border-radius:28px;overflow:hidden;background:#080808}.heroMedia{position:absolute;inset:0}.heroMedia img,.heroMedia video{width:100%;height:100%;object-fit:contain;background:#000}.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.02),rgba(0,0,0,.85))}.identity{position:absolute;left:20px;right:20px;bottom:20px;z-index:2}.ey{color:var(--a);font-size:10px;font-weight:1000;letter-spacing:.12em}.name{font-size:30px;font-weight:1000}.meta{color:#bbb;font-size:12px;margin-top:4px}.bio{color:#aaa;margin-top:8px;line-height:1.45}.section{margin-top:22px}.section h2{font-size:20px}.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}.space{position:relative;min-height:220px;border:1px solid rgba(255,255,255,.13);border-radius:23px;overflow:hidden;background:#0c0c0e}.space.wide{grid-column:1/-1;min-height:250px}.spaceMedia{position:absolute;inset:0}.spaceMedia img,.spaceMedia video{width:100%;height:100%;object-fit:contain;background:#000}.space:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.04),rgba(0,0,0,.83))}.spaceText{position:absolute;z-index:2;left:15px;right:15px;bottom:15px}.spaceText small{color:var(--a);font-weight:1000}.spaceText b{display:block;font-size:20px;margin-top:4px}.placeholder{position:absolute;inset:0;display:grid;place-items:center;color:rgba(255,139,31,.35);font-size:45px}.gallery{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.g{aspect-ratio:4/5;border:1px solid var(--line);border-radius:20px;overflow:hidden;background:#080808}.g img,.g video{width:100%;height:100%;object-fit:contain;background:#000}.none{color:#777;border:1px dashed var(--line);border-radius:18px;padding:23px;text-align:center}@media(min-width:700px){.gallery{grid-template-columns:repeat(3,1fr)}}</style>'''

HUB_HTML = r'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>รวมไอดี · INFINI</title>'''+BASE_STYLE+r'''<style>.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.member{border:1px solid var(--line);border-radius:22px;overflow:hidden;background:#090909}.member .m{aspect-ratio:4/5;background:#000}.member .m img,.member .m video{width:100%;height:100%;object-fit:contain}.member .info{padding:13px}.member b{display:block}.member small{color:#aaa}.search{width:100%;padding:14px;border:1px solid var(--line);border-radius:18px;background:#080808;color:#fff;margin:14px 0}@media(min-width:700px){.grid{grid-template-columns:repeat(3,1fr)}}</style></head><body><header class="top"><b>∞ รวมไอดี</b><a class="btn" href="/id-home">← กลับ</a></header><main class="wrap"><h1>INFINI ID</h1><input class="search" id="search" placeholder="ค้นหาชื่อ หรือ INF-..."><section class="grid" id="grid"></section></main><script>let members=[];function media(m){if(!m||!m.src)return '<div class="placeholder">∞</div>';const v=(m.type||'').startsWith('video')||/\.(mp4|webm|mov)(\?|$)/i.test(m.src);return v?'<video src="'+m.src+'" muted autoplay loop playsinline></video>':'<img src="'+m.src+'">'}function render(){const q=(document.getElementById('search').value||'').toLowerCase();const box=document.getElementById('grid');box.innerHTML='';members.filter(m=>[m.display_name,m.username,m.infini_id].join(' ').toLowerCase().includes(q)).forEach(m=>{const a=document.createElement('a');a.className='member';a.href='/id-hub/member/'+encodeURIComponent(m.user_id);a.innerHTML='<div class="m">'+media(m.cover)+'</div><div class="info"><b></b><small></small></div>';a.querySelector('b').textContent=m.display_name||m.username;a.querySelector('small').textContent=m.infini_id||'';box.appendChild(a)})}fetch('/api/id-hub/members').then(r=>r.json()).then(d=>{members=d.members||[];render()});document.getElementById('search').oninput=render</script></body></html>'''

PUBLIC_HTML = r'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>INFINI Public ID</title>'''+BASE_STYLE+r'''</head><body><header class="top"><b>∞ PUBLIC ID</b><a class="btn" href="/id-hub">← รวมไอดี</a></header><main class="wrap"><section class="hero"><div class="heroMedia" id="heroMedia"></div><div class="shade"></div><div class="identity"><div class="ey">INFINI DIGITAL SPACE</div><div class="name" id="name">กำลังโหลด...</div><div class="meta" id="meta"></div><div class="bio" id="bio"></div></div></section><section class="section"><h2>พื้นที่สาธารณะ</h2><div class="cards" id="spaces"></div></section><section class="section"><h2>ผลงานล่าสุด</h2><div class="gallery" id="gallery"></div><div class="none" id="none" style="display:none">ยังไม่มีผลงานสาธารณะ</div></section></main><script>const USER_ID=__USER_ID_JSON__;function addMedia(box,m){if(!m||!m.src){box.innerHTML='<div class="placeholder">∞</div>';return}const v=(m.type||'').startsWith('video')||/\.(mp4|webm|mov)(\?|$)/i.test(m.src);const el=document.createElement(v?'video':'img');el.src=m.src;if(v){el.muted=true;el.autoplay=true;el.loop=true;el.playsInline=true}box.appendChild(el)}function card(label,title,m,href,wide){const a=document.createElement('a');a.className='space'+(wide?' wide':'');a.href=href;const mm=document.createElement('div');mm.className='spaceMedia';addMedia(mm,m);const t=document.createElement('div');t.className='spaceText';t.innerHTML='<small></small><b></b>';t.querySelector('small').textContent=label;t.querySelector('b').textContent=title;a.append(mm,t);return a}fetch('/api/id-hub/member/'+encodeURIComponent(USER_ID)).then(r=>{if(!r.ok)throw Error();return r.json()}).then(m=>{document.getElementById('name').textContent=m.display_name||m.username;document.getElementById('meta').textContent=(m.infini_id||'')+' · '+(m.level||'MEMBER');document.getElementById('bio').textContent=m.bio||'พื้นที่ดิจิทัลของสมาชิก INFINI';addMedia(document.getElementById('heroMedia'),m.cover);const s=document.getElementById('spaces');(m.creative_rooms||[]).forEach((r,i)=>s.appendChild(card('YOUR CONTENT SPACE',r.title||('CREATIVE ROOM '+(i+1)),r.cover,'/id-hub/member/'+encodeURIComponent(USER_ID)+'/creative/'+encodeURIComponent(r.id),true)));s.append(card('ZONE 3','SHOP',m.shop_cover,'/id-hub/member/'+encodeURIComponent(USER_ID)+'/zone/shop',false),card('ZONE 4','COMMUNITY',m.community_cover,'/id-hub/member/'+encodeURIComponent(USER_ID)+'/zone/community',false));const g=document.getElementById('gallery');(m.gallery||[]).slice().reverse().forEach(x=>{const a=document.createElement('a');a.className='g';a.href=x.source_url||('/id-hub/member/'+encodeURIComponent(USER_ID)+'/creative/room_1');addMedia(a,x);g.appendChild(a)});if(!(m.gallery||[]).length)document.getElementById('none').style.display='block'}).catch(()=>document.getElementById('name').textContent='ไม่พบ INFINI ID')</script></body></html>'''


def _simple_public_space(title: str, media: dict, back: str, subtitle: str = "") -> str:
    src=json.dumps(media,ensure_ascii=False); return f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{BASE_STYLE}</head><body><header class="top"><b>∞ {html.escape(title)}</b><a class="btn" href="{html.escape(back)}">← Public ID</a></header><main class="wrap"><section class="hero"><div class="heroMedia" id="m"></div><div class="shade"></div><div class="identity"><div class="ey">PUBLIC SPACE</div><div class="name">{html.escape(title)}</div><div class="bio">{html.escape(subtitle)}</div></div></section></main><script>const x={src};const b=document.getElementById('m');if(x&&x.src){{const v=(x.type||'').startsWith('video')||/\\.(mp4|webm|mov)(\\?|$)/i.test(x.src);const e=document.createElement(v?'video':'img');e.src=x.src;if(v){{e.muted=true;e.autoplay=true;e.loop=true;e.playsInline=true}}b.appendChild(e)}}</script></body></html>'''


def install_id_hub_7000(app: FastAPI) -> None:
    if getattr(app.state,"_infini_id_hub_clean_v1",False): return
    app.state._infini_id_hub_clean_v1=True

    @app.get("/api/id-hub/members")
    async def members(request: Request):
        current=_current_user_id(request)
        if not current: return JSONResponse({"ok":False,"error":"login required"},status_code=401)
        return JSONResponse({"ok":True,"current_user_id":current,"members":_all_members()})

    @app.get("/api/id-hub/member/{user_id}")
    async def member(user_id: str):
        users=_load_users(); m=users.get(user_id)
        if not isinstance(m,dict): raise HTTPException(404,"member not found")
        return JSONResponse(_member_record(user_id,m))

    @app.get("/id-hub",response_class=HTMLResponse)
    async def hub(request: Request):
        if not _current_user_id(request): return RedirectResponse(LOGIN_URL,status_code=303)
        return HTMLResponse(HUB_HTML)

    @app.get("/id-hub/member/{user_id}",response_class=HTMLResponse)
    async def public_member(user_id: str):
        return HTMLResponse(PUBLIC_HTML.replace("__USER_ID_JSON__",json.dumps(user_id,ensure_ascii=False)))

    @app.get("/id-hub/member/{user_id}/creative/{room_id}",response_class=HTMLResponse)
    async def public_creative(user_id: str, room_id: str):
        member=_load_users().get(user_id)
        if not isinstance(member,dict): raise HTTPException(404,"member not found")
        rec=_member_record(user_id,member); room=next((r for r in rec["creative_rooms"] if r["id"]==room_id),None)
        if not room: raise HTTPException(404,"room not found")
        media=room.get("gate") if room.get("gate",{}).get("src") else room.get("cover",{})
        return HTMLResponse(_simple_public_space(room.get("title") or "CREATIVE ROOM",media,f"/id-hub/member/{quote(user_id)}","Creative Room ของ INFINI ID นี้"))

    @app.get("/id-hub/member/{user_id}/zone/{zone}",response_class=HTMLResponse)
    async def public_zone(user_id: str, zone: str):
        member=_load_users().get(user_id)
        if not isinstance(member,dict): raise HTTPException(404,"member not found")
        rec=_member_record(user_id,member)
        if zone=="shop": title,media="SHOP ZONE",rec["shop_cover"]
        elif zone in {"community","showcase"}: title,media="COMMUNITY ZONE",rec["community_cover"]
        else: raise HTTPException(404,"zone not found")
        return HTMLResponse(_simple_public_space(title,media,f"/id-hub/member/{quote(user_id)}","พื้นที่ของสมาชิกคนนี้"))
