from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer
from pathlib import Path
from typing import Any
import json
import os

BASE_DIR = Path(__file__).resolve().parent
INFINI_8032_ROOT = Path(
    os.getenv("INFINI_8032_ROOT", str(BASE_DIR.parent))
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
ID_STATE_DIR = BASE_DIR / "data" / "id_users"
LOGIN_URL = os.getenv("INFINI_LOGIN_URL", "http://127.0.0.1:8032/login")


def _read_json(path: Path, default: Any) -> Any:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return default


def _load_users() -> dict[str, dict]:
    raw = _read_json(USERS_FILE, {})
    return raw if isinstance(raw, dict) else {}


def _safe_user_id(user_id: str) -> str:
    return "".join(ch for ch in str(user_id) if ch.isalnum() or ch in "-_")[:80] or "member"


def _derived_infini_id(user_id: str) -> str:
    raw = str(user_id).removeprefix("user_").replace("-", "").replace("_", "")
    return "INF-" + (raw[:8] or "00000001").upper()


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
    users = _load_users()
    return user_id if user_id in users else None


def _state_for(user_id: str) -> dict:
    path = ID_STATE_DIR / f"{_safe_user_id(user_id)}.json"
    data = _read_json(path, {})
    return data if isinstance(data, dict) else {}


def _media_obj(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {"src": "", "type": ""}
    src = str(value.get("src") or value.get("url") or "").strip()
    media_type = str(value.get("type") or value.get("media_type") or "").strip()
    return {"src": src, "type": media_type}


def _member_record(user_id: str, member: dict) -> dict:
    state = _state_for(user_id)
    username = str(member.get("username") or state.get("username") or "INFINI MEMBER").strip()
    display_name = str(state.get("displayName") or username or "INFINI MEMBER").strip()
    infini_id = str(member.get("infini_id") or state.get("infiniId") or _derived_infini_id(user_id)).strip()
    cover = _media_obj(state.get("idCover"))
    creative = _media_obj(state.get("creativeCover"))
    zone_covers_raw = state.get("zoneCovers") if isinstance(state.get("zoneCovers"), dict) else {}
    gallery_raw = state.get("gallery") if isinstance(state.get("gallery"), list) else []
    gallery = []
    for item in gallery_raw[-12:]:
        media = _media_obj(item)
        if media["src"]:
            gallery.append(media)
    return {
        "user_id": user_id,
        "display_name": display_name,
        "username": username,
        "infini_id": infini_id,
        "level": str(state.get("level") or "MEMBER"),
        "bio": str(state.get("bio") or "").strip(),
        "cover": cover,
        "creative_cover": creative,
        "shop_cover": _media_obj(zone_covers_raw.get("shop")),
        "community_cover": _media_obj(zone_covers_raw.get("showcase") or zone_covers_raw.get("community")),
        "gallery": gallery,
        "created_at": str(member.get("created_at") or member.get("created") or ""),
    }


def _all_members() -> list[dict]:
    users = _load_users()
    rows: list[tuple[int, dict]] = []
    for index, (key, member) in enumerate(users.items()):
        if not isinstance(member, dict):
            continue
        user_id = str(member.get("id") or (key if str(key).startswith("user_") else "")).strip()
        if not user_id:
            # Skip the old username/password-only records. They are not full INFINI IDs.
            continue
        rows.append((index, _member_record(user_id, member)))

    # Oldest first, so every new registration naturally appears at the end.
    rows.sort(key=lambda pair: (pair[1].get("created_at") or "9999", pair[0]))
    return [row for _, row in rows]


HUB_HTML = r'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>รวมไอดี · INFINI</title>
<style>
:root{--bg:#030303;--panel:#0d0d10;--line:rgba(255,139,31,.32);--accent:#ff8b1f;--text:#f7f7f7;--muted:#999aa1}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;min-height:100%;background:#000;color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}body{background:radial-gradient(circle at 75% 0,rgba(255,112,0,.14),transparent 28%),linear-gradient(#050505,#000)}
a{color:inherit;text-decoration:none}.top{position:sticky;top:0;z-index:20;height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:rgba(0,0,0,.9);border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(15px)}.brand{font-weight:1000;letter-spacing:.07em}.brand b{color:var(--accent);font-size:22px;margin-right:8px}.back{border:1px solid var(--line);border-radius:999px;padding:10px 15px;color:#ffd4ac;background:#0b0704;font-weight:900}
.wrap{max-width:820px;margin:auto;padding:18px 14px 130px}.eyebrow{color:var(--accent);font-weight:1000;letter-spacing:.13em;font-size:11px}.title{margin:7px 0 5px;font-size:40px;line-height:.95;font-weight:1000}.title span{color:var(--accent)}.desc{color:#b0b0b5;line-height:1.5;font-size:14px;max-width:620px}.stats{display:flex;gap:10px;margin:18px 0}.stat{min-width:112px;border:1px solid var(--line);border-radius:18px;background:rgba(12,8,5,.8);padding:12px}.stat b{display:block;color:var(--accent);font-size:23px}.stat span{font-size:11px;color:#b2b2b7}
.searchWrap{position:sticky;top:73px;z-index:10;padding:8px 0 14px;background:linear-gradient(180deg,rgba(0,0,0,.97),rgba(0,0,0,.82),transparent)}.search{width:100%;border:1px solid rgba(255,255,255,.15);border-radius:20px;background:#0c0c0f;color:#fff;padding:15px 17px;font:inherit;outline:none}.search:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,139,31,.1)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{min-width:0;border:1px solid rgba(255,255,255,.13);border-radius:23px;background:linear-gradient(145deg,#111115,#080809);overflow:hidden;box-shadow:0 15px 40px rgba(0,0,0,.35)}.card:active{transform:scale(.985)}.media{position:relative;aspect-ratio:4/5;background:radial-gradient(circle at 65% 18%,rgba(255,130,25,.25),transparent 32%),linear-gradient(145deg,#17100a,#050505);overflow:hidden}.media img,.media video{width:100%;height:100%;object-fit:cover;display:block}.media:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,.75))}.empty{position:absolute;inset:0;display:grid;place-items:center;color:rgba(255,139,31,.78);font-size:50px;font-weight:300}.badge{position:absolute;left:10px;top:10px;z-index:2;border:1px solid rgba(255,139,31,.45);background:rgba(0,0,0,.72);border-radius:999px;padding:6px 9px;color:#ffc287;font-size:9px;font-weight:1000;letter-spacing:.08em}.mine{right:10px;left:auto;color:#fff;background:rgba(255,139,31,.85)}.info{padding:13px}.name{font-size:17px;font-weight:1000;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.id{color:#c5c5c9;font-size:11px;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.bio{color:#818188;font-size:10px;line-height:1.35;margin-top:7px;height:28px;overflow:hidden}.visit{display:flex;align-items:center;justify-content:space-between;margin-top:11px;color:#ffb469;font-size:11px;font-weight:900}.emptyResult{display:none;border:1px dashed var(--line);border-radius:22px;padding:34px 18px;text-align:center;color:#999}.bottom{position:fixed;left:50%;bottom:13px;transform:translateX(-50%);width:min(820px,calc(100% - 24px));height:68px;border:1px solid rgba(255,139,31,.28);border-radius:25px;background:rgba(5,5,5,.9);backdrop-filter:blur(15px);display:flex;align-items:center;justify-content:space-around;z-index:30}.bottom a{display:flex;flex-direction:column;align-items:center;gap:4px;color:#aaa;font-size:10px}.bottom a.active{color:var(--accent)}.bottom b{font-size:20px}
@media(min-width:700px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.title{font-size:54px}}
</style>
</head>
<body>
<header class="top"><div class="brand"><b>∞</b>รวมไอดี</div><a class="back" href="/id-home">← กลับ</a></header>
<main class="wrap">
  <div class="eyebrow">EXPLORE INFINI MEMBERS</div>
  <h1 class="title">รวม <span>INFINI ID</span></h1>
  <div class="desc">สมาชิกที่สมัครสำเร็จจะต่อท้ายเป็นช่องใหม่อัตโนมัติ แตะช่องเพื่อเข้าเยี่ยมชมหน้าไอดีของสมาชิกคนนั้น</div>
  <div class="stats"><div class="stat"><b id="total">0</b><span>ไอดีทั้งหมด</span></div></div>
  <div class="searchWrap"><input class="search" id="search" type="search" placeholder="ค้นหาชื่อ หรือ INF-..." autocomplete="off"></div>
  <section class="grid" id="grid"></section>
  <div class="emptyResult" id="emptyResult">ไม่พบ INFINI ID ที่ค้นหา</div>
</main>
<nav class="bottom"><a href="/id-home"><b>⌂</b><span>หน้าหลัก</span></a><a class="active" href="/id-hub"><b>∞</b><span>รวมไอดี</span></a><a href="/"><b>▣</b><span>ครีเอทีฟ</span></a><a href="/zone-hub"><b>◇</b><span>โซน</span></a></nav>
<script>
const grid=document.getElementById('grid'), search=document.getElementById('search'), empty=document.getElementById('emptyResult');
let members=[], currentUser='';
function mediaNode(media){
  const wrap=document.createElement('div'); wrap.className='media';
  if(media && media.src){
    const isVideo=(media.type||'').toLowerCase().startsWith('video') || /\.(mp4|webm|mov)(\?|$)/i.test(media.src);
    const el=document.createElement(isVideo?'video':'img'); el.src=media.src;
    if(isVideo){el.muted=true;el.autoplay=true;el.loop=true;el.playsInline=true}
    el.loading='lazy'; wrap.appendChild(el);
  }else{const e=document.createElement('div');e.className='empty';e.textContent='∞';wrap.appendChild(e)}
  const badge=document.createElement('span');badge.className='badge';badge.textContent='INFINI ID';wrap.appendChild(badge);
  return wrap;
}
function render(){
  const q=(search.value||'').trim().toLowerCase(); grid.innerHTML='';
  const list=members.filter(m=>[m.display_name,m.username,m.infini_id].join(' ').toLowerCase().includes(q));
  list.forEach(m=>{
    const a=document.createElement('a');a.className='card';a.href='/id-hub/member/'+encodeURIComponent(m.user_id);
    const media=mediaNode(m.cover); if(m.user_id===currentUser){const mine=document.createElement('span');mine.className='badge mine';mine.textContent='ไอดีของคุณ';media.appendChild(mine)} a.appendChild(media);
    const info=document.createElement('div');info.className='info';
    const name=document.createElement('div');name.className='name';name.textContent=m.display_name||m.username||'INFINI MEMBER';
    const id=document.createElement('div');id.className='id';id.textContent=(m.infini_id||'')+' · '+(m.level||'MEMBER');
    const bio=document.createElement('div');bio.className='bio';bio.textContent=m.bio||'พื้นที่ดิจิทัลของสมาชิก INFINI';
    const visit=document.createElement('div');visit.className='visit';visit.innerHTML='<span>เข้าชมพื้นที่</span><span>→</span>';
    info.append(name,id,bio,visit);a.appendChild(info);grid.appendChild(a);
  });
  empty.style.display=list.length?'none':'block';
}
fetch('/api/id-hub/members').then(r=>{if(!r.ok)throw new Error('load failed');return r.json()}).then(data=>{members=data.members||[];currentUser=data.current_user_id||'';document.getElementById('total').textContent=members.length;render()}).catch(()=>{empty.textContent='โหลดรายชื่อสมาชิกไม่สำเร็จ';empty.style.display='block'});
search.addEventListener('input',render);
</script>
</body></html>'''


PUBLIC_HTML = r'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>INFINI Public ID</title>
<style>
:root{--accent:#ff8b1f;--line:rgba(255,139,31,.34);--muted:#9b9ba2}*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;background:#000;color:#fff;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}body{background:radial-gradient(circle at 70% 0,rgba(255,120,0,.13),transparent 30%),#000}a{color:inherit;text-decoration:none}.top{position:sticky;top:0;z-index:20;height:62px;display:flex;align-items:center;justify-content:space-between;padding:0 15px;background:rgba(0,0,0,.9);border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(15px)}.brand{font-weight:1000;letter-spacing:.08em}.brand b{color:var(--accent);font-size:22px;margin-right:7px}.btn{border:1px solid var(--line);border-radius:999px;padding:10px 15px;background:#0c0805;color:#ffd0a2;font-weight:900}.wrap{max-width:760px;margin:auto;padding:16px 14px 110px}.hero{position:relative;min-height:460px;border:1px solid var(--line);border-radius:29px;overflow:hidden;background:radial-gradient(circle at 70% 18%,rgba(255,130,25,.28),transparent 35%),linear-gradient(145deg,#17100a,#050505)}.heroMedia{position:absolute;inset:0}.heroMedia img,.heroMedia video{width:100%;height:100%;object-fit:cover;display:block}.hero:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05),rgba(0,0,0,.16) 45%,rgba(0,0,0,.92))}.heroEmpty{position:absolute;inset:0;display:grid;place-items:center;color:rgba(255,139,31,.6);font-size:100px}.identity{position:absolute;z-index:3;left:20px;right:20px;bottom:22px}.eyebrow{color:var(--accent);font-size:11px;font-weight:1000;letter-spacing:.15em}.name{font-size:34px;font-weight:1000;line-height:1.03;margin-top:6px}.meta{color:#ddd;margin-top:7px;font-size:13px}.bio{color:#aaa;line-height:1.5;margin-top:12px;font-size:13px;white-space:pre-wrap}.section{margin-top:20px}.section h2{font-size:20px;margin:0 0 11px}.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}.space{position:relative;min-height:220px;border:1px solid rgba(255,255,255,.13);border-radius:23px;overflow:hidden;background:#0c0c0e}.space.wide{grid-column:1/-1;min-height:250px}.spaceMedia{position:absolute;inset:0}.spaceMedia img,.spaceMedia video{width:100%;height:100%;object-fit:cover;display:block}.space:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05),rgba(0,0,0,.88))}.spaceText{position:absolute;z-index:2;left:15px;right:15px;bottom:15px}.spaceText small{color:var(--accent);font-weight:1000;letter-spacing:.1em}.spaceText b{display:block;font-size:20px;margin-top:4px}.placeholder{position:absolute;inset:0;display:grid;place-items:center;color:rgba(255,139,31,.35);font-size:45px}.gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.g{aspect-ratio:1;border:1px solid rgba(255,255,255,.1);border-radius:15px;overflow:hidden;background:#0d0d0f}.g img,.g video{width:100%;height:100%;object-fit:cover;display:block}.none{color:#777;border:1px dashed rgba(255,139,31,.28);border-radius:18px;padding:23px;text-align:center}.bottom{position:fixed;left:50%;bottom:13px;transform:translateX(-50%);width:min(760px,calc(100% - 24px));height:65px;border:1px solid var(--line);border-radius:24px;background:rgba(4,4,4,.91);backdrop-filter:blur(15px);display:flex;align-items:center;justify-content:space-around;z-index:30}.bottom a{font-size:12px;font-weight:900;color:#bbb}.bottom a:first-child{color:var(--accent)}
</style></head><body>
<header class="top"><div class="brand"><b>∞</b>PUBLIC ID</div><a class="btn" href="/id-hub">← รวมไอดี</a></header>
<main class="wrap"><section class="hero" id="hero"><div class="heroMedia" id="heroMedia"></div><div class="heroEmpty" id="heroEmpty">∞</div><div class="identity"><div class="eyebrow">INFINI DIGITAL SPACE</div><div class="name" id="name">กำลังโหลด...</div><div class="meta" id="meta"></div><div class="bio" id="bio"></div></div></section>
<section class="section"><h2>พื้นที่สาธารณะ</h2><div class="cards" id="spaces"></div></section>
<section class="section"><h2>ผลงานล่าสุด</h2><div class="gallery" id="gallery"></div><div class="none" id="noGallery" style="display:none">ยังไม่มีผลงานสาธารณะ</div></section></main>
<nav class="bottom"><a href="/id-hub">∞ รวมไอดี</a><a href="/id-home">⌂ ไอดีของฉัน</a></nav>
<script>
const USER_ID=__USER_ID_JSON__;
function addMedia(container,media){if(!media||!media.src)return false;const isVideo=(media.type||'').toLowerCase().startsWith('video')||/\.(mp4|webm|mov)(\?|$)/i.test(media.src);const el=document.createElement(isVideo?'video':'img');el.src=media.src;if(isVideo){el.muted=true;el.autoplay=true;el.loop=true;el.playsInline=true}container.appendChild(el);return true}
function spaceCard(label,title,media,wide=false){const card=document.createElement('article');card.className='space'+(wide?' wide':'');const m=document.createElement('div');m.className='spaceMedia';if(!addMedia(m,media)){const p=document.createElement('div');p.className='placeholder';p.textContent='∞';m.appendChild(p)}const text=document.createElement('div');text.className='spaceText';const small=document.createElement('small');small.textContent=label;const b=document.createElement('b');b.textContent=title;text.append(small,b);card.append(m,text);return card}
fetch('/api/id-hub/member/'+encodeURIComponent(USER_ID)).then(r=>{if(!r.ok)throw new Error('not found');return r.json()}).then(m=>{document.title=(m.display_name||'INFINI')+' · INFINI ID';document.getElementById('name').textContent=m.display_name||m.username||'INFINI MEMBER';document.getElementById('meta').textContent=(m.infini_id||'')+' · '+(m.level||'MEMBER');document.getElementById('bio').textContent=m.bio||'พื้นที่ดิจิทัลของสมาชิก INFINI';if(addMedia(document.getElementById('heroMedia'),m.cover))document.getElementById('heroEmpty').style.display='none';const spaces=document.getElementById('spaces');spaces.append(spaceCard('YOUR CONTENT SPACE','CREATIVE ROOM',m.creative_cover,true),spaceCard('ZONE 3','SHOP',m.shop_cover),spaceCard('ZONE 4','COMMUNITY',m.community_cover));const gallery=document.getElementById('gallery');(m.gallery||[]).forEach(media=>{const box=document.createElement('div');box.className='g';addMedia(box,media);gallery.appendChild(box)});if(!(m.gallery||[]).length)document.getElementById('noGallery').style.display='block'}).catch(()=>{document.getElementById('name').textContent='ไม่พบ INFINI ID';document.getElementById('bio').textContent='บัญชีนี้อาจถูกลบหรือยังไม่พร้อมแสดงผล'});
</script></body></html>'''


def install_id_hub_7000(app: FastAPI) -> None:
    @app.get("/api/id-hub/members")
    async def id_hub_members(request: Request):
        current = _current_user_id(request)
        if not current:
            return JSONResponse({"ok": False, "error": "login required"}, status_code=401)
        return JSONResponse({
            "ok": True,
            "current_user_id": current,
            "members": _all_members(),
        })

    @app.get("/api/id-hub/member/{user_id}")
    async def id_hub_member(user_id: str):
        users = _load_users()
        member = users.get(user_id)
        if not isinstance(member, dict) or not str(member.get("id") or user_id).startswith("user_"):
            raise HTTPException(status_code=404, detail="member not found")
        return JSONResponse(_member_record(user_id, member))

    @app.get("/id-hub", response_class=HTMLResponse)
    async def id_hub_page(request: Request):
        if not _current_user_id(request):
            return RedirectResponse(LOGIN_URL, status_code=303)
        return HTMLResponse(HUB_HTML)

    @app.get("/id-hub/member/{user_id}", response_class=HTMLResponse)
    async def id_hub_public_member(user_id: str):
        html = PUBLIC_HTML.replace("__USER_ID_JSON__", json.dumps(user_id, ensure_ascii=False))
        return HTMLResponse(html)
