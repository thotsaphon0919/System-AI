from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
import json
import os

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from itsdangerous import URLSafeSerializer, BadSignature

MODULE_NAME = "INFINI_CLEAN_UI_7000_V1"


def _editor_owner(request: Request) -> str | None:
    token = request.cookies.get("infini_session")
    if not token:
        return None
    base = Path(__file__).resolve().parent  # .../7000
    # Same shared secret location used by id_entry_7000.py / id_hub_7000.py /
    # friend_chat_entry_7000.py: <project_root>/8032/data/infini_session_secret.txt
    # (overridable via INFINI_8032_ROOT env var). The previous version of this
    # function looked in base.parent/data and base/data instead, which don't
    # exist — that mismatch made every session look invalid here, so the
    # gear button showed (cookie present) but /infini-editor always 401'd.
    infini_8032_root = Path(os.getenv("INFINI_8032_ROOT", str(base.parent / "8032")))
    candidates = [
        infini_8032_root / "data" / "infini_session_secret.txt",
        base.parent / "8032" / "data" / "infini_session_secret.txt",
        base.parent / "data" / "infini_session_secret.txt",
        base / "data" / "infini_session_secret.txt",
    ]
    secret = ""
    for p in candidates:
        try:
            if p.exists():
                secret = p.read_text(encoding="utf-8").strip()
                if secret:
                    break
        except Exception:
            pass
    secret = secret or os.getenv("INFINI_SESSION_SECRET", "").strip()
    if not secret:
        return None
    try:
        payload = URLSafeSerializer(secret, salt="infini-session").loads(token)
        return str((payload or {}).get("user_id") or "").strip() or None
    except (BadSignature, Exception):
        return None

ID_PATCH = r'''
<style id="infini-clean-id-style">
/* Clean Release: zone cards keep one size and show the whole uploaded image. */
.zoneMedia{height:auto!important;aspect-ratio:4/5!important;background:#000!important}
.zoneMedia img,.zoneMedia video{width:100%!important;height:100%!important;object-fit:contain!important;background:#000!important}
.creative-card{position:relative}
.infiniRoomAdd{position:absolute;right:16px;bottom:16px;z-index:12;width:62px;height:62px;border-radius:50%;border:2px solid #ff8b1f;background:#050505;color:#ff9a28;font-size:35px;font-weight:1000;display:grid;place-items:center;box-shadow:0 10px 30px rgba(0,0,0,.45)}
.infiniExtraRooms{display:grid;grid-template-columns:1fr;gap:14px;margin-top:14px}
.infiniRoomCard{position:relative;min-height:235px;border-radius:26px;overflow:hidden;border:1px solid rgba(255,139,31,.42);background:#080808;cursor:pointer}
.infiniRoomCard .rmedia{position:absolute;inset:0;display:grid;place-items:center;background:#070707}
.infiniRoomCard .rmedia img,.infiniRoomCard .rmedia video{width:100%;height:100%;object-fit:contain;background:#000}
.infiniRoomCard .rshade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.03),rgba(0,0,0,.78));pointer-events:none}
.infiniRoomCard .rcopy{position:absolute;left:18px;right:92px;bottom:18px;z-index:3}.infiniRoomCard .rcopy small{color:#ff9a28;font-weight:900}.infiniRoomCard .rcopy b{display:block;font-size:24px;margin-top:3px}
.workCard{position:relative}.infiniDeleteWork{position:absolute;right:8px;top:8px;z-index:9;width:34px;height:34px;border-radius:50%;border:1px solid rgba(255,139,31,.6);background:rgba(0,0,0,.82);color:#fff;font-size:18px;font-weight:900}
#infiniLogoutBtn{font-size:18px!important}
</style>
<script id="infini-clean-id-script">
(function(){
  if(window.__INFINI_CLEAN_ID__)return;window.__INFINI_CLEAN_ID__=1;
  function waitState(fn,tries){tries=tries||0;if(window.STATE&&typeof window.saveState==='function')return fn();if(tries<30)setTimeout(()=>waitState(fn,tries+1),100)}
  function defaultRooms(){return [{id:'room_1',title:'CREATIVE ROOM 1'}]}
  function ensureRooms(){
    if(!Array.isArray(STATE.creativeRooms)||!STATE.creativeRooms.length) STATE.creativeRooms=defaultRooms();
    if(!STATE.creativeRooms[0].id)STATE.creativeRooms[0].id='room_1';
    if(!STATE.creativeRooms[0].title)STATE.creativeRooms[0].title='CREATIVE ROOM 1';
    if(STATE.creativeCover&&!STATE.creativeRooms[0].cover)STATE.creativeRooms[0].cover=STATE.creativeCover;
    return STATE.creativeRooms;
  }
  function roomMedia(item){
    const wrap=document.createElement('div');wrap.className='rmedia';const m=item&&item.cover;
    if(m&&m.src&&typeof mediaEl==='function'){const el=mediaEl(m.src,m.type);if(el.tagName==='VIDEO'){el.autoplay=true;el.muted=true;el.loop=true;el.controls=false}wrap.appendChild(el)}
    else wrap.innerHTML='<div style="font-size:62px;color:rgba(255,139,31,.25)">∞</div>';
    return wrap;
  }
  function addButton(parent,handler){const b=document.createElement('button');b.type='button';b.className='infiniRoomAdd';b.textContent='+';b.title='เพิ่ม Creative Room';b.onclick=e=>{e.preventDefault();e.stopPropagation();handler()};parent.appendChild(b);return b}
  async function createRoom(){
    const rooms=ensureRooms();const n=rooms.length+1;rooms.push({id:'room_'+n,title:'CREATIVE ROOM '+n});await saveState();renderRooms();if(window.toast)toast('สร้าง CREATIVE ROOM '+n+' แล้ว');
  }
  function renderRooms(){
    const base=document.getElementById('creativeCard');if(!base)return;const rooms=ensureRooms();
    base.dataset.href='/creative-gate?room='+encodeURIComponent(rooms[0].id);
    const h=base.querySelector('h2');if(h)h.textContent=rooms[0].title||'CREATIVE ROOM 1';
    const old=base.querySelector('.infiniRoomAdd');if(old)old.remove();if(rooms.length===1)addButton(base,createRoom);
    let box=document.getElementById('infiniExtraRooms');if(!box){box=document.createElement('div');box.id='infiniExtraRooms';box.className='infiniExtraRooms';base.insertAdjacentElement('afterend',box)}box.innerHTML='';
    rooms.slice(1).forEach((r,idx)=>{const c=document.createElement('article');c.className='infiniRoomCard';c.appendChild(roomMedia(r));const shade=document.createElement('div');shade.className='rshade';c.appendChild(shade);const copy=document.createElement('div');copy.className='rcopy';copy.innerHTML='<small>YOUR CONTENT SPACE</small><b></b>';copy.querySelector('b').textContent=r.title||('CREATIVE ROOM '+(idx+2));c.appendChild(copy);c.onclick=()=>location.href='/creative-gate?room='+encodeURIComponent(r.id);if(idx===rooms.length-2)addButton(c,createRoom);box.appendChild(c)});
  }
  function replaceLogout(){
    const b=document.querySelector('.bottomNav .navPlus');if(!b)return;b.id='infiniLogoutBtn';b.textContent='↪';b.title='ออกจากระบบ';b.removeAttribute('onclick');b.onclick=()=>{const f=document.createElement('form');f.method='POST';f.action='/8032/api/logout';document.body.appendChild(f);f.submit()};
  }
  function overrideLatest(){
    window.renderLatest=function(){const grid=document.getElementById('latestGrid');if(!grid)return;grid.innerHTML='';const all=Array.isArray(STATE.gallery)?STATE.gallery:[];const selected=all.map((item,index)=>({item,index})).slice(-6).reverse();selected.forEach((row,i)=>{const item=row.item;const card=document.createElement('div');card.className='workCard';const m=document.createElement('div');m.className='workMedia';m.appendChild(mediaEl(item.src,item.type));const c=document.createElement('div');c.className='workCopy';c.innerHTML='<b>ผลงาน '+(selected.length-i)+'</b><span>จากคลัง INFINI ID</span>';const del=document.createElement('button');del.type='button';del.className='infiniDeleteWork';del.textContent='×';del.onclick=async e=>{e.preventDefault();e.stopPropagation();if(!confirm('ลบผลงานชิ้นนี้ใช่ไหม'))return;STATE.gallery.splice(row.index,1);await saveState();renderLatest();if(window.toast)toast('ลบแล้ว')};card.append(m,c,del);grid.appendChild(card)});const add=document.createElement('button');add.type='button';add.className='workCard addWork';add.innerHTML='<div><strong>＋</strong><span>เพิ่มผลงานใหม่</span></div>';add.onclick=()=>openUpload('gallery');grid.appendChild(add)};
  }
  waitState(()=>{
    overrideLatest();
    const oldApply=window.applyState;if(typeof oldApply==='function')window.applyState=function(){ensureRooms();oldApply();renderRooms();window.renderLatest()};
    ensureRooms();renderRooms();replaceLogout();window.renderLatest();
    if(!STATE.__cleanRoomsSeeded){STATE.__cleanRoomsSeeded=true;saveState().catch(()=>{})}
  });
})();
</script>
'''

CREATIVE_GRID_PATCH = r'''
<style id="infini-clean-creative-grid-style">
.infiniUtilityCard{cursor:pointer;display:grid;place-items:center;text-align:center;background:#050505!important}
.infiniUtilityCard .uicon{font-size:54px;color:#ff981f;font-weight:1000}.infiniUtilityCard .utitle{margin-top:10px;font-size:17px;font-weight:1000;color:#ffc27e}
body .plusBar{display:none!important}
</style>
<script id="infini-clean-creative-grid-script">
(function(){
 if(window.__INFINI_CLEAN_GRID__)return;window.__INFINI_CLEAN_GRID__=1;
 function findFloatingPoster(){return [...document.querySelectorAll('button,a')].find(x=>{const t=(x.textContent||'').trim();const cs=getComputedStyle(x);return t.includes('โปสเตอร์')&&cs.position==='fixed'})}
 function findPlus(){return document.querySelector('.plusBar')||[...document.querySelectorAll('button')].find(x=>(x.textContent||'').trim()==='+'&&getComputedStyle(x).position==='fixed')}
 function makeCard(type,label,icon,source){const c=document.createElement('button');c.type='button';c.className='card infiniUtilityCard '+type;c.innerHTML='<div><div class="uicon">'+icon+'</div><div class="utitle">'+label+'</div></div>';c.onclick=e=>{e.preventDefault();if(source){source.click();return}if(type==='infiniPoster')location.href='/poster'};return c}
 function run(tries){const grid=document.querySelector('.grid');if(!grid){if((tries||0)<30)setTimeout(()=>run((tries||0)+1),150);return}if(grid.querySelector('.infiniUtilityCard'))return;const poster=findFloatingPoster(),plus=findPlus();if(poster)poster.style.display='none';if(plus)plus.style.display='none';grid.append(makeCard('infiniPoster','โปสเตอร์','▣',poster),makeCard('infiniAdd','เพิ่มช่อง','＋',plus))}
 document.readyState==='loading'?document.addEventListener('DOMContentLoaded',()=>run(0)):run(0);setTimeout(()=>run(0),800);let timer=null;new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(()=>run(0),120)}).observe(document.body,{childList:true,subtree:true});
})();
</script>
'''

GATE_PATCH = r'''
<style id="infini-clean-gate-style">.gate-card img,.gate-card video{object-fit:contain!important;background:#000}.infiniGateGear{position:fixed;right:16px;top:72px;z-index:70;width:48px;height:48px;border-radius:50%;border:1px solid rgba(255,139,31,.65);background:#060606;color:#ff9a28;font-size:23px}</style>
<script id="infini-clean-gate-script">
(function(){
 const room=new URLSearchParams(location.search).get('room')||'room_1';
 const enter=[...document.querySelectorAll('button')].find(b=>(b.textContent||'').trim()==='เข้าตึก');if(enter)enter.onclick=()=>location.href='/?creative_room='+encodeURIComponent(room);
 const g=document.createElement('button');g.className='infiniGateGear';g.textContent='⚙';g.title='แก้หน้านี้';g.onclick=()=>location.href='/infini-editor?target='+encodeURIComponent(location.pathname+location.search);document.body.appendChild(g);
})();
</script>
'''

GENERIC_GEAR = r'''
<style id="infini-clean-gear-style">#infiniContextGear{position:fixed;right:14px;top:72px;z-index:99990;width:48px;height:48px;border-radius:50%;border:1px solid rgba(255,139,31,.62);background:rgba(5,5,5,.92);color:#ff9a28;font-size:22px;box-shadow:0 10px 30px rgba(0,0,0,.42)}</style>
<script id="infini-clean-gear-script">(function(){if(document.getElementById('infiniContextGear'))return;if(document.querySelector('#openControl'))return;const b=document.createElement('button');b.id='infiniContextGear';b.textContent='⚙';b.title='แก้หน้านี้';b.onclick=()=>location.href='/infini-editor?target='+encodeURIComponent(location.pathname+location.search);document.body.appendChild(b)})();</script>
'''

EDITOR_HTML = r'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>INFINI Editor</title><style>*{box-sizing:border-box}body{margin:0;background:#030303;color:#fff;font-family:system-ui}.wrap{max-width:760px;margin:auto;padding:20px 14px 100px}.top{display:flex;justify-content:space-between;align-items:center;gap:10px}.back{border:1px solid #754116;border-radius:999px;padding:10px 14px;color:#ffc17d;text-decoration:none}.card{margin-top:18px;border:1px solid rgba(255,139,31,.4);border-radius:26px;padding:18px;background:#0a0806}.ey{color:#ff921e;font-weight:1000;letter-spacing:.12em;font-size:11px}h1{font-size:32px;margin:7px 0 4px}.target{color:#aaa;word-break:break-all}label{display:block;margin-top:15px;color:#c8b9ad;font-size:13px}input,textarea{width:100%;margin-top:7px;border:1px solid #422717;border-radius:16px;background:#050505;color:#fff;padding:13px;font:inherit}textarea{min-height:110px}.save{width:100%;margin-top:18px;border:0;border-radius:18px;background:#ff941f;color:#110700;padding:15px;font-weight:1000}.note{color:#91867e;font-size:12px;line-height:1.5;margin-top:12px}</style></head><body><main class="wrap"><div class="top"><b>∞ INFINI EDITOR</b><a class="back" id="back" href="/id">← กลับหน้าเดิม</a></div><section class="card"><div class="ey">CURRENT PAGE CONTEXT</div><h1>แก้แผ่นที่เข้ามา</h1><div class="target" id="target"></div><label>ชื่อ / หัวข้อของแผ่น<input id="title" placeholder="ถ้าไม่กรอก จะใช้ของเดิม"></label><label>ข้อความสั้น<textarea id="note" placeholder="บันทึกข้อมูลเฉพาะแผ่นนี้"></textarea></label><label>ลิงก์ปลายทาง<input id="link" placeholder="เช่น /creative-gate หรือ /sheet/..."></label><button class="save" id="save">บันทึกสำหรับแผ่นนี้</button><p class="note">เฟืองใช้ Editor กลางตัวเดียว แต่ข้อมูลจะเก็บแยกตาม path/context ของหน้าที่กดเข้ามา เพื่อไม่ให้แก้ข้ามแผ่นกัน</p></section></main><script>const q=new URLSearchParams(location.search),target=q.get('target')||'/id';document.getElementById('target').textContent=target;document.getElementById('back').href=target;fetch('/api/infini-editor/context?target='+encodeURIComponent(target)).then(r=>r.json()).then(d=>{document.getElementById('title').value=d.title||'';document.getElementById('note').value=d.note||'';document.getElementById('link').value=d.link||''});document.getElementById('save').onclick=async()=>{const r=await fetch('/api/infini-editor/context',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target,title:document.getElementById('title').value,note:document.getElementById('note').value,link:document.getElementById('link').value})});const d=await r.json();alert(d.ok?'บันทึกแล้ว':'บันทึกไม่สำเร็จ')}</script></body></html>'''

class _CleanHTMLMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype.lower():
            return response
        try:
            body = b"".join([chunk async for chunk in response.body_iterator]).decode("utf-8", "ignore")
        except Exception:
            return response
        path = request.url.path
        patch = ""
        if path in {"/id", "/id-home"}:
            patch += ID_PATCH
        if path == "/creative-gate":
            patch += GATE_PATCH
        if path == "/" or path.startswith("/room/") or path.startswith("/subpages/"):
            patch += CREATIVE_GRID_PATCH
        # All owner pages get the same context-aware gear entrance unless they already have a native gear.
        if request.cookies.get("infini_session") and path not in {"/infini-editor"}:
            patch += GENERIC_GEAR
        if patch and "</body>" in body:
            body = body.replace("</body>", patch + "</body>", 1)
        headers = {k: v for k, v in response.headers.items() if k.lower() not in {"content-length", "content-encoding"}}
        return HTMLResponse(body, status_code=response.status_code, headers=headers)


def install_infini_clean_ui_7000(app) -> None:
    if getattr(app.state, "_infini_clean_ui_v1", False):
        return
    app.state._infini_clean_ui_v1 = True
    base = Path(__file__).resolve().parent
    db = base / "data" / "infini_editor_context.json"

    def load_db() -> dict:
        try:
            d = json.loads(db.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}

    def save_db(d: dict) -> None:
        db.parent.mkdir(parents=True, exist_ok=True)
        tmp = db.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(db)

    @app.get("/infini-editor", response_class=HTMLResponse)
    async def infini_editor_page(request: Request):
        if not _editor_owner(request):
            return HTMLResponse("login required", status_code=401)
        return HTMLResponse(EDITOR_HTML)

    @app.get("/api/infini-editor/context")
    async def editor_context_get(request: Request, target: str = "/id"):
        uid = _editor_owner(request)
        if not uid:
            return JSONResponse({"ok": False}, status_code=401)
        return JSONResponse(load_db().get(uid, {}).get(target, {}))

    @app.post("/api/infini-editor/context")
    async def editor_context_save(request: Request):
        uid = _editor_owner(request)
        if not uid:
            return JSONResponse({"ok": False}, status_code=401)
        payload = await request.json()
        target = str(payload.get("target") or "/id")[:500]
        d = load_db(); d.setdefault(uid, {})[target] = {
            "title": str(payload.get("title") or "")[:300],
            "note": str(payload.get("note") or "")[:3000],
            "link": str(payload.get("link") or "")[:1000],
        }; save_db(d)
        return JSONResponse({"ok": True})

    app.add_middleware(_CleanHTMLMiddleware)
