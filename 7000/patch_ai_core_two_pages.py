from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8")

MARK = "# === INFINI_AI_CORE_TWO_PAGES_V1 ==="

if MARK in s:
    print("มี INFINI_AI_CORE_TWO_PAGES_V1 แล้ว ไม่เขียนซ้ำ")
else:
    patch = r'''

# === INFINI_AI_CORE_TWO_PAGES_V1 ===
# จัดระบบ AI ให้เหลือ 2 หน้าหลัก:
# 1) ห้องความรู้: AI Chat + AI จัดร้าน
# 2) ห้องความสามารถ: ดึงความรู้/รูปจาก AI จัดร้านไปใช้สร้างงาน
from pathlib import Path as _COREPath
import json as _COREJson
import time as _CORETime
import uuid as _COREUuid
from fastapi import Form as _COREForm, UploadFile as _COREUploadFile, File as _COREFile
from fastapi.responses import HTMLResponse as _COREHTMLResponse, RedirectResponse as _CORERedirectResponse, FileResponse as _COREFileResponse

_CORE_BASE = _COREPath("data/infini_ai_core")
_CORE_BASE.mkdir(parents=True, exist_ok=True)

_CORE_KNOWLEDGE = _CORE_BASE / "knowledge.json"
_CORE_UPLOADS = _CORE_BASE / "uploads"
_CORE_UPLOADS.mkdir(parents=True, exist_ok=True)

def _core_now():
    return int(_CORETime.time())

def _core_load_json(path, default):
    try:
        if path.exists():
            return _COREJson.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def _core_save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_COREJson.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _core_init():
    data = _core_load_json(_CORE_KNOWLEDGE, {"items": []})
    if "items" not in data:
        data = {"items": []}
    _core_save_json(_CORE_KNOWLEDGE, data)
    return data

def _core_ext(filename):
    ext = _COREPath(filename or "file").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".txt", ".csv", ".json"}:
        ext = ".txt"
    return ext

async def _core_save_upload(file, section):
    if not file:
        return None
    raw = await file.read()
    if not raw:
        return None
    if len(raw) > 30 * 1024 * 1024:
        return None

    ext = _core_ext(file.filename)
    name = f"{section}_{_COREUuid.uuid4().hex}{ext}"
    out = _CORE_UPLOADS / name
    out.write_bytes(raw)

    text = ""
    if ext in {".txt", ".csv", ".json"}:
        try:
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    return {
        "name": file.filename or name,
        "stored": name,
        "url": f"/ai-core-file/{name}",
        "ext": ext,
        "text": text
    }

def _core_html_escape(x):
    return str(x or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def _core_pick_items(section=None):
    data = _core_init()
    items = data.get("items", [])
    if section:
        items = [x for x in items if x.get("section") == section]
    return items

def _core_render_items(section):
    items = _core_pick_items(section)
    if not items:
        return '<p class="muted">ยังไม่มีข้อมูลในส่วนนี้</p>'

    html = ""
    for it in items[::-1]:
        file_html = ""
        f = it.get("file")
        if f:
            if f.get("ext") in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                file_html = f'<img class="thumb" src="{_core_html_escape(f.get("url"))}">'
            else:
                file_html = f'<a class="link" href="{_core_html_escape(f.get("url"))}">ไฟล์: {_core_html_escape(f.get("name"))}</a>'

        html += f'''
        <div class="item">
            <div class="tag">{_core_html_escape(it.get("category") or "-")}</div>
            <h3>{_core_html_escape(it.get("title") or "ไม่มีชื่อ")}</h3>
            <p><b>Trigger:</b> {_core_html_escape(it.get("trigger") or "-")}</p>
            <p>{_core_html_escape(it.get("content") or "")}</p>
            {file_html}
        </div>
        '''
    return html

def _core_collect_shop_knowledge():
    items = _core_pick_items("shop_ai")
    texts = []
    images = []

    for it in items:
        line = []
        if it.get("title"):
            line.append(f"หัวข้อ: {it.get('title')}")
        if it.get("category"):
            line.append(f"หมวด: {it.get('category')}")
        if it.get("trigger"):
            line.append(f"Trigger: {it.get('trigger')}")
        if it.get("content"):
            line.append(f"เนื้อหา: {it.get('content')}")
        if line:
            texts.append("\n".join(line))

        f = it.get("file")
        if f and f.get("ext") in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            images.append(f)

    return texts, images

def _core_build_shop_output(goal, pattern, extra_note):
    texts, images = _core_collect_shop_knowledge()

    knowledge_text = "\n\n---\n\n".join(texts[-12:]) if texts else "ยังไม่มีความรู้ AI จัดร้านในห้องความรู้"

    output = f"""
โจทย์:
{goal or "-"}

แพทเทิร์นแผ่น:
{pattern or "basic"}

คำสั่งเพิ่ม:
{extra_note or "-"}

ข้อมูลที่ดึงจากห้องความรู้ AI จัดร้าน:
{knowledge_text}

คำสั่งจัดงาน:
1. ใช้ข้อมูลจากห้องความรู้ AI จัดร้านเป็นกฎหลัก
2. ถ้ามีรูป reference ให้ยึด mood, layout, แสง, สี, ระยะ และสไตล์จากรูปนั้น
3. จัดสินค้าให้เด่นกว่าฉาก
4. ข้อความต้องอ่านง่าย ไม่บังสินค้า
5. ถ้าเป็นร้านวินเทจ ให้รักษาฟีลดิบ อุ่น เก่า มีเรื่องเล่า
6. ถ้าเป็น catalog ให้จัดของเป็นหมวด อ่านราคา/ไซซ์ง่าย
7. ถ้าเป็น market sheet ให้มีจุดขาย ราคา และปุ่มสั่งซื้อชัด
"""
    return output.strip(), images

@app.get("/ai-core-file/{name}")
def ai_core_file(name: str):
    safe = _COREPath(name).name
    path = _CORE_UPLOADS / safe
    if not path.exists():
        return {"ok": False, "error": "file not found"}
    return _COREFileResponse(path)

@app.get("/ai-core-knowledge", response_class=_COREHTMLResponse)
def ai_core_knowledge_page():
    _core_init()

    chat_items = _core_render_items("chat_ai")
    shop_items = _core_render_items("shop_ai")

    html = f'''
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>INFINI AI Knowledge</title>
        <style>
            body {{
                margin:0;
                background:#090402;
                color:#fff;
                font-family:system-ui,sans-serif;
            }}
            .wrap {{
                max-width:980px;
                margin:auto;
                padding:18px;
            }}
            .top {{
                display:flex;
                gap:10px;
                align-items:center;
                margin-bottom:16px;
                flex-wrap:wrap;
            }}
            .btnlink {{
                color:#ffd0a0;
                text-decoration:none;
                border:1px solid #7a3f1a;
                border-radius:18px;
                padding:10px 14px;
                background:#120806;
                font-weight:800;
            }}
            .hero,.panel {{
                border:1px solid #6a3518;
                border-radius:26px;
                padding:18px;
                background:linear-gradient(135deg,#1a0b05,#050505,#1b0d06);
                margin-bottom:18px;
            }}
            h1 {{
                color:#ff8f22;
                margin:0 0 8px;
                font-size:38px;
            }}
            h2 {{
                color:#ff9f28;
                font-size:30px;
            }}
            label {{
                display:block;
                margin:12px 0 6px;
                color:#d8c1ae;
                font-size:16px;
            }}
            input,select,textarea {{
                width:100%;
                box-sizing:border-box;
                padding:13px;
                border-radius:16px;
                border:1px solid #3b2418;
                background:#050505;
                color:#fff;
                font-size:16px;
            }}
            textarea {{ min-height:120px; }}
            button {{
                width:100%;
                margin-top:14px;
                border:0;
                border-radius:18px;
                padding:15px;
                font-size:18px;
                font-weight:900;
                background:linear-gradient(135deg,#ff9f22,#ffbd4a);
                color:#111;
            }}
            .grid {{
                display:grid;
                grid-template-columns:1fr;
                gap:14px;
            }}
            .item {{
                border:1px solid #342015;
                border-radius:20px;
                padding:14px;
                background:#090909;
                margin:10px 0;
            }}
            .tag {{
                display:inline-block;
                color:#ffb15a;
                border:1px solid #6a3518;
                border-radius:999px;
                padding:4px 10px;
                font-size:13px;
                margin-bottom:8px;
            }}
            .thumb {{
                width:100%;
                max-width:360px;
                border-radius:18px;
                border:1px solid #6a3518;
                margin-top:10px;
            }}
            .muted {{ color:#b7a89a; }}
            .link {{ color:#ffb15a; }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="top">
                <a class="btnlink" href="/">← หน้าแรก</a>
                <a class="btnlink" href="/ai-core-ability">ห้องความสามารถ</a>
            </div>

            <div class="hero">
                <h1>ห้องความรู้ AI</h1>
                <p class="muted">หน้าเดียวเก็บทั้งความรู้ AI Chat และความรู้ AI จัดร้าน</p>
            </div>

            <div class="grid">
                <div class="panel">
                    <h2>1) ความรู้ AI Chat</h2>
                    <form method="post" action="/ai-core-knowledge/add" enctype="multipart/form-data">
                        <input type="hidden" name="section" value="chat_ai">
                        <label>ชื่อก้อนความรู้</label>
                        <input name="title" placeholder="เช่น วิธีรับออเดอร์ / เมนูกาแฟ / FAQ ร้าน">

                        <label>หมวด</label>
                        <input name="category" placeholder="FAQ / เมนู / ราคา / ขั้นตอนบริการ / คำถามที่ต้องถามกลับ">

                        <label>Trigger / คำเรียก</label>
                        <input name="trigger" placeholder="เช่น ราคา, สั่งซื้อ, ไซซ์, ส่งของ, ลดได้ไหม">

                        <label>ข้อความความรู้</label>
                        <textarea name="content" placeholder="ใส่คำตอบ วิธีพูด ขั้นตอนขาย หรือข้อมูลบริการ"></textarea>

                        <label>ไฟล์เสริม .txt / .json / .csv / รูปประกอบ</label>
                        <input type="file" name="file">

                        <button>บันทึกเข้าความรู้ AI Chat</button>
                    </form>

                    <h2>คลัง AI Chat</h2>
                    {chat_items}
                </div>

                <div class="panel">
                    <h2>2) ความรู้ AI จัดร้าน</h2>
                    <form method="post" action="/ai-core-knowledge/add" enctype="multipart/form-data">
                        <input type="hidden" name="section" value="shop_ai">
                        <label>ชื่อก้อนความรู้</label>
                        <input name="title" placeholder="เช่น วินเทจเสื้อวง / ร้านรองเท้า / Catalog Grid / Reference ร้าน">

                        <label>หมวด</label>
                        <input name="category" placeholder="Style / Visual DNA / Layout Rules / Reference Image / Product Rule">

                        <label>Trigger / คำเรียก</label>
                        <input name="trigger" placeholder="เช่น วินเทจ, เสื้อกระสอบ, รองเท้า, แคตตาล็อก, ร้านค้า">

                        <label>ข้อความความรู้</label>
                        <textarea name="content" placeholder="ใส่กฎจัดร้าน สไตล์ โทน แสง ตำแหน่งวางสินค้า สิ่งที่ต้องจำ"></textarea>

                        <label>อัปโหลดรูป Reference / ฉาก / Asset / ไฟล์ข้อความ</label>
                        <input type="file" name="file">

                        <button>บันทึกเข้าความรู้ AI จัดร้าน</button>
                    </form>

                    <h2>คลัง AI จัดร้าน</h2>
                    {shop_items}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.post("/ai-core-knowledge/add")
async def ai_core_knowledge_add(
    section: str = _COREForm("shop_ai"),
    title: str = _COREForm(""),
    category: str = _COREForm(""),
    trigger: str = _COREForm(""),
    content: str = _COREForm(""),
    file: _COREUploadFile = _COREFile(None)
):
    data = _core_init()
    saved = await _core_save_upload(file, section)

    final_content = content.strip()
    if saved and saved.get("text"):
        if final_content:
            final_content += "\n\n"
        final_content += saved.get("text", "")

    data.setdefault("items", []).append({
        "id": "core_" + _COREUuid.uuid4().hex[:10],
        "created_at": _core_now(),
        "section": section if section in {"chat_ai", "shop_ai"} else "shop_ai",
        "title": title.strip(),
        "category": category.strip(),
        "trigger": trigger.strip(),
        "content": final_content,
        "file": saved
    })

    _core_save_json(_CORE_KNOWLEDGE, data)
    return _CORERedirectResponse("/ai-core-knowledge", status_code=303)

@app.get("/ai-core-ability", response_class=_COREHTMLResponse)
def ai_core_ability_page():
    last = _core_load_json(_CORE_BASE / "last_ability.json", {})
    result = last.get("result", "")
    images = last.get("images", [])

    img_html = ""
    for f in images[:12]:
        img_html += f'<img class="thumb" src="{_core_html_escape(f.get("url"))}">'

    html = f'''
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>INFINI AI Ability</title>
        <style>
            body {{
                margin:0;
                background:#080402;
                color:#fff;
                font-family:system-ui,sans-serif;
            }}
            .wrap {{
                max-width:900px;
                margin:auto;
                padding:18px;
            }}
            .top {{
                display:flex;
                gap:10px;
                align-items:center;
                margin-bottom:16px;
                flex-wrap:wrap;
            }}
            .btnlink {{
                color:#ffd0a0;
                text-decoration:none;
                border:1px solid #7a3f1a;
                border-radius:18px;
                padding:10px 14px;
                background:#120806;
                font-weight:800;
            }}
            .hero,.panel {{
                border:1px solid #6a3518;
                border-radius:26px;
                padding:18px;
                background:linear-gradient(135deg,#1a0b05,#050505,#160904);
                margin-bottom:18px;
            }}
            h1 {{
                color:#ff8f22;
                margin:0 0 8px;
                font-size:38px;
            }}
            h2 {{
                color:#ff9f28;
                font-size:28px;
            }}
            label {{
                display:block;
                margin:12px 0 6px;
                color:#d8c1ae;
                font-size:16px;
            }}
            input,select,textarea {{
                width:100%;
                box-sizing:border-box;
                padding:13px;
                border-radius:16px;
                border:1px solid #3b2418;
                background:#050505;
                color:#fff;
                font-size:16px;
            }}
            textarea {{ min-height:130px; }}
            button {{
                width:100%;
                margin-top:14px;
                border:0;
                border-radius:18px;
                padding:15px;
                font-size:18px;
                font-weight:900;
                background:linear-gradient(135deg,#ff9f22,#ffbd4a);
                color:#111;
            }}
            .result {{
                white-space:pre-wrap;
                background:#050505;
                border:1px solid #332014;
                border-radius:20px;
                padding:14px;
                line-height:1.55;
            }}
            .thumb {{
                width:100%;
                max-width:360px;
                border-radius:18px;
                border:1px solid #6a3518;
                margin:8px 8px 8px 0;
            }}
            .muted {{ color:#b7a89a; }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="top">
                <a class="btnlink" href="/">← หน้าแรก</a>
                <a class="btnlink" href="/ai-core-knowledge">ห้องความรู้</a>
            </div>

            <div class="hero">
                <h1>ห้องความสามารถ AI จัดร้าน</h1>
                <p class="muted">หน้านี้ไม่ต้องกรอกความรู้ซ้ำ เวลาเจนจะดึงข้อมูลและรูปจาก “ห้องความรู้ AI จัดร้าน” มาใช้</p>
            </div>

            <div class="panel">
                <h2>สั่งให้ AI จัดร้าน</h2>
                <form method="post" action="/ai-core-ability/build">
                    <label>โจทย์ที่จะให้จัด</label>
                    <textarea name="goal" placeholder="เช่น เอาร้านวินเทจเสื้อวง จัดเป็นแผ่น catalog พร้อมขาย"></textarea>

                    <label>แพทเทิร์นงาน</label>
                    <select name="pattern">
                        <option value="basic">Basic Sheet</option>
                        <option value="product">Product Sheet</option>
                        <option value="catalog">Catalog Grid</option>
                        <option value="vintage">Vintage Sheet</option>
                        <option value="promo">Promo Sheet</option>
                        <option value="gallery">Gallery Sheet</option>
                        <option value="market">Market Sheet</option>
                    </select>

                    <label>คำสั่งพิเศษ</label>
                    <textarea name="extra_note" placeholder="เช่น ใช้โทนดิบ อุ่น ป้ายใหญ่ด้านบน สินค้าเด่นกลางภาพ ราคาอ่านง่าย"></textarea>

                    <button>ดึงความรู้ AI จัดร้าน + สร้างผลลัพธ์</button>
                </form>
            </div>

            <div class="panel">
                <h2>รูป/Reference ที่ดึงจากห้องความรู้ AI จัดร้าน</h2>
                {img_html or '<p class="muted">ยังไม่มีรูปในห้องความรู้ AI จัดร้าน</p>'}
            </div>

            <div class="panel">
                <h2>ผลลัพธ์</h2>
                <div class="result">{_core_html_escape(result) if result else "ยังไม่มีผลลัพธ์"}</div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.post("/ai-core-ability/build")
def ai_core_ability_build(
    goal: str = _COREForm(""),
    pattern: str = _COREForm("basic"),
    extra_note: str = _COREForm("")
):
    result, images = _core_build_shop_output(goal, pattern, extra_note)

    _core_save_json(_CORE_BASE / "last_ability.json", {
        "created_at": _core_now(),
        "goal": goal,
        "pattern": pattern,
        "extra_note": extra_note,
        "result": result,
        "images": images
    })

    return _CORERedirectResponse("/ai-core-ability", status_code=303)

@app.get("/ai-core-json")
def ai_core_json():
    return {
        "ok": True,
        "module": "INFINI_AI_CORE_TWO_PAGES_V1",
        "knowledge": _core_init(),
        "last_ability": _core_load_json(_CORE_BASE / "last_ability.json", {})
    }

# === END INFINI_AI_CORE_TWO_PAGES_V1 ===
'''
    p.write_text(s + patch, encoding="utf-8")
    print("เพิ่ม INFINI_AI_CORE_TWO_PAGES_V1 แล้ว")

