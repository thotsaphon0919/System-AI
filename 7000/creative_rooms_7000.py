"""
INFINI Creative Rooms — sequential room gallery.

Lets one user build an ordered series of "CREATIVE ROOM 1", "CREATIVE ROOM
2", ... cards (each its own poster-style image + title), adding more with
a "+" button, matching the reference screenshots. Distinct from the older
single-image "/creative-gate" door/entrance page — this is what a visitor
sees once they're through the gate.

Storage: one JSON file per user (via scoped_data_file, same pattern the
rest of 7000 already uses), so each user's room list is private to them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import time
import uuid

from fastapi import Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
DEFAULT_ROOMS_FILE = DATA / "creative_rooms.json"


def _rooms_file(request: Request):
    try:
        from user_scope_7000 import scoped_data_file
        return scoped_data_file(BASE, "creative_rooms.json", DEFAULT_ROOMS_FILE)
    except Exception:
        return DEFAULT_ROOMS_FILE


def _load(request: Request) -> dict[str, Any]:
    f = _rooms_file(request)
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("rooms"), list):
            return data
    except Exception:
        pass
    return {"rooms": []}


def _save(request: Request, data: dict[str, Any]) -> None:
    f = _rooms_file(request)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(f)


PAGE_HTML = r'''<!doctype html><html lang="th"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>CREATIVE ROOMS</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:#050100;color:#fff;font-family:system-ui,-apple-system,sans-serif}
.top{position:sticky;top:0;z-index:10;height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:rgba(0,0,0,.92);border-bottom:1px solid rgba(255,138,31,.3)}
.top b{color:#ff9a2f;letter-spacing:.1em;font-size:13px}
.top a{color:#ffc17d;text-decoration:none;font-size:13px;font-weight:800}
.wrap{max-width:520px;margin:auto;padding:16px 16px 120px}
.room{position:relative;aspect-ratio:2/3;border-radius:22px;overflow:hidden;background:#0b0b0d;border:1px solid rgba(255,174,25,.25);margin-bottom:16px}
.room img,.room video{width:100%;height:100%;object-fit:cover;display:block}
.room .empty{position:absolute;inset:0;display:grid;place-items:center;color:#886;text-align:center;padding:20px}
.room .empty .plus{font-size:44px;color:#ff9a2f;line-height:1;margin-bottom:8px}
.room .label{position:absolute;left:14px;bottom:14px;right:14px;text-shadow:0 2px 10px #000}
.room .label .mini{color:#ff9a2f;font-size:11px;font-weight:900;letter-spacing:.1em}
.room .label h2{margin:2px 0 0;font-size:24px}
.room .gear{position:absolute;top:12px;right:12px;width:38px;height:38px;border-radius:999px;border:1px solid rgba(255,174,25,.5);background:rgba(0,0,0,.6);color:#ffc17d;font-size:16px;display:grid;place-items:center;cursor:pointer}
.addBtn{width:100%;min-height:58px;border:1px dashed rgba(255,155,40,.55);border-radius:18px;background:rgba(255,148,31,.06);color:#ff9a2f;font-weight:900;font-size:15px;cursor:pointer;margin-top:6px}
.toast{position:fixed;top:66px;left:50%;transform:translateX(-50%);z-index:99;padding:10px 16px;border-radius:999px;background:#18100b;border:1px solid rgba(255,138,31,.5);color:#ffd2a4;font-size:12px;font-weight:900;display:none}
.toast.show{display:block}
input[type=file]{display:none}
</style>
<body>
<div class="top"><b>∞ CREATIVE ROOMS</b><a href="/id">กลับ ID</a></div>
<div class="wrap" id="wrap"></div>
<div class="toast" id="toast"></div>
<input type="file" id="fileInput" accept="image/*,video/*">
<script>
const $=x=>document.getElementById(x);
let ROOMS=[];
let uploadTargetId=null;

function toast(t){const el=$('toast');el.textContent=t;el.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(()=>el.classList.remove('show'),1800)}

function mediaTag(url,type){
  if(!url) return '';
  if(type==='video'||/\.(mp4|webm|mov)(\?|$)/i.test(url)) return `<video src="${url}" muted autoplay loop playsinline></video>`;
  return `<img src="${url}">`;
}

function render(){
  const wrap=$('wrap');
  wrap.innerHTML='';
  ROOMS.forEach((r,i)=>{
    const box=document.createElement('div');
    box.className='room';
    box.innerHTML = r.media_url
      ? mediaTag(r.media_url, r.media_type) + `<div class="label"><div class="mini">YOUR CONTENT SPACE</div><h2>${r.title}</h2></div><div class="gear" data-id="${r.id}">⇧</div>`
      : `<div class="empty"><div><div class="plus">＋</div><b>${r.title}</b><div style="font-size:11px;margin-top:6px;color:#aaa">แตะเพื่อใส่รูป/วิดีโอ</div></div></div><div class="gear" data-id="${r.id}">⇧</div>`;
    box.querySelector('.gear').addEventListener('click', e=>{e.stopPropagation();openUpload(r.id)});
    if(!r.media_url) box.addEventListener('click', ()=>openUpload(r.id));
    wrap.appendChild(box);
  });
  const addBtn=document.createElement('button');
  addBtn.className='addBtn';
  addBtn.textContent='+ เพิ่ม CREATIVE ROOM '+(ROOMS.length+1);
  addBtn.addEventListener('click', addRoom);
  wrap.appendChild(addBtn);
}

function openUpload(roomId){
  uploadTargetId=roomId;
  $('fileInput').click();
}

$('fileInput').addEventListener('change', async ()=>{
  const f=$('fileInput').files && $('fileInput').files[0];
  if(!f || !uploadTargetId) return;
  const fd=new FormData();
  fd.append('file', f);
  toast('กำลังอัปโหลด...');
  try{
    const res=await fetch('/api/creative-rooms/'+uploadTargetId+'/upload', {method:'POST', body:fd});
    const d=await res.json();
    if(!d.ok){toast('อัปโหลดไม่สำเร็จ');return}
    toast('อัปโหลดแล้ว');
    await load();
  }catch(e){toast('อัปโหลดไม่สำเร็จ')}
  finally{$('fileInput').value=''}
});

async function addRoom(){
  const res=await fetch('/api/creative-rooms', {method:'POST'});
  const d=await res.json();
  if(d.ok){ROOMS=d.rooms;render();toast('เพิ่มห้องใหม่แล้ว')}
}

async function load(){
  const res=await fetch('/api/creative-rooms');
  const d=await res.json();
  ROOMS = (d.rooms && d.rooms.length) ? d.rooms : [];
  if(!ROOMS.length){
    // first-time visit: seed with one empty room so there's always
    // at least something to tap, matching the "CREATIVE ROOM 1" reference.
    const res2=await fetch('/api/creative-rooms', {method:'POST'});
    const d2=await res2.json();
    ROOMS = d2.rooms || [];
  }
  render();
}

load();
</script>
</body></html>'''


def install_creative_rooms_7000(app):
    if getattr(app.state, "_creative_rooms_v1", False):
        return
    app.state._creative_rooms_v1 = True

    @app.get("/creative-rooms", response_class=HTMLResponse)
    async def creative_rooms_page(request: Request):
        try:
            from id_entry_7000 import _current_user_id
            if not _current_user_id(request):
                return HTMLResponse("login required", status_code=401)
        except Exception:
            pass
        return HTMLResponse(PAGE_HTML)

    @app.get("/api/creative-rooms")
    async def list_rooms(request: Request):
        return JSONResponse(_load(request))

    @app.post("/api/creative-rooms")
    async def add_room(request: Request):
        data = _load(request)
        n = len(data["rooms"]) + 1
        room = {
            "id": uuid.uuid4().hex[:12],
            "title": f"CREATIVE ROOM {n}",
            "media_url": "",
            "media_type": "",
            "created_at": int(time.time()),
        }
        data["rooms"].append(room)
        _save(request, data)
        return JSONResponse(data)

    @app.delete("/api/creative-rooms/{room_id}")
    async def delete_room(request: Request, room_id: str):
        data = _load(request)
        data["rooms"] = [r for r in data["rooms"] if r.get("id") != room_id]
        _save(request, data)
        return JSONResponse(data)

    @app.post("/api/creative-rooms/{room_id}/upload")
    async def upload_room_media(request: Request, room_id: str, file: UploadFile = File(...)):
        data = _load(request)
        room = next((r for r in data["rooms"] if r.get("id") == room_id), None)
        if not room:
            return JSONResponse({"ok": False, "error": "room not found"}, status_code=404)

        try:
            from main import save_upload_file
            url, media_type = save_upload_file(file)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

        room["media_url"] = url
        room["media_type"] = media_type
        _save(request, data)
        return JSONResponse({"ok": True, "rooms": data["rooms"]})
