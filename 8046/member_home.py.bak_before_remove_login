from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads" / "member_profiles"
MEMBERS_FILE = DATA_DIR / "members.json"
SECRET_FILE = DATA_DIR / "member_secret.txt"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_NAME = "infini_member"
COOKIE_AGE = 60 * 60 * 24 * 30
MAX_IMAGE_SIZE = 8 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _load_data() -> dict[str, Any]:
    if not MEMBERS_FILE.exists():
        return {"members": {}}
    try:
        data = json.loads(MEMBERS_FILE.read_text("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("members"), dict):
            return {"members": {}}
        return data
    except (OSError, json.JSONDecodeError):
        return {"members": {}}


def _save_data(data: dict[str, Any]) -> None:
    temp = MEMBERS_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    temp.replace(MEMBERS_FILE)


def _secret() -> bytes:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text("utf-8").strip().encode()
    value = secrets.token_urlsafe(48)
    SECRET_FILE.write_text(value, "utf-8")
    return value.encode()


SECRET = _secret()


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex(), digest.hex()


def _verify_password(password: str, salt_hex: str, expected: str) -> bool:
    _, actual = _hash_password(password, salt_hex)
    return hmac.compare_digest(actual, expected)


def _make_member_id(data: dict[str, Any]) -> str:
    while True:
        member_id = f"INF-{secrets.randbelow(900000) + 100000}"
        if member_id not in data["members"]:
            return member_id


def _make_session(member_id: str) -> str:
    payload = f"{member_id}|{int(time.time())}"
    signature = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}|{signature}"


def _read_session(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        member_id, created_at, signature = token.rsplit("|", 2)
        payload = f"{member_id}|{created_at}"
        expected = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        if int(time.time()) - int(created_at) > COOKIE_AGE:
            return None
        return member_id
    except (ValueError, TypeError):
        return None


def _member_from_request(request: Request) -> tuple[str, dict[str, Any]] | None:
    member_id = _read_session(request)
    if not member_id:
        return None
    member = _load_data()["members"].get(member_id)
    if not member:
        return None
    return member_id, member


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:linear-gradient(180deg,#16052f,#020617);color:#fff;font-family:system-ui,-apple-system,sans-serif}}
a{{color:inherit;text-decoration:none}}
.wrap{{max-width:720px;margin:auto;padding:18px 16px 48px}}
.card{{background:#080d20;border:1px solid #7c3aed;border-radius:28px;overflow:hidden;box-shadow:0 20px 70px #0009}}
.pad{{padding:22px}}
h1,h2,p{{margin-top:0}}
h1{{color:#d8b4fe}}
.muted{{color:#aab6d0}}
label{{display:block;margin:14px 0 7px}}
input,textarea{{width:100%;padding:14px;border-radius:14px;border:1px solid #6d28d9;background:#020617;color:#fff;font-size:16px}}
textarea{{min-height:90px;resize:vertical}}
button,.btn{{display:flex;align-items:center;justify-content:center;width:100%;padding:14px;border:0;border-radius:15px;background:#7c3aed;color:#fff;font-size:17px;font-weight:750;margin-top:14px}}
.btn.secondary{{background:#172036;border:1px solid #4c5f85}}
.btn.enter{{background:linear-gradient(90deg,#7c3aed,#2563eb);font-size:19px;padding:16px}}
.hero{{height:58vh;min-height:360px;max-height:620px;background:#050816;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.hero img{{width:100%;height:100%;object-fit:cover}}
.hero-empty{{text-align:center;color:#9fb0cc;padding:30px}}
.hero-tools{{position:absolute;left:14px;right:14px;bottom:14px;background:#020617cc;border:1px solid #6d28d9;border-radius:18px;padding:12px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}}
.stat{{background:#0d1530;border:1px solid #293a65;border-radius:16px;padding:14px}}
.stat b{{display:block;color:#c4b5fd;font-size:13px;margin-bottom:5px}}
.row{{display:flex;gap:10px}}
.row>*{{flex:1}}
.swipe{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;padding:3px 0 8px;margin-top:16px}}
.swipe-card{{min-width:84%;scroll-snap-align:center;background:#0d1530;border:1px solid #293a65;border-radius:20px;padding:18px}}
.error{{background:#3f0d18;border:1px solid #ef4444;color:#fecaca;padding:12px;border-radius:14px;margin-bottom:14px}}
.ok{{background:#0a3524;border:1px solid #22c55e;color:#bbf7d0;padding:12px;border-radius:14px;margin-bottom:14px}}
.small{{font-size:14px}}
</style>
</head>
<body><div class="wrap">{body}</div></body>
</html>""")


def setup_member_home(app: FastAPI) -> None:
    @app.get("/member", response_class=HTMLResponse)
    async def member_entry(request: Request):
        if _member_from_request(request):
            return RedirectResponse("/member/id", status_code=303)
        return RedirectResponse("/member/login", status_code=303)

    @app.get("/member/signup", response_class=HTMLResponse)
    async def signup_page():
        return _page("สมัครสมาชิก", """
        <div class="card"><div class="pad">
          <h1>สมัครสมาชิก</h1>
          <p class="muted">สมัครเสร็จแล้วจะเข้าสู่หน้า ID ของตัวเองทันที</p>
          <form method="post" action="/member/signup">
            <label>ชื่อที่แสดง</label>
            <input name="display_name" required>
            <label>ชื่อผู้ใช้</label>
            <input name="username" autocomplete="username" required>
            <label>รหัสผ่าน</label>
            <input type="password" name="password" minlength="4" autocomplete="new-password" required>
            <button type="submit">สมัครและสร้าง ID</button>
          </form>
          <a class="btn secondary" href="/member/login">มีบัญชีแล้ว เข้าสู่ระบบ</a>
        </div></div>
        """)

    @app.post("/member/signup")
    async def signup(
        display_name: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
    ):
        display_name = display_name.strip()
        username = username.strip().lower()

        if not display_name or not username or len(password) < 4:
            raise HTTPException(400, "กรอกข้อมูลไม่ครบ")

        data = _load_data()
        if any(m.get("username") == username for m in data["members"].values()):
            return _page("สมัครสมาชิก", """
            <div class="card"><div class="pad">
              <div class="error">ชื่อผู้ใช้นี้ถูกใช้แล้ว</div>
              <a class="btn" href="/member/signup">กลับไปสมัครใหม่</a>
            </div></div>
            """)

        member_id = _make_member_id(data)
        salt, password_hash = _hash_password(password)
        data["members"][member_id] = {
            "member_id": member_id,
            "display_name": display_name,
            "username": username,
            "password_salt": salt,
            "password_hash": password_hash,
            "bio": "",
            "contact": "",
            "link": "",
            "profile_image": "",
            "points": 0,
            "wallet_points": 0,
            "level": "Member",
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        _save_data(data)

        response = RedirectResponse("/member/id", status_code=303)
        response.set_cookie(
            COOKIE_NAME,
            _make_session(member_id),
            max_age=COOKIE_AGE,
            httponly=True,
            samesite="lax",
        )
        return response

    @app.get("/member/login", response_class=HTMLResponse)
    async def login_page():
        return _page("เข้าสู่ระบบ", """
        <div class="card"><div class="pad">
          <h1>เข้าสู่ระบบ</h1>
          <form method="post" action="/member/login">
            <label>ชื่อผู้ใช้</label>
            <input name="username" autocomplete="username" required>
            <label>รหัสผ่าน</label>
            <input type="password" name="password" autocomplete="current-password" required>
            <button type="submit">เข้าสู่หน้า ID</button>
          </form>
          <a class="btn secondary" href="/member/signup">สมัครสมาชิกใหม่</a>
        </div></div>
        """)

    @app.post("/member/login")
    async def login(username: str = Form(...), password: str = Form(...)):
        username = username.strip().lower()
        data = _load_data()

        selected_id = None
        selected_member = None
        for member_id, member in data["members"].items():
            if member.get("username") == username:
                selected_id = member_id
                selected_member = member
                break

        if not selected_member or not _verify_password(
            password,
            selected_member["password_salt"],
            selected_member["password_hash"],
        ):
            return _page("เข้าสู่ระบบ", """
            <div class="card"><div class="pad">
              <div class="error">ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง</div>
              <a class="btn" href="/member/login">ลองอีกครั้ง</a>
            </div></div>
            """)

        response = RedirectResponse("/member/id", status_code=303)
        response.set_cookie(
            COOKIE_NAME,
            _make_session(selected_id),
            max_age=COOKIE_AGE,
            httponly=True,
            samesite="lax",
        )
        return response

    @app.get("/member/id", response_class=HTMLResponse)
    async def member_id_page(request: Request):
        current = _member_from_request(request)
        if not current:
            return RedirectResponse("/member/login", status_code=303)

        member_id, member = current
        image = member.get("profile_image", "")
        image_html = (
            f'<img src="/member/media/{member_id}" alt="profile">'
            if image
            else '<div class="hero-empty"><h2>รูปประจำ ID</h2><p>กดเลือกรูปด้านล่างเพื่ออัปโหลด</p></div>'
        )

        return _page("หน้า ID สมาชิก", f"""
        <div class="card">
          <div class="hero">
            {image_html}
            <form class="hero-tools" method="post" action="/member/image" enctype="multipart/form-data">
              <input type="file" name="image" accept="image/*" required>
              <button type="submit">อัปโหลด / เปลี่ยนรูป</button>
            </form>
          </div>

          <div class="pad">
            <h1>{member.get("display_name","")}</h1>
            <p class="muted">@{member.get("username","")} · {member_id}</p>
            <p>{member.get("bio") or "ยังไม่ได้เขียนคำแนะนำตัว"}</p>

            <div class="grid">
              <div class="stat"><b>กระเป๋าคะแนน</b>{member.get("wallet_points",0)}</div>
              <div class="stat"><b>คะแนนสะสม</b>{member.get("points",0)}</div>
              <div class="stat"><b>ระดับสมาชิก</b>{member.get("level","Member")}</div>
              <div class="stat"><b>วันที่สมัคร</b>{member.get("joined_at","")}</div>
            </div>

            <div class="swipe">
              <div class="swipe-card">
                <h2>ข้อมูลของฉัน</h2>
                <p>ติดต่อ: {member.get("contact") or "-"}</p>
                <p>ลิงก์: {member.get("link") or "-"}</p>
              </div>
              <div class="swipe-card">
                <h2>กิจกรรม</h2>
                <p class="muted">ส่วนกิจกรรมจะปัดซ้าย–ขวาได้ตรงนี้</p>
              </div>
              <div class="swipe-card">
                <h2>คะแนนและสิทธิ์</h2>
                <p class="muted">พื้นที่แสดงประวัติคะแนนและสิทธิ์สมาชิก</p>
              </div>
            </div>

            <a class="btn enter" href="/">เดินเข้าตึก INFINI POINT TOWER</a>
            <div class="row">
              <a class="btn secondary" href="/member/edit">แก้ไขข้อมูล</a>
              <a class="btn secondary" href="/member/logout">ออกจากระบบ</a>
            </div>
          </div>
        </div>
        """)

    @app.get("/member/edit", response_class=HTMLResponse)
    async def edit_page(request: Request):
        current = _member_from_request(request)
        if not current:
            return RedirectResponse("/member/login", status_code=303)

        _, member = current
        return _page("แก้ไขข้อมูล", f"""
        <div class="card"><div class="pad">
          <h1>แก้ไขข้อมูล</h1>
          <form method="post" action="/member/edit">
            <label>ชื่อที่แสดง</label>
            <input name="display_name" value="{member.get("display_name","")}" required>
            <label>คำแนะนำตัว</label>
            <textarea name="bio">{member.get("bio","")}</textarea>
            <label>ช่องทางติดต่อ</label>
            <input name="contact" value="{member.get("contact","")}">
            <label>ลิงก์</label>
            <input name="link" value="{member.get("link","")}">
            <button type="submit">บันทึกข้อมูล</button>
          </form>
          <a class="btn secondary" href="/member/id">กลับหน้า ID</a>
        </div></div>
        """)

    @app.post("/member/edit")
    async def edit_member(
        request: Request,
        display_name: str = Form(...),
        bio: str = Form(""),
        contact: str = Form(""),
        link: str = Form(""),
    ):
        current = _member_from_request(request)
        if not current:
            return RedirectResponse("/member/login", status_code=303)

        member_id, _ = current
        data = _load_data()
        member = data["members"][member_id]
        member["display_name"] = display_name.strip()
        member["bio"] = bio.strip()
        member["contact"] = contact.strip()
        member["link"] = link.strip()
        _save_data(data)
        return RedirectResponse("/member/id", status_code=303)

    @app.post("/member/image")
    async def upload_image(request: Request, image: UploadFile = File(...)):
        current = _member_from_request(request)
        if not current:
            return RedirectResponse("/member/login", status_code=303)

        member_id, _ = current
        suffix = Path(image.filename or "").suffix.lower()
        if suffix not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(400, "รองรับ JPG, PNG, WEBP และ GIF")

        content = await image.read(MAX_IMAGE_SIZE + 1)
        await image.close()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(413, "รูปใหญ่เกิน 8 MB")

        data = _load_data()
        old_name = data["members"][member_id].get("profile_image")
        if old_name:
            old_file = UPLOAD_DIR / old_name
            if old_file.is_file():
                old_file.unlink()

        stored_name = f"{member_id}-{secrets.token_hex(5)}{suffix}"
        (UPLOAD_DIR / stored_name).write_bytes(content)
        data["members"][member_id]["profile_image"] = stored_name
        _save_data(data)

        return RedirectResponse("/member/id", status_code=303)

    @app.get("/member/media/{member_id}")
    async def member_media(member_id: str):
        data = _load_data()
        member = data["members"].get(member_id)
        if not member or not member.get("profile_image"):
            raise HTTPException(404, "ไม่พบรูป")
        path = UPLOAD_DIR / member["profile_image"]
        if not path.is_file():
            raise HTTPException(404, "ไม่พบไฟล์รูป")
        return FileResponse(path)

    @app.get("/member/logout")
    async def logout():
        response = RedirectResponse("/member/login", status_code=303)
        response.delete_cookie(COOKIE_NAME)
        return response
