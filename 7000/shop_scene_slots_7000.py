from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import json
import mimetypes
import os
import re
import shutil
import time
import uuid

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer
from starlette.middleware.base import BaseHTTPMiddleware

MODULE_NAME = "INFINI_SHOP_SCENE_SLOTS_7000_V4"
BASE = Path(__file__).resolve().parent
USERS_ROOT = BASE / "data" / "shop_scene_users"
LEGACY_ROOT = BASE / "data" / "infini_library_scene_builder"
LEGACY_DB = LEGACY_ROOT / "library.json"
LEGACY_UPLOADS = LEGACY_ROOT / "uploads"
LEGACY_CLAIM = USERS_ROOT / ".legacy_owner_claimed"
SYSTEM_ROOT = BASE / "data" / "shop_scene_system"
SYSTEM_UPLOADS = SYSTEM_ROOT / "scenes"
SYSTEM_DB = SYSTEM_ROOT / "scenes.json"
USERS_ROOT.mkdir(parents=True, exist_ok=True)
SYSTEM_UPLOADS.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _safe_user_id(user_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", user_id)[:80] or "member"


def _shared_data_candidates() -> list[Path]:
    return [
        BASE.parent / "data",
        BASE / "data",
        Path(os.getenv("INFINI_8032_ROOT", str(BASE.parent / "8032"))).expanduser() / "data",
    ]


def _session_secret_file() -> Path | None:
    for d in _shared_data_candidates():
        p = d / "infini_session_secret.txt"
        if p.exists() and p.read_text(encoding="utf-8").strip():
            return p
    return None


def _users_file() -> Path | None:
    for d in _shared_data_candidates():
        p = d / "users.json"
        if p.exists():
            return p
    return None


def _current_user_id(request: Request) -> str | None:
    token = request.cookies.get("infini_session")
    secret_file = _session_secret_file()
    if not token or not secret_file:
        return None
    try:
        signer = URLSafeSerializer(secret_file.read_text(encoding="utf-8").strip(), salt="infini-session")
        payload = signer.loads(token)
    except (BadSignature, Exception):
        return None
    user_id = str(payload.get("user_id") or "").strip()
    if not user_id:
        return None

    users_file = _users_file()
    if users_file:
        try:
            users = json.loads(users_file.read_text(encoding="utf-8"))
            if isinstance(users, dict) and users and user_id not in users:
                return None
        except Exception:
            pass
    return user_id


def _user_paths(user_id: str) -> dict[str, Path]:
    root = USERS_ROOT / _safe_user_id(user_id)
    uploads = root / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "uploads": uploads,
        "library": root / "library.json",
        "draft": root / "draft.json",
    }


def _load_json(path: Path, fallback: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except Exception:
        return fallback


def _save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _claim_legacy_for_first_user(user_id: str) -> None:
    paths = _user_paths(user_id)
    if paths["library"].exists() or LEGACY_CLAIM.exists() or not LEGACY_DB.exists():
        return
    try:
        legacy = _load_json(LEGACY_DB, {"items": []})
        items = legacy.get("items", []) if isinstance(legacy, dict) else []
        claimed: list[dict[str, Any]] = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue
            item = dict(raw_item)
            stored = Path(str(item.get("stored") or item.get("url") or "")).name
            if stored and (LEGACY_UPLOADS / stored).exists():
                target = paths["uploads"] / stored
                if not target.exists():
                    shutil.copy2(LEGACY_UPLOADS / stored, target)
                item["stored"] = stored
                item["url"] = _public_url(stored)
            item["owner"] = user_id
            claimed.append(item)
        _save_json(paths["library"], {"items": claimed})
        LEGACY_CLAIM.write_text(user_id, encoding="utf-8")
    except Exception:
        pass


def _load_library(user_id: str) -> dict[str, Any]:
    _claim_legacy_for_first_user(user_id)
    data = _load_json(_user_paths(user_id)["library"], {"items": []})
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return {"items": []}
    return data


def _save_library(user_id: str, data: dict[str, Any]) -> None:
    _save_json(_user_paths(user_id)["library"], data)


def _load_draft(user_id: str) -> dict[str, Any]:
    value = _load_json(_user_paths(user_id)["draft"], {})
    return value if isinstance(value, dict) else {}


def _save_draft(user_id: str, data: dict[str, Any]) -> None:
    _save_json(_user_paths(user_id)["draft"], data)



def _system_scene_url(name: str) -> str:
    return f"/shop-scene-builder/system-file/{Path(name).name}"


def _load_system_scenes() -> list[dict[str, Any]]:
    """Load shared system scenes, seeding them from the old global scene library."""
    current = _load_json(SYSTEM_DB, {"items": []})
    items = current.get("items", []) if isinstance(current, dict) else []
    seen = {Path(str(x.get("stored") or "")).name for x in items if isinstance(x, dict)}
    changed = False

    legacy = _load_json(LEGACY_DB, {"items": []}) if LEGACY_DB.exists() else {"items": []}
    for raw in legacy.get("items", []) if isinstance(legacy, dict) else []:
        if not isinstance(raw, dict) or raw.get("kind") != "scene":
            continue
        stored = Path(str(raw.get("stored") or raw.get("url") or "")).name
        if not stored or stored in seen or not (LEGACY_UPLOADS / stored).exists():
            continue
        target = SYSTEM_UPLOADS / stored
        if not target.exists():
            shutil.copy2(LEGACY_UPLOADS / stored, target)
        items.append({
            "id": str(raw.get("id") or ("sys_" + uuid.uuid4().hex[:12])),
            "kind": "scene",
            "title": str(raw.get("title") or Path(stored).stem),
            "stored": stored,
            "url": _system_scene_url(stored),
            "scope": "system",
            "created_at": int(raw.get("created_at") or time.time()),
        })
        seen.add(stored)
        changed = True

    clean: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        stored = Path(str(raw.get("stored") or raw.get("url") or "")).name
        if not stored or not (SYSTEM_UPLOADS / stored).exists():
            continue
        item = dict(raw)
        item["kind"] = "scene"
        item["stored"] = stored
        item["url"] = _system_scene_url(stored)
        item["scope"] = "system"
        clean.append(item)
    if changed or clean != items or not SYSTEM_DB.exists():
        _save_json(SYSTEM_DB, {"items": clean})
    return clean


def _decode_png(data_url: str) -> bytes:
    if not isinstance(data_url, str) or not data_url:
        raise ValueError("missing image data")
    payload = data_url.split(",", 1)[1] if "," in data_url else data_url
    raw = base64.b64decode(payload, validate=False)
    if not raw:
        raise ValueError("empty image")
    if len(raw) > 35 * 1024 * 1024:
        raise ValueError("image too large")
    return raw


def _clean_filename(filename: str) -> tuple[str, str]:
    original = Path(filename or "image.jpg").name
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXTS:
        guessed = mimetypes.guess_extension(mimetypes.guess_type(original)[0] or "") or ".jpg"
        ext = guessed if guessed in ALLOWED_EXTS else ".jpg"
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(original).stem)[:50] or "image"
    return stem, ext


def _public_url(name: str) -> str:
    return f"/shop-scene-builder/file/{name}"


def _html(items: list[dict[str, Any]], draft: dict[str, Any], username: str, system_scenes: list[dict[str, Any]]) -> str:
    items_json = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    draft_json = json.dumps(draft, ensure_ascii=False).replace("</", "<\\/")
    username_json = json.dumps(username, ensure_ascii=False)
    system_json = json.dumps(system_scenes, ensure_ascii=False).replace("</", "<\\/")
    page = r'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>INFINI AI Shop Slot Editor</title>
<style>
:root{--bg:#070302;--panel:#0d0805;--line:#6a3518;--orange:#ff961e;--gold:#ffc35b;--text:#fff8ef;--muted:#bda38f}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}body{margin:0;background:radial-gradient(circle at top,#251007,#070302 48%,#000);color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}a{color:#ffd2a0;text-decoration:none}
.app{max-width:1180px;margin:auto;padding:12px 12px 122px}.top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px}.brand{font-weight:1000;font-size:22px;color:var(--orange);margin-right:auto}.who{font-size:12px;color:#d9b89b;border:1px solid #4f2d1c;border-radius:999px;padding:8px 11px}
.btn,.fileBtn{border:1px solid var(--line);background:#130b07;color:#ffe0bb;border-radius:15px;padding:11px 13px;font-weight:900;font-size:14px;cursor:pointer;text-align:center}.btn.primary{background:linear-gradient(135deg,#ffb52d,#ff8c13);color:#190900;border-color:#ffb52d}.btn.active{outline:2px solid var(--orange);background:#2a1208}.fileBtn input{display:none}
.layout{display:grid;grid-template-columns:330px minmax(0,1fr);gap:12px}.panel{border:1px solid var(--line);background:rgba(12,7,4,.94);border-radius:22px;padding:12px}h2{font-size:18px;color:var(--gold);margin:4px 0 10px}.note{font-size:13px;color:var(--muted);line-height:1.45;margin-bottom:10px}.warn{font-size:12px;color:#ffc976;border:1px solid #5b391e;background:#160d08;padding:9px;border-radius:12px;margin:8px 0}
.tabs,.tools{display:flex;gap:7px;flex-wrap:wrap;margin:8px 0}.tabs .btn,.tools .btn{flex:1;min-width:86px}.assets{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-height:300px;overflow:auto}.asset{border:1px solid #3a2418;background:#0a0908;border-radius:14px;padding:6px;cursor:pointer}.asset img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:10px;display:block}.asset div{font-size:11px;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#dbc4b0}
.canvasBox{background:#000;border:1px solid var(--line);border-radius:22px;padding:9px;overflow:hidden}canvas{display:block;width:100%;height:auto;background:#111;border-radius:15px;touch-action:none}.status{padding:9px 12px;border:1px solid #473020;border-radius:14px;color:#ffd6a4;background:#100906;margin-top:8px;font-size:13px}.row{display:flex;gap:8px;flex-wrap:wrap}.row>*{flex:1}input[type=text]{width:100%;padding:12px;border-radius:14px;border:1px solid var(--line);background:#090706;color:#fff;font:inherit}
.bottom{position:fixed;left:50%;bottom:10px;transform:translateX(-50%);width:min(1160px,calc(100% - 20px));display:flex;gap:8px;padding:9px;border:1px solid var(--line);border-radius:21px;background:rgba(8,4,2,.93);backdrop-filter:blur(14px);z-index:20}.bottom .btn{flex:1}.hidden{display:none!important}@media(max-width:760px){.layout{grid-template-columns:1fr}.assets{max-height:220px}.bottom{overflow-x:auto}.bottom .btn{min-width:118px}}
</style></head><body>
<div class="app"><div class="top"><div class="brand">∞ AI SHOP SLOT EDITOR</div><div class="who">คลังส่วนตัว: __USERNAME__</div><a class="btn" href="/id">ไอดีของฉัน</a><a class="btn" href="/">หน้าแรก</a></div>
<div class="layout"><aside class="panel">
<h2>1) ห้องฉากของระบบ</h2>
<div class="row"><button id="systemRoomBtn" class="btn primary" onclick="showSystemScenes()">เปิดฉากของระบบ</button><label class="fileBtn">ฉากส่วนตัว<input id="sceneFile" type="file" accept="image/*"></label></div>
<div class="warn">ฉากของระบบเป็นคลังกลางที่ทุกไอดีเลือกใช้ได้ ส่วนรูปสินค้าและงานของผู้ใช้แยกตามไอดีและไม่ปนกัน</div>
<h2>2) รูปส่วนตัวของไอดี</h2>
<div class="row"><label class="fileBtn">เพิ่มสินค้าหลายรูป<input id="bulkProductFile" type="file" accept="image/*" multiple></label><label class="fileBtn primary">AI จัดร้านให้<input id="aiProductFile" type="file" accept="image/*" multiple></label></div>
<div class="note">แตะช่องใดก็ได้ ระบบจะเปิดคลังรูปในเครื่องทันที เลือกรูปแล้วรูปจะลงช่องนั้น หรือเลือกหลายรูปด้วยปุ่ม AI เพื่อสร้างโปสเตอร์ดำ–ส้มอัตโนมัติ</div>
<input id="slotProductFile" class="hidden" type="file" accept="image/*">
<div class="tabs"><button id="tabProduct" class="btn active" onclick="setAssetTab('product')">สินค้าของฉัน</button><button id="tabGenerated" class="btn" onclick="setAssetTab('generated')">งานสำเร็จของฉัน</button></div><div id="assets" class="assets"></div>
<h2>3) ช่องและการแก้ไข</h2><div class="note">เครื่องมือส่วนนี้เก็บไว้เป็นโหมดละเอียด อนาคต AI จะเรียกใช้แทนผู้ใช้</div>
<div class="tools"><button class="btn" onclick="makeGridSlots(8)">สร้าง 8 ช่อง</button><button id="modeDraw" class="btn" onclick="setMode('draw')">วาดช่อง</button><button id="modeSelect" class="btn active" onclick="setMode('select')">เลือก/ย้าย</button><button id="modeImage" class="btn" onclick="setMode('image')">ลากรูปในช่อง</button></div>
<div class="tools"><button class="btn" onclick="addSlot()">+ ช่องใหม่</button><button class="btn" onclick="deleteSelected()">ลบชิ้นที่เลือก</button><button id="guideBtn" class="btn active" onclick="toggleGuides()">เส้นช่อง: เปิด</button></div>
<h2>รูปในช่อง</h2><div class="tools"><button class="btn" onclick="zoomSelected(.9)">รูป −</button><button class="btn" onclick="zoomSelected(1.1)">รูป +</button><button class="btn" onclick="setFit('contain')">พอดีช่อง</button><button class="btn" onclick="setFit('cover')">เต็มช่อง</button></div>
<h2>ข้อความ</h2><input id="textInput" type="text" placeholder="ชื่อร้าน ราคา หรือข้อความ"><div class="tools"><button class="btn primary" onclick="addText()">+ เพิ่มข้อความ</button><button class="btn" onclick="fontSize(.9)">ตัวเล็ก</button><button class="btn" onclick="fontSize(1.1)">ตัวใหญ่</button></div>
</aside>
<main><div class="panel"><h2>จัดร้านตามรูปสินค้าที่อัปโหลด</h2><div class="note">แตะช่อง → อัปโหลดรูป • ลากช่องเพื่อย้าย • จับมุมเพื่อขยาย • โหมดลากรูปใช้เลื่อนเสื้อภายในกรอบ</div><div class="canvasBox"><canvas id="c" width="900" height="1200"></canvas></div><div id="status" class="status">เลือกฉาก หรือสร้าง 8 ช่องก่อน</div><div style="margin-top:10px"><input id="saveTitle" type="text" value="ร้านที่จัดด้วย INFINI AI Shop"></div></div></main></div></div>
<div class="bottom"><button class="btn" onclick="undo()">ย้อนกลับ</button><button class="btn" onclick="saveDraft()">บันทึกแบบร่าง</button><button class="btn" onclick="downloadPng()">ดาวน์โหลด PNG</button><button class="btn primary" onclick="saveToLibrary()">บันทึกรูปเข้าคลัง</button></div>
<script>
let LIB=__ITEMS_JSON__;const SYSTEM_SCENES=__SYSTEM_SCENES__;const DRAFT=__DRAFT_JSON__;const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let bg=null,slots=[],texts=[],selectedType=null,selectedIndex=-1,assetTab='product',assetRoom='system',mode='select',guides=true,history=[],action=null,start=null,snap=null;const HANDLE=28,MIN=60;
function status(t){document.getElementById('status').textContent=t}function loadImg(src){return new Promise((ok,no)=>{const i=new Image();i.crossOrigin='anonymous';i.onload=()=>ok(i);i.onerror=no;i.src=src})}function esc(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
function showSystemScenes(){assetRoom='system';assetTab='scene';document.getElementById('systemRoomBtn').classList.add('active');['Product','Generated'].forEach(x=>{const e=document.getElementById('tab'+x);if(e)e.classList.remove('active')});renderAssets();status('เลือกฉากของระบบได้เลย')}
function setAssetTab(t){assetRoom='private';assetTab=t;document.getElementById('systemRoomBtn').classList.remove('active');['Product','Generated'].forEach(x=>{const e=document.getElementById('tab'+x);if(e)e.classList.toggle('active',x.toLowerCase()===t)});renderAssets()}
function renderAssets(){const box=document.getElementById('assets');box.innerHTML='';const list=(assetRoom==='system'?SYSTEM_SCENES:LIB.filter(x=>x.kind===assetTab)).slice().reverse();if(!list.length){box.innerHTML='<div class="note">'+(assetRoom==='system'?'ยังไม่มีฉากในห้องระบบ':'คลังส่วนตัวหมวดนี้ยังว่าง')+'</div>';return}list.forEach(item=>{const d=document.createElement('div');d.className='asset';d.innerHTML='<img src="'+esc(item.url||'')+'"><div>'+esc(item.title||'รูป')+'</div>';d.onclick=()=>useAsset(item);box.appendChild(d)})}
async function useAsset(item){try{const img=await loadImg(item.url);if(item.kind==='scene'){pushHistory();bg=img;fitCanvas(img);if(!slots.length)makeGridSlots(8,false);status('เลือกฉากแล้ว')}else assignToSlot(img,item.url);draw()}catch(e){status('เปิดรูปนี้ไม่ได้')}}
async function uploadFiles(files,kind){if(!files||!files.length)return[];const fd=new FormData();for(const f of files)fd.append('files',f);fd.append('kind',kind);const r=await fetch('/shop-scene-builder/upload',{method:'POST',body:fd});const d=await r.json();if(!r.ok||!d.ok)throw new Error(d.error||'upload failed');LIB.push(...d.items);renderAssets();return d.items}
document.getElementById('sceneFile').onchange=async e=>{try{const items=await uploadFiles(e.target.files,'scene');if(items[0])await useAsset(items[0])}catch(err){status('อัปฉากไม่สำเร็จ: '+err.message)}e.target.value=''};
document.getElementById('slotProductFile').onchange=async e=>{try{const items=await uploadFiles(e.target.files,'product');if(items[0])await useAsset(items[0])}catch(err){status('อัปสินค้าไม่สำเร็จ: '+err.message)}e.target.value=''};
document.getElementById('bulkProductFile').onchange=async e=>{try{status('กำลังอัปหลายรูป...');const items=await uploadFiles(e.target.files,'product');await autoArrangeItems(items)}catch(err){status('จัดอัตโนมัติไม่สำเร็จ: '+err.message)}e.target.value=''};
document.getElementById('aiProductFile').onchange=async e=>{try{status('กำลังสร้างโปสเตอร์ AI...');const items=await uploadFiles(e.target.files,'product');await aiPoster(items)}catch(err){status('AI จัดร้านไม่สำเร็จ: '+err.message)}e.target.value=''};
function fitCanvas(img){const sc=Math.min(1200/img.width,1600/img.height,1);canvas.width=Math.max(420,Math.round(img.width*sc));canvas.height=Math.max(560,Math.round(img.height*sc))}
function newSlot(x,y,w,h){return{x,y,w,h,img:null,src:'',scale:1,offsetX:0,offsetY:0,fit:'contain'}}
function makeGridSlots(count=8,remember=true){if(remember)pushHistory();count=Math.max(1,Math.min(40,count));const cols=count<=2?count:count<=6?3:4;const rows=Math.ceil(count/cols);const mx=canvas.width*.06,gap=canvas.width*.018;const top=canvas.height*.43,bottom=canvas.height*.05;const availW=canvas.width-mx*2-gap*(cols-1),availH=canvas.height-top-bottom-gap*(rows-1);const w=availW/cols,h=availH/rows;slots=[];for(let i=0;i<count;i++){const c=i%cols,r=Math.floor(i/cols);slots.push(newSlot(mx+c*(w+gap),top+r*(h+gap),w,h))}selectedType='slot';selectedIndex=0;draw();status('สร้าง '+count+' ช่องแล้ว แตะช่องว่างเพื่ออัปโหลดสินค้า')}
function addSlot(){pushHistory();slots.push(newSlot(canvas.width*.35,canvas.height*.45,canvas.width*.25,canvas.height*.25));selectedType='slot';selectedIndex=slots.length-1;draw();status('เพิ่มช่องแล้ว แตะรูปเพื่อใส่')}
function assignToSlot(img,src){if(selectedType!=='slot'||selectedIndex<0){const empty=slots.findIndex(s=>!s.img);if(empty>=0){selectedType='slot';selectedIndex=empty}else{status('แตะช่องในฉากก่อน แล้วค่อยเลือกรูป');return}}pushHistory();const s=slots[selectedIndex];s.img=img;s.src=src||'';s.scale=1;s.offsetX=0;s.offsetY=0;s.fit='contain';draw();status('ใส่รูปลงช่อง '+(selectedIndex+1)+' แล้ว')}
async function autoArrangeItems(items){if(!items.length)return;if(slots.length<items.length)makeGridSlots(items.length,false);pushHistory();for(let i=0;i<items.length;i++){try{const img=await loadImg(items[i].url);const s=slots[i];s.img=img;s.src=items[i].url;s.scale=1;s.offsetX=0;s.offsetY=0;s.fit='contain'}catch(e){}}selectedType='slot';selectedIndex=0;draw();status('จัดสินค้า '+items.length+' รูปลงร้านอัตโนมัติแล้ว ปรับตำแหน่งต่อได้')}
async function makePosterBackground(){
  const t=document.createElement('canvas');t.width=1080;t.height=1440;const g=t.getContext('2d');
  const grad=g.createRadialGradient(540,180,80,540,720,950);grad.addColorStop(0,'#211006');grad.addColorStop(.42,'#090807');grad.addColorStop(1,'#000');g.fillStyle=grad;g.fillRect(0,0,t.width,t.height);
  g.strokeStyle='#5d5d5d';g.lineWidth=2;g.fillStyle='#fff';g.font='900 78px system-ui';g.fillText('INFINI',34,92);g.fillStyle='#ff9228';g.font='700 25px system-ui';g.fillText('SMART PRODUCT STORY',38,130);
  g.fillStyle='#fff';g.font='800 25px system-ui';g.fillText('สินค้าของคุณ จัดเป็นเรื่องราวได้ในครั้งเดียว',38,169);
  const feats=['ภาพหลักเด่นชัด','จัดวางอัตโนมัติ','ปรับแก้ต่อได้','บันทึกเป็นภาพ'];g.font='800 24px system-ui';
  feats.forEach((x,i)=>{const y=235+i*74;g.strokeStyle='#ff9228';g.beginPath();g.arc(55,y-8,18,0,Math.PI*2);g.stroke();g.fillStyle='#fff';g.fillText(x,88,y)});
  function panel(x,y,w,h,title=''){g.strokeStyle='#6a6a6a';g.lineWidth=2;g.beginPath();g.roundRect(x,y,w,h,18);g.stroke();if(title){g.fillStyle='#ff9228';g.font='800 26px system-ui';g.fillText(title,x+18,y+38)}}
  panel(270,190,555,450,'ภาพหลัก');panel(835,60,210,210,'รายละเอียด');panel(30,660,500,285,'มุมสินค้า');panel(550,660,500,285,'วิธีใช้');panel(30,970,320,300,'ดีไซน์');panel(380,970,320,300,'วัสดุ');panel(730,970,320,300,'ตัวเลือก');
  g.fillStyle='#fff';g.font='900 39px system-ui';g.fillText('สินค้าธรรมดา... ที่ไม่ธรรมดา',34,1345);g.fillStyle='#ff9228';g.font='700 21px system-ui';g.fillText('INFINI • UPLOAD • ARRANGE • CREATE',38,1383);
  return await loadImg(t.toDataURL('image/png'));
}
async function aiPoster(items){
  if(!items.length){status('เลือกรูปสินค้าอย่างน้อย 1 รูป');return}
  pushHistory();canvas.width=1080;canvas.height=1440;bg=await makePosterBackground();texts=[];
  const boxes=[[285,215,525,405],[850,82,180,165],[48,710,465,215],[568,710,465,215],[48,1025,285,220],[398,1025,285,220],[748,1025,285,220]];
  slots=boxes.map(b=>newSlot(...b));
  for(let i=0;i<Math.min(items.length,slots.length);i++){
    try{const img=await loadImg(items[i].url);Object.assign(slots[i],{img,src:items[i].url,fit:'contain',scale:1,offsetX:0,offsetY:0})}catch(e){}
  }
  selectedType='slot';selectedIndex=0;guides=false;draw();status('AI จัดร้านแบบโปสเตอร์ดำ–ส้มให้แล้ว แก้ช่องต่อได้');
}
function setMode(m){mode=m;['Select','Draw','Image'].forEach(x=>document.getElementById('mode'+x).classList.toggle('active',x.toLowerCase()===m));status(m==='draw'?'ลากนิ้วครอบช่องจริงในฉาก':m==='image'?'แตะช่องแล้วลากรูปข้างใน':'แตะชิ้นงาน ลากเพื่อย้าย หรือจับมุมเพื่อขยาย')}
function addText(){const v=document.getElementById('textInput').value.trim();if(!v){status('พิมพ์ข้อความก่อน');return}pushHistory();texts.push({x:canvas.width*.08,y:canvas.height*.08,w:canvas.width*.65,h:80,text:v,size:42});selectedType='text';selectedIndex=texts.length-1;mode='select';draw();status('เพิ่มข้อความแล้ว')}
function current(){return selectedType==='slot'?slots[selectedIndex]:selectedType==='text'?texts[selectedIndex]:null}function toggleGuides(){guides=!guides;const b=document.getElementById('guideBtn');b.textContent='เส้นช่อง: '+(guides?'เปิด':'ปิด');b.classList.toggle('active',guides);draw()}
function zoomSelected(f){if(selectedType!=='slot')return;const s=slots[selectedIndex];if(!s||!s.img)return;pushHistory();s.scale=Math.max(.1,Math.min(8,s.scale*f));draw()}function setFit(f){if(selectedType!=='slot')return;const s=slots[selectedIndex];if(!s)return;pushHistory();s.fit=f;s.scale=1;s.offsetX=0;s.offsetY=0;draw()}function fontSize(f){if(selectedType!=='text')return;const t=texts[selectedIndex];pushHistory();t.size=Math.max(16,Math.min(140,t.size*f));t.h=Math.max(50,t.size*1.45);draw()}
function deleteSelected(){if(selectedIndex<0)return;pushHistory();if(selectedType==='slot')slots.splice(selectedIndex,1);else if(selectedType==='text')texts.splice(selectedIndex,1);selectedType=null;selectedIndex=-1;draw();status('ลบแล้ว')}
function rr(x,y,w,h,r){r=Math.min(r,w/2,h/2);ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}function drawCover(img,x,y,w,h){const sc=Math.max(w/img.width,h/img.height),dw=img.width*sc,dh=img.height*sc;ctx.drawImage(img,x+(w-dw)/2,y+(h-dh)/2,dw,dh)}
function handles(o){ctx.fillStyle='#ff981f';[[o.x,o.y],[o.x+o.w,o.y],[o.x,o.y+o.h],[o.x+o.w,o.y+o.h]].forEach(([x,y])=>{ctx.beginPath();ctx.arc(x,y,HANDLE/2,0,Math.PI*2);ctx.fill()})}
function drawSlot(s,i){ctx.save();rr(s.x,s.y,s.w,s.h,14);ctx.clip();ctx.fillStyle='rgba(0,0,0,.2)';ctx.fillRect(s.x,s.y,s.w,s.h);if(s.img){const base=s.fit==='cover'?Math.max(s.w/s.img.width,s.h/s.img.height):Math.min(s.w/s.img.width,s.h/s.img.height),dw=s.img.width*base*s.scale,dh=s.img.height*base*s.scale,cx=s.x+s.w/2+s.offsetX,cy=s.y+s.h/2+s.offsetY;ctx.drawImage(s.img,cx-dw/2,cy-dh/2,dw,dh)}else{ctx.fillStyle='rgba(255,195,91,.18)';ctx.font='900 '+Math.max(18,Math.min(34,s.w*.08))+'px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('+ แตะใส่สินค้า',s.x+s.w/2,s.y+s.h/2);ctx.textAlign='start'}ctx.restore();if(guides||selectedType==='slot'&&selectedIndex===i){ctx.save();rr(s.x,s.y,s.w,s.h,14);ctx.strokeStyle=selectedType==='slot'&&selectedIndex===i?'#ff981f':'rgba(255,195,91,.72)';ctx.lineWidth=selectedType==='slot'&&selectedIndex===i?5:2;ctx.setLineDash(selectedType==='slot'&&selectedIndex===i?[]:[10,7]);ctx.stroke();ctx.setLineDash([]);if(selectedType==='slot'&&selectedIndex===i)handles(s);ctx.restore()}}
function drawText(t,i){ctx.save();ctx.font='900 '+t.size+'px system-ui';ctx.textBaseline='middle';ctx.fillStyle='#fff';ctx.shadowColor='rgba(0,0,0,.8)';ctx.shadowBlur=8;ctx.fillText(t.text,t.x+10,t.y+t.h/2);ctx.shadowBlur=0;if(selectedType==='text'&&selectedIndex===i){ctx.strokeStyle='#ff981f';ctx.lineWidth=4;ctx.strokeRect(t.x,t.y,t.w,t.h);handles(t)}ctx.restore()}function draw(){ctx.clearRect(0,0,canvas.width,canvas.height);if(bg)drawCover(bg,0,0,canvas.width,canvas.height);else{ctx.fillStyle='#140905';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#ff981f';ctx.font='bold 42px system-ui';ctx.textAlign='center';ctx.fillText('เลือกฉากร้าน',canvas.width/2,120);ctx.textAlign='start'}slots.forEach(drawSlot);texts.forEach(drawText)}
function point(ev){const r=canvas.getBoundingClientRect();return{x:(ev.clientX-r.left)*canvas.width/r.width,y:(ev.clientY-r.top)*canvas.height/r.height}}function inside(o,p){return p.x>=o.x&&p.x<=o.x+o.w&&p.y>=o.y&&p.y<=o.y+o.h}function hitSlot(p){for(let i=slots.length-1;i>=0;i--)if(inside(slots[i],p))return i;return-1}function hitText(p){for(let i=texts.length-1;i>=0;i--)if(inside(texts[i],p))return i;return-1}
function corner(o,p){for(const [n,x,y] of [['nw',o.x,o.y],['ne',o.x+o.w,o.y],['sw',o.x,o.y+o.h],['se',o.x+o.w,o.y+o.h]])if(Math.hypot(p.x-x,p.y-y)<=HANDLE*1.4)return n;return null}function clamp(o){o.x=Math.max(0,Math.min(canvas.width-o.w,o.x));o.y=Math.max(0,Math.min(canvas.height-o.h,o.y))}
let tapWasEmpty=false;canvas.onpointerdown=ev=>{const p=point(ev);start=p;action=null;snap=null;tapWasEmpty=false;if(mode==='draw'){pushHistory();slots.push(newSlot(p.x,p.y,1,1));selectedType='slot';selectedIndex=slots.length-1;action='draw'}else{let i=hitSlot(p),ti=hitText(p);if(i>=0){selectedType='slot';selectedIndex=i;const s=slots[i];const co=corner(s,p);tapWasEmpty=(mode==='select'&&!co);pushHistory();snap={...s};action=mode==='image'?'image':co?'resize:'+co:'move'}else if(ti>=0){selectedType='text';selectedIndex=ti;pushHistory();const t=texts[ti];snap={...t};action=corner(t,p)?'resize:'+corner(t,p):'move'}else{selectedType=null;selectedIndex=-1}}canvas.setPointerCapture(ev.pointerId);draw()}
canvas.onpointermove=ev=>{if(!action)return;const p=point(ev),dx=p.x-start.x,dy=p.y-start.y;if(Math.abs(dx)+Math.abs(dy)>10)tapWasEmpty=false;if(action==='draw'){const s=slots[selectedIndex];s.x=Math.min(start.x,p.x);s.y=Math.min(start.y,p.y);s.w=Math.abs(p.x-start.x);s.h=Math.abs(p.y-start.y)}else{const o=current();if(!o)return;if(action==='move'){o.x=snap.x+dx;o.y=snap.y+dy;clamp(o)}else if(action==='image'){o.offsetX=snap.offsetX+dx;o.offsetY=snap.offsetY+dy}else if(action.startsWith('resize:')){const co=action.split(':')[1];let x=snap.x,y=snap.y,w=snap.w,h=snap.h;if(co.includes('e'))w=Math.max(MIN,snap.w+dx);if(co.includes('s'))h=Math.max(MIN,snap.h+dy);if(co.includes('w')){x=Math.min(snap.x+snap.w-MIN,snap.x+dx);w=snap.x+snap.w-x}if(co.includes('n')){y=Math.min(snap.y+snap.h-MIN,snap.y+dy);h=snap.y+snap.h-y}o.x=x;o.y=y;o.w=w;o.h=h;clamp(o);if(selectedType==='text')o.size=Math.max(16,Math.min(140,o.h*.58))}}draw()}
canvas.onpointerup=()=>{if(action==='draw'){const s=slots[selectedIndex];if(s.w<MIN||s.h<MIN){slots.splice(selectedIndex,1);selectedType=null;selectedIndex=-1;status('ช่องเล็กเกินไป ลองวาดใหม่')}else status('สร้างช่องแล้ว แตะช่องนี้เพื่ออัปโหลดรูป')}else if(tapWasEmpty&&selectedType==='slot'){setTimeout(()=>document.getElementById('slotProductFile').click(),50)}action=null;tapWasEmpty=false;draw()};canvas.onpointercancel=()=>{action=null;tapWasEmpty=false;draw()};
function state(){return{bgSrc:bg?bg.src:null,width:canvas.width,height:canvas.height,slots:slots.map(s=>({x:s.x,y:s.y,w:s.w,h:s.h,src:s.src,scale:s.scale,offsetX:s.offsetX,offsetY:s.offsetY,fit:s.fit})),texts:texts.map(t=>({...t}))}}function pushHistory(){history.push(state());if(history.length>25)history.shift()}async function applyState(h){if(!h||typeof h!=='object')return;if(h.width)canvas.width=h.width;if(h.height)canvas.height=h.height;bg=h.bgSrc?await loadImg(h.bgSrc).catch(()=>null):null;slots=[];for(const s of h.slots||[]){const n={...s,img:null};if(s.src)n.img=await loadImg(s.src).catch(()=>null);slots.push(n)}texts=h.texts||[];selectedType=null;selectedIndex=-1;draw()}async function undo(){const h=history.pop();if(!h)return;await applyState(h);status('ย้อนกลับแล้ว')}
function cleanData(){const g=guides,st=selectedType,si=selectedIndex;guides=false;selectedType=null;selectedIndex=-1;draw();const d=canvas.toDataURL('image/png');guides=g;selectedType=st;selectedIndex=si;draw();return d}function downloadPng(){const a=document.createElement('a');a.href=cleanData();a.download='infini-ai-shop.png';a.click();status('ดาวน์โหลด PNG แล้ว')}
async function saveDraft(){try{const r=await fetch('/shop-scene-builder/draft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state())});const d=await r.json();if(!r.ok||!d.ok)throw new Error(d.error||'save failed');status('บันทึกแบบร่างส่วนตัวแล้ว')}catch(e){status('บันทึกแบบร่างไม่สำเร็จ: '+e.message)}}
async function saveToLibrary(){try{status('กำลังบันทึก...');const res=await fetch('/shop-scene-builder/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:document.getElementById('saveTitle').value,image_data:cleanData()})});const data=await res.json();if(!res.ok||!data.ok)throw new Error(data.error||'save failed');LIB.push(data.item);renderAssets();status('บันทึกรูปเข้าคลังส่วนตัวแล้ว')}catch(e){status('บันทึกไม่สำเร็จ: '+e.message)}}
async function init(){showSystemScenes();if(DRAFT&&Object.keys(DRAFT).length){await applyState(DRAFT);status('เปิดแบบร่างล่าสุดแล้ว')}else{makeGridSlots(8,false);status('สร้าง 8 ช่องให้แล้ว เลือกฉากหรือแตะช่องเพื่อใส่สินค้า')}}init();
</script></body></html>'''
    return (
        page.replace("__ITEMS_JSON__", items_json)
        .replace("__DRAFT_JSON__", draft_json)
        .replace("__SYSTEM_SCENES__", system_json)
        .replace("__USERNAME__", username_json[1:-1])
    )


class _RedirectOldAiShopMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.rstrip("/") == "/ai-shop":
            return RedirectResponse("/shop-scene-builder", status_code=307)
        return await call_next(request)


def install_shop_scene_slots_7000(app) -> None:
    marker = "_infini_shop_scene_slots_v4"
    if getattr(app.state, marker, False):
        return
    setattr(app.state, marker, True)
    app.add_middleware(_RedirectOldAiShopMiddleware)

    async def page(request: Request):
        user_id = _current_user_id(request)
        if not user_id:
            return RedirectResponse("/id", status_code=303)
        items = _load_library(user_id).get("items", [])
        users_file = _users_file()
        username = user_id
        if users_file:
            try:
                users = json.loads(users_file.read_text(encoding="utf-8"))
                username = str(users.get(user_id, {}).get("username") or user_id)
            except Exception:
                pass
        return HTMLResponse(_html(items, _load_draft(user_id), username, _load_system_scenes()))

    async def upload(
        request: Request,
        files: list[UploadFile] = File(...),
        kind: str = Form("product"),
    ) -> JSONResponse:
        user_id = _current_user_id(request)
        if not user_id:
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)
        kind = kind if kind in {"product", "scene", "generated"} else "product"
        paths = _user_paths(user_id)
        data = _load_library(user_id)
        created: list[dict[str, Any]] = []
        for f in files[:60]:
            raw = await f.read()
            if not raw:
                continue
            if len(raw) > MAX_UPLOAD_BYTES:
                continue
            stem, ext = _clean_filename(f.filename or "image.jpg")
            stored = f"{kind}_{stem}_{uuid.uuid4().hex[:12]}{ext}"
            (paths["uploads"] / stored).write_bytes(raw)
            item = {
                "id": "img_" + uuid.uuid4().hex[:12],
                "kind": kind,
                "title": Path(f.filename or stored).stem,
                "stored": stored,
                "url": _public_url(stored),
                "created_at": int(time.time()),
                "source": MODULE_NAME,
                "owner": user_id,
            }
            data.setdefault("items", []).append(item)
            created.append(item)
        _save_library(user_id, data)
        return JSONResponse({"ok": True, "items": created})

    async def file_route(request: Request, name: str):
        user_id = _current_user_id(request)
        if not user_id:
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)
        safe = Path(name).name
        target = _user_paths(user_id)["uploads"] / safe
        if not target.exists() or not target.is_file():
            return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
        return FileResponse(target, headers={"Cache-Control": "private, no-store"})

    async def system_file_route(request: Request, name: str):
        if not _current_user_id(request):
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)
        safe = Path(name).name
        target = SYSTEM_UPLOADS / safe
        if not target.exists() or not target.is_file():
            return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
        return FileResponse(target, headers={"Cache-Control": "public, max-age=3600"})

    async def save(request: Request) -> JSONResponse:
        user_id = _current_user_id(request)
        if not user_id:
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)
        try:
            payload = await request.json()
            title = str(payload.get("title") or "ร้านที่จัดด้วย INFINI AI Shop").strip()
            raw = _decode_png(str(payload.get("image_data") or ""))
            stored = "generated_shop_" + uuid.uuid4().hex + ".png"
            paths = _user_paths(user_id)
            (paths["uploads"] / stored).write_bytes(raw)
            item = {
                "id": "img_" + uuid.uuid4().hex[:12],
                "kind": "generated",
                "title": title or "ร้านที่จัดด้วย INFINI AI Shop",
                "stored": stored,
                "url": _public_url(stored),
                "created_at": int(time.time()),
                "source": MODULE_NAME,
                "owner": user_id,
            }
            data = _load_library(user_id)
            data.setdefault("items", []).append(item)
            _save_library(user_id, data)
            return JSONResponse({"ok": True, "item": item})
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

    async def get_draft(request: Request) -> JSONResponse:
        user_id = _current_user_id(request)
        if not user_id:
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)
        return JSONResponse({"ok": True, "draft": _load_draft(user_id)})

    async def save_draft(request: Request) -> JSONResponse:
        user_id = _current_user_id(request)
        if not user_id:
            return JSONResponse({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, status_code=401)
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise ValueError("invalid draft")
            encoded = json.dumps(payload, ensure_ascii=False)
            if len(encoded) > 2_500_000:
                raise ValueError("draft too large")
            _save_draft(user_id, payload)
            return JSONResponse({"ok": True})
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

    app.add_api_route("/shop-scene-builder", page, methods=["GET"], response_class=HTMLResponse, name="shop_scene_slots_page_v4")
    app.add_api_route("/shop-scene-builder/upload", upload, methods=["POST"], response_class=JSONResponse, name="shop_scene_slots_upload_v4")
    app.add_api_route("/shop-scene-builder/file/{name}", file_route, methods=["GET"], name="shop_scene_slots_file_v4")
    app.add_api_route("/shop-scene-builder/system-file/{name}", system_file_route, methods=["GET"], name="shop_scene_slots_system_file_v4")
    app.add_api_route("/shop-scene-builder/save", save, methods=["POST"], response_class=JSONResponse, name="shop_scene_slots_save_v4")
    app.add_api_route("/shop-scene-builder/draft", get_draft, methods=["GET"], response_class=JSONResponse, name="shop_scene_slots_draft_get_v4")
    app.add_api_route("/shop-scene-builder/draft", save_draft, methods=["POST"], response_class=JSONResponse, name="shop_scene_slots_draft_save_v4")
