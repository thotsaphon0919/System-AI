from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
USERS_FILE = DATA / "users.json"
ROOT7000 = Path(os.getenv("INFINI_7000_ROOT", str(BASE.parent / "7000"))).expanduser()
ID_STATE_DIR = ROOT7000 / "data" / "id_users"


def _read(path: Path, fallback: Any):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return fallback


def _safe(uid:str)->str:return "".join(c for c in str(uid) if c.isalnum() or c in "-_")[:80] or "member"


def _media(state:dict,key:str):
    zones=state.get("zoneCovers") if isinstance(state.get("zoneCovers"),dict) else {}
    item=zones.get(key) if isinstance(zones.get(key),dict) else {}
    return {"src":str(item.get("src") or ""),"type":str(item.get("type") or "")}


def _members():
    users=_read(USERS_FILE,{})
    if not isinstance(users,dict):return []
    out=[]
    for idx,(k,u) in enumerate(users.items()):
        if not isinstance(u,dict):continue
        uid=str(u.get("id") or (k if str(k).startswith("user_") else "")).strip()
        if not uid:continue
        state=_read(ID_STATE_DIR/f"{_safe(uid)}.json",{})
        if not isinstance(state,dict):state={}
        # The central shop zone is a directory of real INFINI IDs. Every full ID can appear;
        # its own shop image is used when the owner has uploaded one.
        out.append({"user_id":uid,"name":str(state.get("displayName") or u.get("username") or uid),"infini_id":str(state.get("infiniId") or u.get("infini_id") or ""),"cover":_media(state,"shop"),"created_at":str(u.get("created_at") or ""),"idx":idx})
    out.sort(key=lambda x:(x["created_at"] or "9999",x["idx"]))
    return out


PAGE=r'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>INFINI SHOP ZONE</title><style>*{box-sizing:border-box}html,body{margin:0;background:#020202;color:#fff;font-family:system-ui}.wrap{max-width:860px;margin:auto;padding:18px 14px 100px}.top{display:flex;justify-content:space-between;align-items:center;gap:10px}.back{border:1px solid rgba(255,139,31,.4);border-radius:999px;padding:9px 13px;color:#ffc17d;text-decoration:none}.ey{margin-top:22px;color:#ff941f;font-size:11px;font-weight:1000;letter-spacing:.13em}h1{font-size:40px;margin:6px 0 4px}.desc{color:#999;line-height:1.45}.search{width:100%;margin:16px 0;border:1px solid rgba(255,139,31,.35);border-radius:18px;background:#080808;color:#fff;padding:14px;font:inherit}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{border:1px solid rgba(255,139,31,.32);border-radius:23px;overflow:hidden;background:#080808;color:inherit;text-decoration:none}.media{aspect-ratio:4/5;background:#000;display:grid;place-items:center}.media img,.media video{width:100%;height:100%;object-fit:contain}.empty{font-size:48px;color:rgba(255,139,31,.3)}.info{padding:12px}.info b{display:block;font-size:16px}.info small{display:block;margin-top:4px;color:#999}@media(min-width:720px){.grid{grid-template-columns:repeat(4,1fr)}}</style></head><body><main class="wrap"><div class="top"><b>∞ INFINI SHOP ZONE</b><a class="back" href="/service">← SERVICE</a></div><div class="ey">ONE CARD = ONE INFINI ID</div><h1>โซนร้านค้า</h1><div class="desc">รายชื่อ INFINI ID จริงในระบบ แตะการ์ดเพื่อเข้า Shop Zone ของ ID นั้น</div><input class="search" id="q" placeholder="ค้นหาชื่อ หรือ INFINI ID"><section class="grid" id="grid"></section></main><script>const DATA=__DATA__;function media(m){if(!m||!m.src)return '<div class="empty">∞</div>';const v=(m.type||'').startsWith('video')||/\.(mp4|webm|mov)(\?|$)/i.test(m.src);return v?'<video src="'+m.src+'" muted autoplay loop playsinline></video>':'<img src="'+m.src+'">'}function render(){const q=(document.getElementById('q').value||'').toLowerCase(),box=document.getElementById('grid');box.innerHTML='';DATA.filter(x=>[x.name,x.infini_id].join(' ').toLowerCase().includes(q)).forEach(x=>{const a=document.createElement('a');a.className='card';a.href='/id-hub/member/'+encodeURIComponent(x.user_id)+'/zone/shop';a.innerHTML='<div class="media">'+media(x.cover)+'</div><div class="info"><b></b><small></small></div>';a.querySelector('b').textContent=x.name;a.querySelector('small').textContent=x.infini_id||'INFINI ID';box.appendChild(a)})}document.getElementById('q').oninput=render;render()</script></body></html>'''

class _ShopDirectoryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        if request.url.path in {"/zone/shop","/shop-zone","/shop-directory"} and request.method=="GET":
            page=PAGE.replace("__DATA__",json.dumps(_members(),ensure_ascii=False).replace("</","<\\/"))
            return HTMLResponse(page)
        return await call_next(request)


def install_infini_shop_directory_8033(app)->None:
    if getattr(app.state,"_infini_shop_directory_v1",False):return
    app.state._infini_shop_directory_v1=True
    app.add_middleware(_ShopDirectoryMiddleware)
