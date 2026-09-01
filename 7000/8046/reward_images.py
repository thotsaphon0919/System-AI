from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads" / "reward_images"
INDEX_FILE = DATA_DIR / "reward_images.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def _load_index() -> dict[str, Any]:
    if not INDEX_FILE.exists():
        return {"rewards": {}}
    try:
        data = json.loads(INDEX_FILE.read_text("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("rewards"), dict):
            return {"rewards": {}}
        return data
    except (OSError, json.JSONDecodeError):
        return {"rewards": {}}


def _save_index(data: dict[str, Any]) -> None:
    temp = INDEX_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    temp.replace(INDEX_FILE)


def _clean_reward_id(value: str) -> str:
    value = value.strip().lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    cleaned = "".join(ch for ch in value if ch in allowed)
    if not cleaned:
        raise HTTPException(status_code=400, detail="รหัสรางวัลไม่ถูกต้อง")
    return cleaned[:80]


def reward_image_url(reward_id: str) -> str:
    """ใช้ URL เดียวกันทั้งหน้ารวมและหน้ายืนยัน"""
    return f"/reward-media/{_clean_reward_id(reward_id)}"


def reward_image_html(
    reward_id: str,
    *,
    alt: str = "รูปของรางวัล",
    css_class: str = "reward-image",
) -> str:
    """
    เรียกใช้ใน HTML ของทั้งสองหน้า:
    {reward_image_html("shoe")}
    """
    safe_id = _clean_reward_id(reward_id)
    index = _load_index()
    info = index["rewards"].get(safe_id)

    if info:
        return (
            f'<img class="{css_class}" src="/reward-media/{safe_id}" '
            f'alt="{alt}" loading="lazy">'
        )

    return (
        f'<div class="{css_class} reward-image-empty">'
        f'รูปของรางวัล'
        f'</div>'
    )


def reward_upload_button_html(reward_id: str) -> str:
    """
    ปุ่มนี้วางใต้ช่องรูปของรางวัล
    กดแล้วเปิดหน้าอัปโหลดของรางวัลชิ้นนั้น
    """
    safe_id = _clean_reward_id(reward_id)
    return f'<a class="reward-upload-button" href="/reward-upload/{safe_id}">อัปโหลด / เปลี่ยนรูป</a>'


def setup_reward_images(app: FastAPI) -> None:
    @app.get("/reward-upload/{reward_id}", response_class=HTMLResponse)
    async def reward_upload_page(reward_id: str) -> HTMLResponse:
        safe_id = _clean_reward_id(reward_id)
        preview = reward_image_html(safe_id, css_class="preview")

        return HTMLResponse(f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>อัปโหลดรูปรางวัล</title>
<style>
*{{box-sizing:border-box}}
body{{
    margin:0;
    background:linear-gradient(180deg,#16052f,#020617);
    color:#fff;
    font-family:system-ui,-apple-system,sans-serif;
}}
.wrap{{max-width:680px;margin:auto;padding:22px 16px 50px}}
.card{{
    background:#080d20;
    border:1px solid #7c3aed;
    border-radius:28px;
    overflow:hidden;
    box-shadow:0 20px 70px #0009;
}}
.preview{{
    width:100%;
    height:58vh;
    min-height:360px;
    object-fit:cover;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#12082c;
    color:#c4b5fd;
    font-size:24px;
}}
.pad{{padding:22px}}
h1{{margin:0 0 8px;color:#d8b4fe}}
p{{color:#aab6d0}}
input{{
    width:100%;
    padding:14px;
    border:1px solid #6d28d9;
    border-radius:14px;
    background:#020617;
    color:#fff;
}}
button,a{{
    display:flex;
    align-items:center;
    justify-content:center;
    width:100%;
    padding:14px;
    margin-top:14px;
    border:0;
    border-radius:15px;
    background:#7c3aed;
    color:#fff;
    text-decoration:none;
    font-size:17px;
    font-weight:750;
}}
a{{background:#172036;border:1px solid #4c5f85}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    {preview}
    <div class="pad">
      <h1>รูปรางวัล</h1>
      <p>รหัสรางวัล: <b>{safe_id}</b></p>

      <form method="post" action="/reward-upload/{safe_id}" enctype="multipart/form-data">
        <input type="file" name="image" accept="image/*" required>
        <button type="submit">อัปโหลด / เปลี่ยนรูป</button>
      </form>

      <a href="javascript:history.back()">ย้อนกลับ</a>
    </div>
  </div>
</div>
</body>
</html>""")

    @app.post("/reward-upload/{reward_id}")
    async def upload_reward_image(
        reward_id: str,
        request: Request,
        image: UploadFile = File(...),
    ):
        safe_id = _clean_reward_id(reward_id)
        suffix = Path(image.filename or "").suffix.lower()

        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="รองรับเฉพาะ JPG, PNG, WEBP และ GIF",
            )

        content = await image.read(MAX_IMAGE_SIZE + 1)
        await image.close()

        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="รูปใหญ่เกิน 10 MB")

        index = _load_index()
        old = index["rewards"].get(safe_id)

        if old:
            old_path = UPLOAD_DIR / old.get("stored_name", "")
            if old_path.is_file():
                old_path.unlink()

        stored_name = f"{safe_id}-{secrets.token_hex(6)}{suffix}"
        (UPLOAD_DIR / stored_name).write_bytes(content)

        index["rewards"][safe_id] = {
            "stored_name": stored_name,
            "original_name": image.filename or stored_name,
            "content_type": image.content_type or "image/jpeg",
        }
        _save_index(index)

        referer = request.headers.get("referer")
        return RedirectResponse(
            url=referer or f"/reward-upload/{safe_id}",
            status_code=303,
        )

    @app.get("/reward-media/{reward_id}")
    async def reward_media(reward_id: str):
        safe_id = _clean_reward_id(reward_id)
        index = _load_index()
        info = index["rewards"].get(safe_id)

        if not info:
            raise HTTPException(status_code=404, detail="ยังไม่มีรูปรางวัล")

        path = UPLOAD_DIR / info["stored_name"]
        if not path.is_file():
            raise HTTPException(status_code=404, detail="ไม่พบไฟล์รูปรางวัล")

        return FileResponse(
            path,
            media_type=info.get("content_type") or "image/jpeg",
        )
