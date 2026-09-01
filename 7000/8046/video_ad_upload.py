from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads" / "ad_videos"
DATA_DIR = BASE_DIR / "data"
INDEX_FILE = DATA_DIR / "ad_videos.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
MAX_VIDEO_SIZE = 250 * 1024 * 1024


def _load_index() -> dict[str, Any]:
    if not INDEX_FILE.exists():
        return {"videos": {}}
    try:
        data = json.loads(INDEX_FILE.read_text("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("videos"), dict):
            return {"videos": {}}
        return data
    except (OSError, json.JSONDecodeError):
        return {"videos": {}}


def _save_index(data: dict[str, Any]) -> None:
    temp_file = INDEX_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    temp_file.replace(INDEX_FILE)


def _clean_ad_id(value: str) -> str:
    value = value.strip().lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    cleaned = "".join(ch for ch in value if ch in allowed)
    if not cleaned:
        raise HTTPException(status_code=400, detail="รหัสโฆษณาไม่ถูกต้อง")
    return cleaned[:80]


def video_player_html(ad_id: str) -> str:
    safe_id = _clean_ad_id(ad_id)
    info = _load_index()["videos"].get(safe_id)
    if not info:
        return f'''
        <div style="width:100%;min-height:70vh;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:24px;background:#070d21;border:1px solid #7c3aed;color:white;padding:28px">
          <div><h1 style="font-size:42px;margin:0 0 18px">พื้นที่แสดงโฆษณา 80%</h1><p style="font-size:24px">ยังไม่มีวิดีโอสำหรับรหัส <b>{safe_id}</b></p></div>
        </div>'''
    return f'''
    <div style="width:100%;min-height:70vh;display:flex;align-items:center;justify-content:center;border-radius:24px;overflow:hidden;background:#000;border:1px solid #7c3aed">
      <video controls playsinline preload="metadata" style="width:100%;height:70vh;object-fit:contain;background:#000">
        <source src="/ad-media/{safe_id}" type="{info.get('content_type', 'video/mp4')}">
        เบราว์เซอร์นี้ไม่รองรับการเล่นวิดีโอ
      </video>
    </div>'''


def setup_video_upload(app: FastAPI) -> None:
    @app.get("/ad-upload", response_class=HTMLResponse)
    async def ad_upload_page() -> HTMLResponse:
        index = _load_index()
        rows = []
        for ad_id, info in sorted(index["videos"].items()):
            rows.append(f'''
            <div class="item">
              <div><b>{ad_id}</b><div class="muted">{info.get('original_name', '')}</div></div>
              <div class="actions"><a href="/ad-preview/{ad_id}">ดูคลิป</a><form method="post" action="/ad-delete/{ad_id}" onsubmit="return confirm('ลบคลิปนี้หรือไม่?')"><button type="submit" class="danger">ลบ</button></form></div>
            </div>''')
        body = "".join(rows) or '<p class="muted">ยังไม่มีคลิปที่อัปโหลด</p>'
        return HTMLResponse(f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>อัปโหลดวิดีโอโฆษณา</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(180deg,#13052a,#030712);color:#fff;font-family:system-ui,-apple-system,sans-serif}}.wrap{{max-width:720px;margin:auto;padding:24px 18px 60px}}.card{{background:#080d20;border:1px solid #7c3aed;border-radius:28px;padding:22px;box-shadow:0 20px 70px #0008}}h1{{margin:0 0 8px;color:#c084fc}}label{{display:block;margin:16px 0 7px}}input{{width:100%;padding:14px;border:1px solid #6d28d9;border-radius:14px;background:#020617;color:#fff;font-size:16px}}button,.actions a{{display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:14px;padding:13px 18px;background:#7c3aed;color:#fff;font-weight:700;font-size:16px;text-decoration:none}}button{{width:100%;margin-top:18px}}.item{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 0;border-top:1px solid #26304b}}.actions{{display:flex;align-items:center;gap:8px}}.actions form{{margin:0}}.actions button{{width:auto;margin:0}}.danger{{background:#b91c1c}}.muted{{color:#a9b4cc;font-size:14px;word-break:break-all}}.note{{color:#fcd34d}}</style></head>
<body><div class="wrap"><div class="card"><h1>อัปโหลดวิดีโอโฆษณา</h1><p>ใส่รหัสเดียวกับโฆษณา เช่น <b>tech-1</b> แล้วเลือกคลิป</p>
<form action="/ad-upload" method="post" enctype="multipart/form-data"><label>รหัสโฆษณา</label><input name="ad_id" value="tech-1" required><label>เลือกคลิป</label><input type="file" name="video" accept="video/mp4,video/webm,video/quicktime" required><button type="submit">อัปโหลดคลิป</button></form>
<p class="note">รองรับ MP4, WEBM, MOV, M4V ขนาดไม่เกิน 250 MB</p><h2>คลิปที่มีอยู่</h2>{body}</div></div></body></html>''')

    @app.post("/ad-upload")
    async def upload_ad_video(ad_id: str = Form(...), video: UploadFile = File(...)) -> RedirectResponse:
        safe_ad_id = _clean_ad_id(ad_id)
        suffix = Path(video.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="รองรับเฉพาะ MP4, WEBM, MOV และ M4V")
        content = await video.read(MAX_VIDEO_SIZE + 1)
        await video.close()
        if len(content) > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=413, detail="ไฟล์ใหญ่เกิน 250 MB")
        index = _load_index()
        old = index["videos"].get(safe_ad_id)
        if old:
            old_path = UPLOAD_DIR / old.get("stored_name", "")
            if old_path.is_file():
                old_path.unlink()
        stored_name = f"{safe_ad_id}-{secrets.token_hex(6)}{suffix}"
        target = UPLOAD_DIR / stored_name
        target.write_bytes(content)
        index["videos"][safe_ad_id] = {"stored_name": stored_name, "original_name": video.filename or stored_name, "content_type": video.content_type or "video/mp4", "size": len(content), "uploaded_at": datetime.now(timezone.utc).isoformat()}
        _save_index(index)
        return RedirectResponse(url=f"/ad-preview/{safe_ad_id}", status_code=303)

    @app.get("/ad-media/{ad_id}")
    async def serve_ad_video(ad_id: str) -> FileResponse:
        safe_ad_id = _clean_ad_id(ad_id)
        info = _load_index()["videos"].get(safe_ad_id)
        if not info:
            raise HTTPException(status_code=404, detail="ไม่พบวิดีโอ")
        path = UPLOAD_DIR / info["stored_name"]
        if not path.is_file():
            raise HTTPException(status_code=404, detail="ไฟล์วิดีโอหาย")
        return FileResponse(path, media_type=info.get("content_type") or "video/mp4", filename=info.get("original_name") or path.name)

    @app.get("/ad-preview/{ad_id}", response_class=HTMLResponse)
    async def preview_ad_video(ad_id: str) -> HTMLResponse:
        safe_ad_id = _clean_ad_id(ad_id)
        player = video_player_html(safe_ad_id)
        return HTMLResponse(f'''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>โฆษณา {safe_ad_id}</title><style>*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(180deg,#16052f,#020617);color:white;font-family:system-ui,-apple-system,sans-serif}}.wrap{{max-width:760px;margin:auto;padding:22px 18px 50px}}.top{{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:18px}}a{{color:white;text-decoration:none;border:1px solid #7c3aed;border-radius:14px;padding:12px 16px}}</style></head><body><div class="wrap"><div class="top"><h2>โฆษณา: {safe_ad_id}</h2><a href="/ad-upload">จัดการคลิป</a></div>{player}</div></body></html>''')

    @app.post("/ad-delete/{ad_id}")
    async def delete_ad_video(ad_id: str) -> RedirectResponse:
        safe_ad_id = _clean_ad_id(ad_id)
        index = _load_index()
        info = index["videos"].pop(safe_ad_id, None)
        if info:
            path = UPLOAD_DIR / info.get("stored_name", "")
            if path.is_file():
                path.unlink()
            _save_index(index)
        return RedirectResponse(url="/ad-upload", status_code=303)
