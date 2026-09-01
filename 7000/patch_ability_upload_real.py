from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8")

MARK = "# === AI_ABILITY_ROOM_UPLOAD_REAL_V1 ==="

if MARK in s:
    print("มี AI_ABILITY_ROOM_UPLOAD_REAL_V1 แล้ว ไม่เขียนซ้ำ")
else:
    # 1) ให้ form อัปโหลดไฟล์ได้
    s = s.replace(
        '<form method="post" action="/ai-ability-room/build">',
        '<form method="post" action="/ai-ability-room/build" enctype="multipart/form-data">',
        1
    )

    # 2) เพิ่มช่องรูป + แพทเทิร์น ก่อนปุ่มเดิม
    old_btn = '<button class="btn" type="submit">ดึงห้องความรู้ + แสดงผล Prompt</button>'
    add_fields = '''
            <label>เลือกรูปฉาก</label>
            <input type="file" name="scene_image" accept="image/*">

            <label>เลือกรูปสินค้า / ของที่จะวาง</label>
            <input type="file" name="product_image" accept="image/*">

            <label>แพทเทิร์นแผ่นที่จะออกมา</label>
            <select name="sheet_pattern">
                <option value="basic">Basic Sheet</option>
                <option value="product">Product Sheet</option>
                <option value="catalog">Catalog Grid</option>
                <option value="vintage">Vintage Sheet</option>
                <option value="promo">Promo Sheet</option>
                <option value="gallery">Gallery Sheet</option>
                <option value="market">Market Sheet</option>
            </select>

            <button class="btn" type="submit">อัปโหลดรูป + ดึงความรู้ + สร้าง Prompt</button>'''
    if old_btn in s:
        s = s.replace(old_btn, add_fields, 1)
    else:
        print("เตือน: ไม่เจอปุ่มเดิม อาจต้องใส่ช่องรูปเอง")

    # 3) เพิ่ม helper สำหรับเซฟไฟล์ ก่อน POST route
    helper = r'''
# === AI_ABILITY_ROOM_UPLOAD_REAL_V1 ===
from pathlib import Path as _ABPath
import uuid as _ABUuid
from fastapi import UploadFile as _ABUploadFile, File as _ABFile

_AB_UPLOADS = _ABPath("data/ai_ability_room/uploads")
_AB_UPLOADS.mkdir(parents=True, exist_ok=True)

def _ab_ext(filename):
    ext = _ABPath(filename or "image.jpg").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    return ext

async def _ab_save_upload(file, kind):
    if not file:
        return None
    raw = await file.read()
    if not raw:
        return None
    if len(raw) > 25 * 1024 * 1024:
        return None
    name = f"{kind}_{_ABUuid.uuid4().hex}{_ab_ext(file.filename)}"
    out = _AB_UPLOADS / name
    out.write_bytes(raw)
    return {
        "name": file.filename or name,
        "url": f"/ai-ability-room/file/{name}",
        "kind": kind
    }

@app.get("/ai-ability-room/file/{name}")
def ai_ability_room_file(name: str):
    from fastapi.responses import FileResponse as _ABFileResponse
    safe = _ABPath(name).name
    path = _AB_UPLOADS / safe
    if not path.exists():
        return {"ok": False, "error": "file not found"}
    return _ABFileResponse(path)
'''
    s = s.replace('@app.post("/ai-ability-room/build")', helper + '\n@app.post("/ai-ability-room/build")', 1)

    # 4) เปลี่ยน def เป็น async def และเพิ่ม field รับไฟล์จริง
    s = s.replace(
'''def ai_ability_room_build(
    goal: str = _TRForm(""),
    style_name: str = _TRForm(""),
    color: str = _TRForm(""),
    scene_note: str = _TRForm(""),
    product_note: str = _TRForm(""),
):''',
'''async def ai_ability_room_build(
    goal: str = _TRForm(""),
    style_name: str = _TRForm(""),
    color: str = _TRForm(""),
    scene_note: str = _TRForm(""),
    product_note: str = _TRForm(""),
    sheet_pattern: str = _TRForm("basic"),
    scene_image: _ABUploadFile = _ABFile(None),
    product_image: _ABUploadFile = _ABFile(None),
):''',
        1
    )

    # 5) เซฟไฟล์ แล้วผสมข้อมูลรูปเข้า prompt/result
    old_result = '    result = _tr_build_ability_prompt(goal, style_name, color, scene_note, product_note)'
    new_result = '''    scene_file = await _ab_save_upload(scene_image, "scene")
    product_file = await _ab_save_upload(product_image, "product")

    file_note_parts = []
    if scene_file:
        file_note_parts.append(f"รูปฉากจริง: {scene_file['url']}")
    if product_file:
        file_note_parts.append(f"รูปสินค้าจริง: {product_file['url']}")
    file_note_parts.append(f"แพทเทิร์นแผ่น: {sheet_pattern}")

    merged_scene_note = scene_note
    merged_product_note = product_note

    if file_note_parts:
        merged_scene_note = (merged_scene_note + "\\n" + "\\n".join(file_note_parts)).strip()

    result = _tr_build_ability_prompt(goal, style_name, color, merged_scene_note, merged_product_note)

    preview_html = ""
    if scene_file or product_file:
        preview_html += "\\n\\n<hr><h3>รูปที่ใช้สร้างงาน</h3>"
        if scene_file:
            preview_html += f'<p><b>ฉาก:</b></p><img src="{scene_file["url"]}" style="width:100%;max-width:420px;border-radius:18px;margin:8px 0;">'
        if product_file:
            preview_html += f'<p><b>สินค้า:</b></p><img src="{product_file["url"]}" style="width:100%;max-width:260px;border-radius:18px;margin:8px 0;">'
        preview_html += f"<p><b>Pattern:</b> {sheet_pattern}</p>"

    result = result + preview_html'''
    if old_result in s:
        s = s.replace(old_result, new_result, 1)
    else:
        print("เตือน: ไม่เจอบรรทัด result เดิม")

    # 6) เก็บค่าลง last
    s = s.replace(
'''        "product_note": product_note,
        "result": result,''',
'''        "product_note": product_note,
        "sheet_pattern": sheet_pattern,
        "scene_file": scene_file,
        "product_file": product_file,
        "result": result,''',
        1
    )

    p.write_text(s, encoding="utf-8")
    print("เพิ่ม upload รูปจริงใน ai-ability-room แล้ว")

