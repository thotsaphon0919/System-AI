from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib import request as urlrequest, error as urlerror
import base64
import json
import os
import time
import uuid

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from itsdangerous import BadSignature, URLSafeSerializer

BASE = Path(__file__).resolve().parent
SETTINGS_ROOT = BASE / "data" / "image_generator_users"
SHOP_USERS_ROOT = BASE / "data" / "shop_scene_users"
SETTINGS_ROOT.mkdir(parents=True, exist_ok=True)


def _safe(s: str) -> str:
    return "".join(c for c in str(s) if c.isalnum() or c in "-_")[:80] or "member"


def _shared_candidates():
    return [BASE.parent / "data", BASE / "data", Path(os.getenv("INFINI_8032_ROOT", str(BASE.parent / "8032"))).expanduser() / "data"]


def _current_user(request: Request) -> str | None:
    token=request.cookies.get("infini_session")
    if not token: return None
    secret=""
    users=None
    for d in _shared_candidates():
        sf=d/"infini_session_secret.txt"
        uf=d/"users.json"
        if sf.exists() and not secret:
            try: secret=sf.read_text(encoding="utf-8").strip()
            except Exception: pass
        if uf.exists() and users is None:
            try:
                x=json.loads(uf.read_text(encoding="utf-8")); users=x if isinstance(x,dict) else None
            except Exception: pass
    if not secret: secret=os.getenv("INFINI_SESSION_SECRET","").strip()
    if not secret: return None
    try: payload=URLSafeSerializer(secret,salt="infini-session").loads(token)
    except (BadSignature,Exception): return None
    uid=str((payload or {}).get("user_id") or "").strip()
    if users and uid not in users: return None
    return uid or None


def _settings_path(uid: str) -> Path: return SETTINGS_ROOT / f"{_safe(uid)}.json"

def _load_settings(uid: str) -> dict:
    try:
        d=json.loads(_settings_path(uid).read_text(encoding="utf-8")); return d if isinstance(d,dict) else {}
    except Exception: return {}

def _save_settings(uid: str,d:dict):
    p=_settings_path(uid);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(".tmp");tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");tmp.replace(p)


def _characters_path(uid: str) -> Path: return SETTINGS_ROOT / f"{_safe(uid)}.characters.json"

def _load_characters(uid: str) -> list[dict]:
    try:
        d=json.loads(_characters_path(uid).read_text(encoding="utf-8"))
        return d if isinstance(d,list) else []
    except Exception: return []

def _save_characters(uid: str, items: list[dict]):
    p=_characters_path(uid);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(".tmp");tmp.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8");tmp.replace(p)


def _http_json(url:str, payload:dict, headers:dict, timeout=120) -> dict:
    body=json.dumps(payload).encode("utf-8")
    req=urlrequest.Request(url,data=body,headers={"Content-Type":"application/json",**headers},method="POST")
    with urlrequest.urlopen(req,timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def _openai_image(key:str,prompt:str)->bytes:
    data=_http_json("https://api.openai.com/v1/images/generations",{"model":"gpt-image-2","prompt":prompt,"size":"1024x1024"},{"Authorization":"Bearer "+key})
    row=(data.get("data") or [{}])[0]
    if row.get("b64_json"): return base64.b64decode(row["b64_json"])
    if row.get("url"):
        with urlrequest.urlopen(row["url"],timeout=120) as res: return res.read()
    raise ValueError("API ไม่ส่งรูปกลับมา")


def _gemini_image(key:str,prompt:str)->bytes:
    # Endpoint is isolated here so it can be changed without touching UI/state.
    model=os.getenv("INFINI_GEMINI_IMAGE_MODEL","gemini-3.1-flash-image")
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    data=_http_json(url,{"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseModalities":["TEXT","IMAGE"]}}, {})
    for cand in data.get("candidates") or []:
        for part in ((cand.get("content") or {}).get("parts") or []):
            inline=part.get("inlineData") or part.get("inline_data") or {}
            if inline.get("data"): return base64.b64decode(inline["data"])
    raise ValueError("Gemini ไม่ส่งรูปกลับมา")


def _shop_paths(uid:str):
    root=SHOP_USERS_ROOT/_safe(uid);uploads=root/"uploads";uploads.mkdir(parents=True,exist_ok=True);return root,uploads,root/"library.json"

def _save_to_shop_library(uid:str, raw:bytes, title:str)->dict:
    root,uploads,libp=_shop_paths(uid);stored="generated_api_"+uuid.uuid4().hex+".png";(uploads/stored).write_bytes(raw)
    try:d=json.loads(libp.read_text(encoding="utf-8"));d=d if isinstance(d,dict) else {"items":[]}
    except Exception:d={"items":[]}
    item={"id":"img_"+uuid.uuid4().hex[:12],"kind":"generated","title":title or "AI Generated Image","stored":stored,"url":"/shop-scene-builder/file/"+stored,"created_at":int(time.time()),"source":"INFINI_IMAGE_GENERATOR","owner":uid}
    d.setdefault("items",[]).append(item);tmp=libp.with_suffix(".tmp");tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");tmp.replace(libp);return item

PAGE=r'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>INFINI Image Generator</title><style>*{box-sizing:border-box}html,body{margin:0;background:#030303;color:#fff;font-family:system-ui}.wrap{max-width:760px;margin:auto;padding:18px 14px 100px}.top{display:flex;align-items:center;justify-content:space-between}.back{color:#ffc17d;text-decoration:none;border:1px solid #744016;border-radius:999px;padding:9px 13px}.hero{margin-top:16px;border:1px solid rgba(255,139,31,.4);border-radius:28px;padding:18px;background:#090705}.ey{color:#ff941f;font-size:11px;font-weight:1000;letter-spacing:.12em}h1{margin:6px 0 14px;font-size:32px}.api{display:grid;grid-template-columns:1fr 1.25fr;gap:10px}.field label{display:block;color:#baa99b;font-size:12px;margin-bottom:6px}select,input,textarea{width:100%;border:1px solid #4a2a18;border-radius:15px;background:#040404;color:#fff;padding:13px;font:inherit;outline:none}textarea{min-height:140px;resize:vertical}.prompt{margin-top:14px}.actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}.btn{border:1px solid #754018;border-radius:17px;padding:14px;background:#080808;color:#ffc17d;font-weight:1000}.btn.primary{background:#ff941f;color:#140700;border:0}.status{color:#aaa;font-size:12px;margin-top:10px;min-height:20px}.result{margin-top:16px;border:1px solid #3d2719;border-radius:24px;min-height:260px;overflow:hidden;display:grid;place-items:center;background:#000}.result img{width:100%;height:auto;display:block}.links{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}.links a{color:#ffc17d;text-decoration:none;border:1px solid #70401f;border-radius:999px;padding:9px 12px}
.charBox{margin-top:16px;border:1px solid rgba(255,139,31,.4);border-radius:22px;padding:16px;background:#090705}
.charList{display:flex;flex-direction:column;gap:8px;margin:10px 0}
.charRow{display:flex;align-items:center;gap:10px;border:1px solid #3d2719;border-radius:14px;padding:10px 12px;cursor:pointer}
.charRow.active{border-color:#ff941f;background:rgba(255,148,31,.08)}
.charRow input[type=checkbox]{width:18px;height:18px;accent-color:#ff941f}
.charRow .cname{flex:1;font-weight:800}
.charRow .cdel{color:#a55;font-size:12px;background:none;border:0;cursor:pointer}
@media(max-width:520px){.api{grid-template-columns:1fr}.actions{grid-template-columns:1fr}}</style></head><body><main class="wrap"><div class="top"><b>∞ IMAGE GENERATOR</b><a class="back" href="/id">← ID</a></div>
<section class="charBox"><div class="ey">ตัวละครของฉัน</div><h1 style="font-size:20px;margin:6px 0 12px">เลือกตัวละครให้ภาพหน้าเดิมทุกครั้ง</h1>
<div class="charList" id="charList"></div>
<div class="field"><label>ชื่อตัวละคร</label><input id="charName" placeholder="เช่น Simonlaeng"></div>
<div class="field" style="margin-top:8px"><label>คำอธิบายหน้าตา/ลักษณะ (จะแปะเข้า prompt ทุกครั้งที่เลือก)</label><textarea id="charDesc" style="min-height:80px" placeholder="เช่น ผู้ชายไทยวัย 40 ผมสั้นหยิกสีดำ หน้าเหลี่ยม ใส่เสื้อหนัง สไตล์ร็อค"></textarea></div>
<button class="btn" id="charSave" style="margin-top:10px;width:100%">+ บันทึกตัวละครนี้</button>
</section>
<section class="hero"><div class="ey">API SETTINGS</div><h1>สร้างภาพ</h1><div class="api"><div class="field"><label>เลือกค่าย</label><select id="provider"><option value="openai">OpenAI</option><option value="gemini">Google Gemini</option></select></div><div class="field"><label>API Key</label><input id="key" type="password" placeholder="••••••••"></div></div><div class="field prompt"><label>Prompt</label><textarea id="prompt" placeholder="พิมพ์ภาพที่ต้องการสร้าง..."></textarea></div><div class="actions"><button class="btn" id="save">บันทึก API</button><button class="btn primary" id="gen">สร้างภาพ</button></div><div class="status" id="status"></div><div class="result" id="result"><span style="color:#555">รูปที่สร้างจะแสดงตรงนี้</span></div><div class="links"><a href="/shop-scene-builder">AI จัดร้าน V4 →</a><a href="/ai-chat">AI / Voice →</a></div></section></main><script>const $=x=>document.getElementById(x);let CHARACTERS=[],SELECTED_CHAR=null;
async function loadChars(){CHARACTERS=await fetch('/api/image-generator/characters').then(r=>r.json()).then(d=>d.items||[]);renderChars()}
function renderChars(){const box=$('charList');box.innerHTML='';if(!CHARACTERS.length){box.innerHTML='<div style="color:#776;font-size:12px">ยังไม่มีตัวละครที่บันทึกไว้</div>';return}
CHARACTERS.forEach(c=>{const row=document.createElement('div');row.className='charRow'+(SELECTED_CHAR===c.id?' active':'');row.innerHTML=`<input type="checkbox" ${SELECTED_CHAR===c.id?'checked':''}><span class="cname">${c.name}</span><button class="cdel" type="button">ลบ</button>`;
row.querySelector('input').addEventListener('change',e=>{SELECTED_CHAR=e.target.checked?c.id:null;renderChars()});
row.querySelector('.cdel').addEventListener('click',async e=>{e.stopPropagation();await fetch('/api/image-generator/characters/'+c.id,{method:'DELETE'});if(SELECTED_CHAR===c.id)SELECTED_CHAR=null;await loadChars()});
box.appendChild(row)})}
$('charSave').onclick=async()=>{const name=$('charName').value.trim(),desc=$('charDesc').value.trim();if(!name||!desc){$('status').textContent='ใส่ชื่อและคำอธิบายตัวละครก่อน';return}
const d=await fetch('/api/image-generator/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,description:desc})}).then(r=>r.json());
if(d.ok){$('charName').value='';$('charDesc').value='';await loadChars();$('status').textContent='บันทึกตัวละคร '+name+' แล้ว'}};
async function load(){const d=await fetch('/api/image-generator/settings').then(r=>r.json());if(d.provider)$('provider').value=d.provider;if(d.has_key)$('key').placeholder='•••••••• (บันทึกแล้ว)';await loadChars()}async function save(){const d=await fetch('/api/image-generator/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider:$('provider').value,api_key:$('key').value})}).then(r=>r.json());$('status').textContent=d.ok?'บันทึก API แล้ว':(d.error||'บันทึกไม่สำเร็จ');if(d.ok)$('key').value=''}$('save').onclick=save;$('gen').onclick=async()=>{$('status').textContent='กำลังสร้าง...';$('gen').disabled=true;try{if($('key').value)await save();const d=await fetch('/api/image-generator/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:$('prompt').value,character_id:SELECTED_CHAR})}).then(r=>r.json());if(!d.ok)throw Error(d.error||'สร้างไม่สำเร็จ');$('result').innerHTML='<img src="'+d.url+'?t='+Date.now()+'">';$('status').textContent='สร้างแล้ว · บันทึกเข้าคลัง AI จัดร้าน V4 แล้ว'}catch(e){$('status').textContent=e.message}finally{$('gen').disabled=false}};load()</script></body></html>'''


def install_infini_image_generator_7000(app) -> None:
    if getattr(app.state,"_infini_image_generator_v1",False): return
    app.state._infini_image_generator_v1=True

    @app.get("/image-generator",response_class=HTMLResponse)
    async def page(request:Request):
        if not _current_user(request): return HTMLResponse("login required",status_code=401)
        return HTMLResponse(PAGE)

    @app.get("/api/image-generator/settings")
    async def get_settings(request:Request):
        uid=_current_user(request)
        if not uid:return JSONResponse({"ok":False},status_code=401)
        d=_load_settings(uid);return JSONResponse({"ok":True,"provider":d.get("provider") or "openai","has_key":bool(d.get("api_key"))})

    @app.post("/api/image-generator/settings")
    async def set_settings(request:Request):
        uid=_current_user(request)
        if not uid:return JSONResponse({"ok":False},status_code=401)
        p=await request.json();d=_load_settings(uid);provider=str(p.get("provider") or "openai").lower();d["provider"]=provider if provider in {"openai","gemini"} else "openai";key=str(p.get("api_key") or "").strip();
        if key:d["api_key"]=key
        _save_settings(uid,d);return JSONResponse({"ok":True})

    @app.get("/api/image-generator/characters")
    async def list_characters(request:Request):
        uid=_current_user(request)
        if not uid:return JSONResponse({"ok":False},status_code=401)
        return JSONResponse({"ok":True,"items":_load_characters(uid)})

    @app.post("/api/image-generator/characters")
    async def add_character(request:Request):
        uid=_current_user(request)
        if not uid:return JSONResponse({"ok":False},status_code=401)
        p=await request.json()
        name=str(p.get("name") or "").strip()[:80]
        desc=str(p.get("description") or "").strip()[:2000]
        if not name or not desc:
            return JSONResponse({"ok":False,"error":"ต้องใส่ชื่อและคำอธิบายตัวละคร"},status_code=400)
        items=_load_characters(uid)
        item={"id":uuid.uuid4().hex[:12],"name":name,"description":desc,"created_at":int(time.time())}
        items.append(item)
        _save_characters(uid,items)
        return JSONResponse({"ok":True,"item":item,"items":items})

    @app.delete("/api/image-generator/characters/{char_id}")
    async def delete_character(request:Request,char_id:str):
        uid=_current_user(request)
        if not uid:return JSONResponse({"ok":False},status_code=401)
        items=[c for c in _load_characters(uid) if c.get("id")!=char_id]
        _save_characters(uid,items)
        return JSONResponse({"ok":True,"items":items})

    @app.post("/api/image-generator/generate")
    async def generate(request:Request):
        uid=_current_user(request)
        if not uid:return JSONResponse({"ok":False,"error":"กรุณาเข้าสู่ระบบ"},status_code=401)
        p=await request.json();prompt=str(p.get("prompt") or "").strip()
        if not prompt:return JSONResponse({"ok":False,"error":"กรุณาใส่ Prompt"},status_code=400)

        char_id=str(p.get("character_id") or "").strip()
        if char_id:
            char=next((c for c in _load_characters(uid) if c.get("id")==char_id),None)
            if char:
                # Prepend the saved appearance description so the SAME
                # character shows up across different generated images —
                # neither OpenAI's nor Gemini's image APIs here take a
                # reference photo as input, so consistent text description
                # baked into every prompt is what actually gets a
                # recognizably-similar result each time.
                prompt=f"{char['name']}: {char['description']}. {prompt}".strip()

        s=_load_settings(uid);key=str(s.get("api_key") or "").strip();provider=str(s.get("provider") or "openai")
        if not key:return JSONResponse({"ok":False,"error":"กรุณาเลือกค่ายและกรอก API Key ก่อน"},status_code=400)
        try:
            raw=_gemini_image(key,prompt) if provider=="gemini" else _openai_image(key,prompt)
            if not raw:raise ValueError("ไม่ได้รับข้อมูลรูป")
            item=_save_to_shop_library(uid,raw,prompt[:80]);return JSONResponse({"ok":True,"url":item["url"],"item":item})
        except urlerror.HTTPError as exc:
            try:detail=exc.read().decode("utf-8","ignore")[:800]
            except Exception:detail=str(exc)
            return JSONResponse({"ok":False,"error":f"API ตอบ {exc.code}: {detail}"},status_code=400)
        except Exception as exc:return JSONResponse({"ok":False,"error":str(exc)},status_code=400)
