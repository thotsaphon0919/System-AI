from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel

import sys
import threading
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    import backup_sync as _backup_sync
except Exception:
    _backup_sync = None


def _backup_users_file_now() -> None:
    """
    Fire-and-forget: push the just-updated users.json to Neon right away
    instead of waiting for the periodic (10-min) backup loop, so a new
    registration survives even if Render restarts moments later.
    """
    if _backup_sync is None:
        return
    threading.Thread(
        target=_backup_sync.backup_file_now,
        args=("8032/data/users.json",),
        daemon=True,
    ).start()


APP_NAME = "INFINI"
BASE_DIR = Path(__file__).resolve().parent

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.json"
SHEETS_FILE = DATA_DIR / "sheets.json"
LINKS_FILE = DATA_DIR / "links.json"
CHATS_FILE = DATA_DIR / "chats.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
MEMORY_FILE = DATA_DIR / "shared_memory.json"
ZONE_CARDS_FILE = DATA_DIR / "zone_cards.json"
USE_CASES_FILE = DATA_DIR / "use_case_videos.json"
USE_CASE_UPLOADS_DIR = UPLOADS_DIR / "use_cases"

for folder in (
    TEMPLATES_DIR,
    STATIC_DIR / "css",
    STATIC_DIR / "js",
    STATIC_DIR / "img",
    UPLOADS_DIR,
    USE_CASE_UPLOADS_DIR,
    DATA_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)

DEFAULT_FILES: dict[Path, Any] = {
    USERS_FILE: {},
    SHEETS_FILE: {},
    LINKS_FILE: [],
    CHATS_FILE: {},
    SETTINGS_FILE: {},
    MEMORY_FILE: {},
    ZONE_CARDS_FILE: [],
    USE_CASES_FILE: {},
}

for file_path, default_value in DEFAULT_FILES.items():
    if not file_path.exists():
        file_path.write_text(
            json.dumps(default_value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/wc", response_class=HTMLResponse)
async def workspace_page(request: Request):
    return templates.TemplateResponse(
        request,
        "workspace.html",
        {"request": request},
    )

# === INFINI_8032_TO_7000_AUTH_BRIDGE_V1 ===
SESSION_SECRET_FILE = DATA_DIR / "infini_session_secret.txt"
if not SESSION_SECRET_FILE.exists():
    SESSION_SECRET_FILE.write_text(
        os.getenv("INFINI_SESSION_SECRET") or secrets.token_urlsafe(48),
        encoding="utf-8",
    )
SESSION_SECRET = SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()
session_signer = URLSafeSerializer(SESSION_SECRET, salt="infini-session")
INFINI_7000_ID_URL = os.getenv("INFINI_7000_ID_URL", "http://127.0.0.1:7000/id")

# === INFINI_PUBLIC_8032_TO_7000_BRIDGE_V2 ===
PUBLIC_LINKS_FILE = DATA_DIR / "public_links.json"

def _read_public_links() -> dict:
    try:
        data = json.loads(PUBLIC_LINKS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _clean_public_base(value: str, fallback: str) -> str:
    raw = str(value or "").strip() or fallback
    try:
        parts = urlsplit(raw)
        if parts.scheme in ("http", "https") and parts.netloc:
            return urlunsplit((parts.scheme, parts.netloc, "", "", "")).rstrip("/")
    except Exception:
        pass
    return fallback.rstrip("/")

def _public_7000_base() -> str:
    # proxy.py serves the 7000 app at the ROOT of the same public domain
    # as this 8032 app (everything not under /8046 or /8032 falls through
    # to 7000), so a relative path always works correctly in production.
    # INFINI_7000_PUBLIC_URL / public_links.json are kept only as an
    # override for local/standalone (non-proxied) runs.
    configured = (
        os.getenv("INFINI_7000_PUBLIC_URL")
        or _read_public_links().get("public_7000_url")
        or ""
    )
    if str(configured).strip().startswith(("http://", "https://")):
        return _clean_public_base(configured, "")
    return ""

def _bridge_url_for(user_id: str) -> str:
    token = session_signer.dumps({
        "user_id": str(user_id),
        "issued_at": int(time.time()),
    })
    return (
        _public_7000_base()
        + "/auth/bridge?token="
        + quote(token, safe="")
        + "&next=%2Fid"
    )
# === END INFINI_PUBLIC_8032_TO_7000_BRIDGE_V2 ===
# === END INFINI_8032_TO_7000_AUTH_BRIDGE_V1 ===


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        fallback = DEFAULT_FILES.get(path, {})
        save_json(path, fallback)
        return fallback


def save_json(path: Path, data: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp.replace(path)


def password_hash(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        180_000,
    )
    return digest.hex(), salt


def verify_password(password: str, expected_hash: str, salt: str) -> bool:
    actual_hash, _ = password_hash(password, salt)
    return secrets.compare_digest(actual_hash, expected_hash)


def safe_filename(filename: str) -> str:
    original = Path(filename or "file").name
    stem = "".join(ch for ch in Path(original).stem if ch.isalnum() or ch in "-_")[:60]
    suffix = Path(original).suffix.lower()[:12]
    return f"{stem or 'file'}-{uuid.uuid4().hex[:10]}{suffix}"


def current_user_id(request: Request) -> str | None:
    token = request.cookies.get("infini_session")
    if not token:
        return None
    try:
        payload = session_signer.loads(token)
    except BadSignature:
        return None
    user_id = payload.get("user_id")
    return str(user_id) if user_id else None


def require_user(request: Request) -> str:
    user_id = current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")
    return user_id


def require_owned_sheet(sheet_id: str, user_id: str) -> dict[str, Any]:
    sheets = load_json(SHEETS_FILE)
    sheet = sheets.get(sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="ไม่พบแผ่น")
    if sheet.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึงแผ่นนี้")
    return sheet


def create_sheet_record(
    user_id: str,
    title: str,
    parent_sheet_id: str | None = None,
    inherited_core: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    sheet_id = f"sheet_{uuid.uuid4().hex[:12]}"
    timestamp = now_iso()
    return {
        "id": sheet_id,
        "user_id": user_id,
        "title": title.strip() or "แผ่นใหม่",
        "parent_sheet_id": parent_sheet_id,
        "children": [],
        "media": [],
        "notes": "",
        "goal": "",
        "links": [],
        "core_memory": inherited_core or [],
        "context": [],
        "history": [],
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def public_sheet(sheet: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": sheet["id"],
        "title": sheet["title"],
        "parent_sheet_id": sheet.get("parent_sheet_id"),
        "display_code": sheet.get("display_code"),
        "parent_code": sheet.get("parent_code"),
        "children": sheet.get("children", []),
        "media": sheet.get("media", []),
        "notes": sheet.get("notes", ""),
        "goal": sheet.get("goal", ""),
        "links": sheet.get("links", []),
        "core_memory": sheet.get("core_memory", []),
        "context": sheet.get("context", []),
        "history": sheet.get("history", []),
        "created_at": sheet.get("created_at"),
        "updated_at": sheet.get("updated_at"),
    }


def get_user_settings(user_id: str) -> dict[str, Any]:
    settings = load_json(SETTINGS_FILE)
    return settings.get(
        user_id,
        {
            "api_provider": "",
            "api_key": "",
            "sheet_limit": 100,
            "license_plan": "cloud",
        },
    )


class SheetCreate(BaseModel):
    title: str = "แผ่นใหม่"
    parent_sheet_id: str | None = None


class SheetUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    goal: str | None = None
    sender_code: str | None = None
    receiver_code: str | None = None
    warp_target: str | None = None


class LinkCreate(BaseModel):
    source_sheet_id: str
    source_item_id: str | None = None
    destination_page: str = ""
    destination_section: str = ""
    destination_sheet_id: str | None = None
    action: str = ""
    symbol: str = ""


class MemoryCreate(BaseModel):
    text: str
    source_sheet_id: str | None = None
    importance: int = 1


class ContextCreate(BaseModel):
    role: str = "user"
    text: str


class SettingsUpdate(BaseModel):
    api_provider: str = ""
    api_key: str = ""


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user_id = current_user_id(request)
    return RedirectResponse("/control-room" if user_id else "/service", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request, "app_name": APP_NAME},
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"request": request, "app_name": APP_NAME},
    )





@app.post("/api/zones/{zone_slug}/cards")
async def create_zone_card(
    request: Request,
    zone_slug: str,
    target_sheet_id: str = Form(...),
    title: str = Form(""),
    file: UploadFile = File(...),
):
    user_id = require_user(request)

    sheets = load_json(SHEETS_FILE)
    target_sheet = sheets.get(target_sheet_id)

    if not target_sheet:
        raise HTTPException(status_code=404, detail="ไม่พบแผ่นปลายทาง")

    if target_sheet.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์ใช้แผ่นนี้")

    destination = UPLOADS_DIR / user_id / "zones" / zone_slug
    destination.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "").suffix.lower() or ".jpg"
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = destination / stored_name
    stored_path.write_bytes(await file.read())

    card = {
        "id": f"zone_card_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "zone_slug": zone_slug,
        "title": title.strip() or target_sheet.get("title", "การ์ด"),
        "image_url": f"/uploads/{user_id}/zones/{zone_slug}/{stored_name}",
        "target_sheet_id": target_sheet_id,
        "target_url": f"/sheet/{target_sheet_id}",
        "created_at": now_iso(),
    }

    cards = load_json(ZONE_CARDS_FILE)
    cards.append(card)
    save_json(ZONE_CARDS_FILE, cards)

    return card


@app.get("/zone/{zone_slug}", response_class=HTMLResponse)
def zone_page(request: Request, zone_slug: str):
    user_id = current_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    sheets_data = load_json(SHEETS_FILE)
    owned_sheets = [
        item
        for item in sheets_data.values()
        if item.get("user_id") == user_id
        and not item.get("parent_sheet_id")
    ]
    owned_sheets.sort(key=lambda item: item.get("created_at", ""))

    return templates.TemplateResponse(
        request,
        "zone.html",
        {
            "request": request,
            "zone_slug": zone_slug,
            "sheets": owned_sheets,
        },
    )


@app.get("/workspace", response_class=HTMLResponse)
def workspace_page(request: Request):
    user_id = current_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    sheets_data = load_json(SHEETS_FILE)
    owned_sheets = [
        sheet
        for sheet in sheets_data.values()
        if sheet.get("user_id") == user_id
    ]
    owned_sheets.sort(key=lambda item: item.get("created_at", ""))

    # INFINI_WORKSPACE_ORDER_V1
    owned_sheets.sort(
        key=lambda sheet: (
            0 if str(sheet.get("title", "")).strip().lower() == "infini space"
            else 1 if (
                str(sheet.get("title", "")).strip().lower() == "zone"
                or str(sheet.get("title", "")).strip().lower().startswith("zone ")
                or str(sheet.get("title", "")).strip().startswith("โซน")
            )
            else 2,
            sheet.get("created_at", ""),
        )
    )

    return templates.TemplateResponse(
        request,
        "workspace.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "sheets": owned_sheets,
        },
    )



@app.get("/friends", response_class=HTMLResponse)
def friends_page(request: Request):
    user_id = current_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "friends.html",
        {
            "request": request,
            "app_name": APP_NAME,
        },
    )


@app.get("/control-room", response_class=HTMLResponse)
def control_room_page(request: Request):
    user_id = current_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    users = load_json(USERS_FILE)
    user = users.get(user_id)
    if not user:
        response = RedirectResponse("/login", status_code=303)
        response.delete_cookie("infini_session")
        return response


    sheets_data = load_json(SHEETS_FILE)
    owned_sheets = [
        sheet
        for sheet in sheets_data.values()
        if sheet.get("user_id") == user_id
    ]

    return templates.TemplateResponse(
        request,
        "control_room.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "user": user,
            "sheets": owned_sheets,
        },
    )


@app.get("/sheet/{sheet_id}", response_class=HTMLResponse)
def sheet_page(request: Request, sheet_id: str):
    user_id = current_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    sheet = require_owned_sheet(sheet_id, user_id)

    sheets_data = load_json(SHEETS_FILE)
    owned_sheets = [
        item for item in sheets_data.values()
        if item.get("user_id") == user_id
    ]
    owned_sheets.sort(key=lambda item: item.get("created_at", ""))

    sheet_ids = [item.get("id") for item in owned_sheets]
    current_index = sheet_ids.index(sheet_id)

    previous_sheet_id = sheet_ids[current_index - 1] if current_index > 0 else None
    next_sheet_id = sheet_ids[current_index + 1] if current_index < len(sheet_ids) - 1 else None

    child_ids = sheet.get("children", [])[:10]
    child_sheets = [
        sheets_data[child_id]
        for child_id in child_ids
        if child_id in sheets_data
    ]

    return templates.TemplateResponse(
        request,
        "sheet.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "sheet_id": sheet_id,
            "sheet": sheet,
            "child_sheets": child_sheets,
            "previous_sheet_id": previous_sheet_id,
            "next_sheet_id": next_sheet_id,
        },
    )


@app.post("/api/register")
def register(username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัว")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="รหัสผ่านต้องมีอย่างน้อย 6 ตัว")

    users = load_json(USERS_FILE)
    if any(user.get("username", "").lower() == username.lower() for user in users.values()):
        raise HTTPException(status_code=409, detail="ชื่อผู้ใช้นี้ถูกใช้แล้ว")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed, salt = password_hash(password)

    users[user_id] = {
        "id": user_id,
        "username": username,
        "infini_id": "INF-" + user_id.removeprefix("user_")[:8].upper(),
        "password_hash": hashed,
        "password_salt": salt,
        "created_at": now_iso(),
    }
    save_json(USERS_FILE, users)
    _backup_users_file_now()

    sheets = load_json(SHEETS_FILE)
    first_sheet = create_sheet_record(user_id, "แผ่นแรก")
    sheets[first_sheet["id"]] = first_sheet
    save_json(SHEETS_FILE, sheets)

    shared_memory = load_json(MEMORY_FILE)
    shared_memory[user_id] = []
    save_json(MEMORY_FILE, shared_memory)

    settings = load_json(SETTINGS_FILE)
    settings[user_id] = {
        "api_provider": "",
        "api_key": "",
        "sheet_limit": 100,
        "license_plan": "cloud",
    }
    save_json(SETTINGS_FILE, settings)

    response = RedirectResponse(_bridge_url_for(user_id), status_code=303)
    response.set_cookie(
        "infini_session",
        session_signer.dumps({"user_id": user_id}),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return response


@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    users = load_json(USERS_FILE)
    matched = next(
        (
            user
            for user in users.values()
            if user.get("username", "").lower() == username.strip().lower()
        ),
        None,
    )

    if not matched or not verify_password(
        password,
        matched["password_hash"],
        matched["password_salt"],
    ):
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    response = RedirectResponse(_bridge_url_for(matched["id"]), status_code=303)
    response.set_cookie(
        "infini_session",
        session_signer.dumps({"user_id": matched["id"]}),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return response


@app.post("/api/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("infini_session")
    return response


@app.get("/logout")
def logout_get():
    # templates (control_room.html, workspace.html) link here with a plain
    # <a href="/logout">, not a POST form, so this GET alias is needed too.
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("infini_session")
    return response


@app.get("/api/me")
def me(request: Request):
    user_id = require_user(request)
    users = load_json(USERS_FILE)
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    return {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
        "settings": get_user_settings(user_id),
    }


@app.get("/api/sheets")
def list_sheets(request: Request):
    user_id = require_user(request)
    sheets = load_json(SHEETS_FILE)
    owned = [
        public_sheet(sheet)
        for sheet in sheets.values()
        if sheet.get("user_id") == user_id
    ]
    owned.sort(key=lambda item: item.get("created_at") or "")
    return {"items": owned, "count": len(owned)}


@app.post("/api/sheets")
def create_sheet(request: Request, payload: SheetCreate):
    user_id = require_user(request)
    settings = get_user_settings(user_id)

    sheets = load_json(SHEETS_FILE)
    owned_count = sum(1 for sheet in sheets.values() if sheet.get("user_id") == user_id)
    sheet_limit = int(settings.get("sheet_limit", 100))

    if owned_count >= sheet_limit:
        raise HTTPException(
            status_code=403,
            detail=f"สิทธิ์ปัจจุบันสร้างได้สูงสุด {sheet_limit} แผ่น",
        )

    inherited_core: list[dict[str, Any]] = []
    if payload.parent_sheet_id:
        parent = require_owned_sheet(payload.parent_sheet_id, user_id)
        inherited_core = list(parent.get("core_memory", []))

    record = create_sheet_record(
        user_id=user_id,
        title=payload.title,
        parent_sheet_id=payload.parent_sheet_id,
        inherited_core=inherited_core,
    )
    # INFINI_DISPLAY_CODE_V1
    if payload.parent_sheet_id:
        parent = sheets[payload.parent_sheet_id]
        parent_code = str(parent.get("display_code") or "1")

        sibling_numbers = []
        for item in sheets.values():
            if (
                item.get("user_id") == user_id
                and item.get("parent_sheet_id") == payload.parent_sheet_id
            ):
                code = str(item.get("display_code") or "")
                try:
                    sibling_numbers.append(int(code.split(".")[-1]))
                except ValueError:
                    pass

        next_number = max(sibling_numbers, default=0) + 1
        record["display_code"] = f"{parent_code}.{next_number}"
        record["parent_code"] = parent_code
    else:
        root_numbers = []
        for item in sheets.values():
            if (
                item.get("user_id") == user_id
                and not item.get("parent_sheet_id")
            ):
                code = str(item.get("display_code") or "")
                if code.isdigit():
                    root_numbers.append(int(code))

        next_number = max(root_numbers, default=0) + 1
        record["display_code"] = str(next_number)
        record["parent_code"] = None

    sheets[record["id"]] = record

    if payload.parent_sheet_id:
        parent = sheets[payload.parent_sheet_id]
        parent.setdefault("children", []).append(record["id"])
        parent["updated_at"] = now_iso()

    save_json(SHEETS_FILE, sheets)
    return public_sheet(record)


@app.get("/api/sheets/{sheet_id}")
def read_sheet(request: Request, sheet_id: str):
    user_id = require_user(request)
    return public_sheet(require_owned_sheet(sheet_id, user_id))


@app.patch("/api/sheets/{sheet_id}")
def update_sheet(request: Request, sheet_id: str, payload: SheetUpdate):
    user_id = require_user(request)
    require_owned_sheet(sheet_id, user_id)

    sheets = load_json(SHEETS_FILE)
    sheet = sheets[sheet_id]

    for key, value in payload.model_dump(exclude_none=True).items():
        sheet[key] = value

    sheet["updated_at"] = now_iso()
    save_json(SHEETS_FILE, sheets)
    return public_sheet(sheet)



@app.delete("/api/sheets/{sheet_id}")
def delete_sheet(request: Request, sheet_id: str):
    user_id = current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")

    sheets = load_json(SHEETS_FILE)
    sheet = sheets.get(sheet_id)

    if not sheet:
        raise HTTPException(status_code=404, detail="ไม่พบแผ่นงาน")

    if sheet.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์ลบแผ่นนี้")

    del sheets[sheet_id]
    save_json(SHEETS_FILE, sheets)

    return {"ok": True, "deleted_sheet_id": sheet_id}


@app.post("/api/sheets/{sheet_id}/upload")
async def upload_to_sheet(
    request: Request,
    sheet_id: str,
    file: UploadFile = File(...),
):
    user_id = require_user(request)
    require_owned_sheet(sheet_id, user_id)

    destination = UPLOADS_DIR / user_id / sheet_id
    destination.mkdir(parents=True, exist_ok=True)

    stored_name = safe_filename(file.filename or "file")
    stored_path = destination / stored_name

    with stored_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    media_item = {
        "id": f"media_{uuid.uuid4().hex[:12]}",
        "original_name": file.filename,
        "stored_name": stored_name,
        "content_type": file.content_type or "application/octet-stream",
        "url": f"/uploads/{user_id}/{sheet_id}/{stored_name}",
        "created_at": now_iso(),
    }

    sheets = load_json(SHEETS_FILE)
    sheets[sheet_id].setdefault("media", []).append(media_item)
    sheets[sheet_id]["updated_at"] = now_iso()
    save_json(SHEETS_FILE, sheets)

    return media_item


@app.get("/api/links")
def list_links(request: Request, sheet_id: str | None = None):
    user_id = require_user(request)
    links = load_json(LINKS_FILE)

    owned_sheet_ids = {
        sheet["id"]
        for sheet in load_json(SHEETS_FILE).values()
        if sheet.get("user_id") == user_id
    }

    result = [
        link
        for link in links
        if link.get("source_sheet_id") in owned_sheet_ids
        and (sheet_id is None or link.get("source_sheet_id") == sheet_id)
    ]
    return {"items": result, "count": len(result)}


@app.post("/api/links")
def create_link(request: Request, payload: LinkCreate):
    user_id = require_user(request)
    require_owned_sheet(payload.source_sheet_id, user_id)

    if payload.destination_sheet_id:
        require_owned_sheet(payload.destination_sheet_id, user_id)

    link = {
        "id": f"link_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        **payload.model_dump(),
        "created_at": now_iso(),
    }

    links = load_json(LINKS_FILE)
    links.append(link)
    save_json(LINKS_FILE, links)

    sheets = load_json(SHEETS_FILE)
    sheets[payload.source_sheet_id].setdefault("links", []).append(link["id"])
    sheets[payload.source_sheet_id]["updated_at"] = now_iso()
    save_json(SHEETS_FILE, sheets)

    return link


@app.get("/api/memory")
def read_shared_memory(request: Request):
    user_id = require_user(request)
    memory = load_json(MEMORY_FILE)
    return {"items": memory.get(user_id, [])}


@app.post("/api/memory")
def add_shared_memory(request: Request, payload: MemoryCreate):
    user_id = require_user(request)

    if payload.source_sheet_id:
        require_owned_sheet(payload.source_sheet_id, user_id)

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="ข้อความความจำว่างไม่ได้")

    item = {
        "id": f"memory_{uuid.uuid4().hex[:12]}",
        "text": text,
        "source_sheet_id": payload.source_sheet_id,
        "importance": max(1, min(int(payload.importance), 5)),
        "created_at": now_iso(),
    }

    memory = load_json(MEMORY_FILE)
    memory.setdefault(user_id, []).append(item)
    save_json(MEMORY_FILE, memory)
    return item


@app.post("/api/sheets/{sheet_id}/core-memory")
def add_sheet_core_memory(request: Request, sheet_id: str, payload: MemoryCreate):
    user_id = require_user(request)
    require_owned_sheet(sheet_id, user_id)

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="ข้อความแก่นความจำว่างไม่ได้")

    item = {
        "id": f"core_{uuid.uuid4().hex[:12]}",
        "text": text,
        "importance": max(1, min(int(payload.importance), 5)),
        "created_at": now_iso(),
    }

    sheets = load_json(SHEETS_FILE)
    sheets[sheet_id].setdefault("core_memory", []).append(item)
    sheets[sheet_id]["updated_at"] = now_iso()
    save_json(SHEETS_FILE, sheets)
    return item


@app.get("/api/sheets/{sheet_id}/context")
def read_context(request: Request, sheet_id: str):
    user_id = require_user(request)
    sheet = require_owned_sheet(sheet_id, user_id)
    return {"items": sheet.get("context", [])}


@app.post("/api/sheets/{sheet_id}/context")
def add_context(request: Request, sheet_id: str, payload: ContextCreate):
    user_id = require_user(request)
    require_owned_sheet(sheet_id, user_id)

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="ข้อความว่างไม่ได้")

    item = {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "role": payload.role,
        "text": text,
        "created_at": now_iso(),
    }

    sheets = load_json(SHEETS_FILE)
    sheets[sheet_id].setdefault("context", []).append(item)
    sheets[sheet_id].setdefault("history", []).append(item)
    sheets[sheet_id]["updated_at"] = now_iso()
    save_json(SHEETS_FILE, sheets)

    chats = load_json(CHATS_FILE)
    chats.setdefault(sheet_id, []).append(item)
    save_json(CHATS_FILE, chats)
    return item


@app.get("/api/settings")
def read_settings(request: Request):
    user_id = require_user(request)
    settings = get_user_settings(user_id)
    return {
        **settings,
        "api_key": "••••••••" if settings.get("api_key") else "",
    }


@app.patch("/api/settings")
def update_settings(request: Request, payload: SettingsUpdate):
    user_id = require_user(request)
    settings = load_json(SETTINGS_FILE)
    current = settings.setdefault(user_id, get_user_settings(user_id))

    current["api_provider"] = payload.api_provider.strip()
    if payload.api_key.strip():
        current["api_key"] = payload.api_key.strip()

    save_json(SETTINGS_FILE, settings)
    return {
        **current,
        "api_key": "••••••••" if current.get("api_key") else "",
    }



@app.post("/api/sheets/{sheet_id}/connection")
def update_sheet_connection(
    request: Request,
    sheet_id: str,
    payload: SheetUpdate,
):
    user_id = current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")

    sheets = load_json(SHEETS_FILE)
    sheet = sheets.get(sheet_id)

    if not sheet:
        raise HTTPException(status_code=404, detail="ไม่พบแผ่นงาน")

    if sheet.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์แก้ไขแผ่นนี้")

    if payload.sender_code is not None:
        sheet["sender_code"] = payload.sender_code.strip()

    if payload.receiver_code is not None:
        sheet["receiver_code"] = payload.receiver_code.strip()

    if payload.warp_target is not None:
        sheet["warp_target"] = payload.warp_target.strip()

    sheet["updated_at"] = now_iso()
    sheets[sheet_id] = sheet
    save_json(SHEETS_FILE, sheets)

    return {
        "ok": True,
        "sheet_id": sheet_id,
        "sender_code": sheet.get("sender_code", ""),
        "receiver_code": sheet.get("receiver_code", ""),
        "warp_target": sheet.get("warp_target", ""),
    }


@app.get("/api/health")
def health():
    return JSONResponse({"ok": True, "app": APP_NAME, "time": now_iso()})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8032, reload=True)

# =========================
# INFINI MEMORY V1
# =========================

INFINI_MEMORY_FILE = DATA_DIR / "infini_memory.json"


def load_infini_memory() -> dict:
    if not INFINI_MEMORY_FILE.exists():
        save_json(INFINI_MEMORY_FILE, {})
    return load_json(INFINI_MEMORY_FILE)


@app.get("/api/infini-memory")
def get_infini_memory(request: Request):
    user_id = require_user(request)
    memory = load_infini_memory()

    return {
        "messages": memory.get(user_id, [])
    }


@app.post("/api/infini-memory")
async def save_infini_memory(request: Request):
    user_id = require_user(request)
    payload = await request.json()

    text = str(payload.get("text", "")).strip()
    role = str(payload.get("role", "user")).strip()
    mode = str(payload.get("mode", "ai")).strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="ข้อความว่าง",
        )

    if role not in {"user", "assistant"}:
        role = "user"

    memory = load_infini_memory()
    messages = memory.setdefault(user_id, [])

    messages.append(
        {
            "role": role,
            "mode": mode,
            "text": text,
            "created_at": now_iso(),
        }
    )

    # เก็บล่าสุด 200 ข้อความต่อผู้ใช้
    memory[user_id] = messages[-200:]
    save_json(INFINI_MEMORY_FILE, memory)

    return {
        "ok": True,
        "message": memory[user_id][-1],
    }

# =========================
# INFINI KNOWLEDGE V1
# =========================

INFINI_KNOWLEDGE_FILE = DATA_DIR / "infini_knowledge.json"


@app.post("/api/infini-knowledge/ask")
async def ask_infini_knowledge(request: Request):
    require_user(request)

    payload = await request.json()
    question = str(payload.get("question", "")).strip().lower()

    if not question:
        raise HTTPException(status_code=400, detail="คำถามว่าง")

    knowledge = load_json(INFINI_KNOWLEDGE_FILE)

    best_answer = None
    best_score = 0

    for item in knowledge.values():
        score = 0

        for keyword in item.get("keywords", []):
            keyword_text = str(keyword).strip().lower()

            if keyword_text and keyword_text in question:
                score += len(keyword_text)

        if score > best_score:
            best_score = score
            best_answer = item.get("answer")

    if not best_answer:
        best_answer = (
            "ตอนนี้ผมยังไม่มีข้อมูลเรื่องนี้ในความรู้กลางของ INFINI "
            "แต่สามารถเพิ่มข้อมูลนี้เข้าไปได้ครับ"
        )

    return {
        "answer": best_answer,
        "matched": best_score > 0
    }

# INFINI_DESIGN_CENTER_V1

# =========================
# INFINI DESIGN CENTER V1
# =========================

@app.post("/api/designer/apply")
async def apply_infini_design(
    request: Request,
    sheet_id: str = Form(...),
    file: UploadFile | None = File(None),
    sheet_type: str = Form(""),
    zone_slug: str = Form(""),
    media_role: str = Form(""),
    target_url: str = Form(""),
    visibility: str = Form(""),
    shop_enabled: str = Form(""),
    payment_enabled: str = Form(""),
):
    user_id = current_user_id(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="กรุณาเข้าสู่ระบบ",
        )

    sheets = load_json(SHEETS_FILE)
    sheet = sheets.get(sheet_id)

    if not sheet:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบแผ่นงาน",
        )

    if sheet.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="ไม่มีสิทธิ์แก้ไขแผ่นนี้",
        )

    # แก้เฉพาะช่องที่ผู้ใช้เลือกหรือกรอก
    clean_sheet_type = sheet_type.strip().lower()
    clean_zone_slug = zone_slug.strip()
    clean_media_role = media_role.strip().lower()
    clean_target_url = target_url.strip()
    clean_visibility = visibility.strip().lower()

    if clean_sheet_type:
        allowed_types = {
            "infini_space",
            "zone",
            "id_home",
            "subsheet",
        }

        if clean_sheet_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="ประเภทแผ่นไม่ถูกต้อง",
            )

        sheet["sheet_type"] = clean_sheet_type

    if clean_zone_slug:
        sheet["zone_slug"] = clean_zone_slug
        sheet["zone_name"] = clean_zone_slug.replace("-", " ")

    if clean_target_url:
        sheet["target_url"] = clean_target_url

    if clean_visibility:
        if clean_visibility not in {"private", "public"}:
            raise HTTPException(
                status_code=400,
                detail="สถานะการเผยแพร่ไม่ถูกต้อง",
            )

        sheet["visibility"] = clean_visibility

    if shop_enabled:
        sheet["shop_enabled"] = (
            shop_enabled.strip().lower()
            in {"1", "true", "yes", "on"}
        )

    if payment_enabled:
        sheet["payment_enabled"] = (
            payment_enabled.strip().lower()
            in {"1", "true", "yes", "on"}
        )

    # อัปโหลดไฟล์เมื่อมีการเลือกไฟล์
    if file and file.filename:
        content_type = str(file.content_type or "").lower()

        if not (
            content_type.startswith("image/")
            or content_type.startswith("video/")
        ):
            raise HTTPException(
                status_code=400,
                detail="รองรับเฉพาะรูปภาพและวิดีโอ",
            )

        suffix = Path(file.filename).suffix.lower()

        if not suffix:
            suffix = (
                ".mp4"
                if content_type.startswith("video/")
                else ".jpg"
            )

        filename = (
            f"design_{user_id}_"
            f"{uuid.uuid4().hex[:16]}{suffix}"
        )

        destination = UPLOADS_DIR / filename

        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        media_item = {
            "id": uuid.uuid4().hex,
            "url": f"/uploads/{filename}",
            "filename": file.filename,
            "content_type": content_type,
            "role": clean_media_role or "gallery",
            "created_at": now_iso(),
        }

        sheet.setdefault("media", []).append(media_item)

        # บันทึกตัวชี้สื่อหลักแยกไว้ด้วย
        if clean_media_role in {
            "main",
            "background",
            "zone_cover",
            "card",
        }:
            sheet["active_media_url"] = media_item["url"]
            sheet["active_media_type"] = content_type
            sheet["active_media_role"] = clean_media_role

    sheet["updated_at"] = now_iso()
    sheets[sheet_id] = sheet
    save_json(SHEETS_FILE, sheets)

    return {
        "ok": True,
        "sheet_id": sheet_id,
        "sheet": public_sheet(sheet),
    }

# =========================
# INFINI CHAT CENTER V1
# =========================

@app.get("/chat-center", response_class=HTMLResponse)
def chat_center_page(request: Request):
    user_id = current_user_id(request)

    if not user_id:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    return templates.TemplateResponse(
        request,
        "chat_center.html",
        {
            "request": request,
        },
    )

from member_system import setup_member_system
setup_member_system(app)

from remote_sheet import install_remote_sheet
install_remote_sheet(app)

from remote_sheet_tools import install_remote_sheet_tools
install_remote_sheet_tools(app)


# infini_custom_rooms_v1
@app.get("/media-library", response_class=HTMLResponse)
async def media_library_page():
    return """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>คลังภาพ INFINI</title>
<style>
body{margin:0;background:#020814;color:white;font-family:Arial;padding:24px}
.card{border:1px solid #17456b;border-radius:22px;padding:18px;background:#071426;margin-bottom:18px}
button{width:100%;padding:16px;border:0;border-radius:18px;background:linear-gradient(90deg,#35c8ff,#8b5cff);font-weight:800}
input{display:none}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:16px;border:1px solid #17456b}
a{color:#7fd8ff;text-decoration:none}
</style></head><body>
<a href="/control-room">← กลับห้องควบคุม</a>
<h1>คลังภาพ INFINI</h1>
<div class="card">
<p>เก็บรูปของพื้นที่คุณไว้ก่อน</p>
<button onclick="pick()">⬆️ เพิ่มรูป</button>
<input id="file" type="file" accept="image/*" multiple>
</div>
<div id="grid" class="grid"></div>
<script>
const key="infini_media_library_images";
const file=document.getElementById("file");
function load(){const arr=JSON.parse(localStorage.getItem(key)||"[]");grid.innerHTML=arr.map(x=>`<img src="${x}">`).join("")}
function pick(){file.click()}
file.onchange=()=>{let arr=JSON.parse(localStorage.getItem(key)||"[]");[...file.files].forEach(f=>{const r=new FileReader();r.onload=()=>{arr.push(r.result);localStorage.setItem(key,JSON.stringify(arr));load()};r.readAsDataURL(f)})}
load()
</script></body></html>
"""

@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page():
    return """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ธุรกรรม INFINI</title>
<style>
body{margin:0;background:#020814;color:white;font-family:Arial;padding:24px}
.card{border:1px solid #17456b;border-radius:22px;padding:24px;background:#071426}
a{color:#7fd8ff;text-decoration:none}
</style></head><body>
<a href="/control-room">← กลับห้องควบคุม</a>
<h1>ธุรกรรม</h1>
<div class="card">
<h2>ยังไม่มีรายการ</h2>
<p>ห้องนี้เตรียมไว้สำหรับลิงก์ การเชื่อมต่อ การขาย และประวัติธุรกรรมในอนาคต</p>
</div>
</body></html>
"""

@app.get("/api-room", response_class=HTMLResponse)
async def api_room_page():
    return """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>API ส่วนตัว</title>
<style>
body{margin:0;background:#020814;color:white;font-family:Arial;padding:24px}
.card{border:1px solid #17456b;border-radius:22px;padding:20px;background:#071426}
input{width:100%;box-sizing:border-box;padding:15px;border-radius:14px;border:1px solid #2b6b9a;background:#081321;color:white;margin:12px 0}
button{width:100%;padding:16px;border:0;border-radius:18px;background:linear-gradient(90deg,#35c8ff,#8b5cff);font-weight:800}
a{color:#7fd8ff;text-decoration:none}
small{display:block;margin-top:12px;color:#90ffb0}
</style></head><body>
<a href="/control-room">← กลับห้องควบคุม</a>
<h1>API ส่วนตัว</h1>
<div class="card">
<label>วาง API Key หรือ API URL ของคุณ</label>
<input id="apiKey" type="password" placeholder="API Key / API URL">
<button onclick="saveApi()">🔗 เชื่อมต่อ</button>
<small id="status"></small>
</div>
<script>
const key="infini_private_api_key";
apiKey.value=localStorage.getItem(key)||"";
function saveApi(){
 if(!apiKey.value.trim()){alert("กรุณาวาง API");return}
 localStorage.setItem(key,apiKey.value.trim());
 status.innerText="✅ บันทึก API แล้ว";
}
</script></body></html>
"""

# =========================
# INFINI PUBLIC USE CASES V2
# ระบบส่วนกลางอัปโหลดภาพปกและวิดีโอให้แต่ละสายงาน
# =========================

USE_CASE_CATALOG = [
    {
        "slug": "shop",
        "icon": "🛍️",
        "title": "ร้านค้าและผู้ขายสินค้า",
        "description": "จัดพื้นที่ขายสินค้า แบ่งหมวด และพาคนจากโซเชียลเข้ามาดูร้านของคุณ",
    },
    {
        "slug": "collector",
        "icon": "🧸",
        "title": "Art Toy และนักสะสม",
        "description": "สร้างห้องโชว์คอลเลกชัน เล่าเรื่องของแต่ละชิ้น และเลือกงานไปแสดงใน Zone",
    },
    {
        "slug": "fashion",
        "icon": "👕",
        "title": "เสื้อผ้าและแฟชั่น",
        "description": "นำเสนอคอลเลกชัน ลุคสินค้า และลิงก์สำหรับติดต่อหรือสั่งซื้อ",
    },
    {
        "slug": "creator",
        "icon": "🎨",
        "title": "ศิลปินและครีเอเตอร์",
        "description": "รวมผลงาน วิดีโอ เบื้องหลัง และช่องทางติดตามไว้ในพื้นที่เดียว",
    },
    {
        "slug": "investor",
        "icon": "📈",
        "title": "นักลงทุนและเจ้าของโครงการ",
        "description": "จัดพื้นที่นำเสนอแนวคิด โครงการ ความคืบหน้า และข้อมูลที่ต้องการให้ผู้ชมเห็น",
    },
    {
        "slug": "home-office",
        "icon": "🏢",
        "title": "โฮมออฟฟิศและผู้ให้บริการ",
        "description": "รวมบริการ ตัวอย่างงาน ขั้นตอนทำงาน และช่องทางติดต่อไว้หลังโปรไฟล์",
    },
    {
        "slug": "community",
        "icon": "👥",
        "title": "โรงเรียน ชุมชน และกิจกรรม",
        "description": "ใช้เป็นพื้นที่รวมกิจกรรม ผลงานสมาชิก ข่าวสาร และลิงก์ที่เกี่ยวข้อง",
    },
    {
        "slug": "portfolio",
        "icon": "🗂️",
        "title": "พอร์ตส่วนตัวและฟรีแลนซ์",
        "description": "แสดงผลงาน ทักษะ ประสบการณ์ และข้อมูลติดต่อให้ดูง่ายจากลิงก์เดียว",
    },
]


def get_service_admin_user_id() -> str | None:
    configured = os.getenv("INFINI_SERVICE_ADMIN_USER_ID", "").strip()
    if configured:
        return configured

    users = load_json(USERS_FILE)
    if not isinstance(users, dict):
        return None

    records = [
        item
        for item in users.values()
        if isinstance(item, dict) and item.get("id")
    ]
    if not records:
        return None

    records.sort(key=lambda item: str(item.get("created_at") or ""))
    return str(records[0]["id"])


def can_manage_use_cases(request: Request) -> bool:
    user_id = current_user_id(request)
    admin_user_id = get_service_admin_user_id()
    return bool(user_id and admin_user_id and user_id == admin_user_id)


def require_use_case_admin(request: Request) -> str:
    user_id = current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบเจ้าของก่อน")
    if not can_manage_use_cases(request):
        raise HTTPException(status_code=403, detail="เฉพาะเจ้าของระบบเท่านั้นที่แก้ไขหน้านี้ได้")
    return user_id


def allowed_use_case_slugs() -> set[str]:
    return {item["slug"] for item in USE_CASE_CATALOG}


def read_use_case_store() -> dict[str, Any]:
    stored = load_json(USE_CASES_FILE)
    return stored if isinstance(stored, dict) else {}


def delete_use_case_file(url: str) -> None:
    filename = Path(str(url or "")).name
    if filename:
        (USE_CASE_UPLOADS_DIR / filename).unlink(missing_ok=True)


def build_use_case_items() -> list[dict[str, Any]]:
    stored = read_use_case_store()
    items: list[dict[str, Any]] = []
    for base in USE_CASE_CATALOG:
        media = stored.get(base["slug"], {})
        if not isinstance(media, dict):
            media = {}
        items.append({**base, **media})
    return items


async def save_use_case_upload(
    *,
    file: UploadFile,
    slug: str,
    kind: str,
    allowed_suffixes: set[str],
    required_content_prefix: str,
    fallback_suffix: str,
    max_bytes: int,
) -> tuple[str, str, str, int]:
    original_name = Path(file.filename or f"{kind}{fallback_suffix}").name
    suffix = Path(original_name).suffix.lower()
    content_type = str(file.content_type or "").lower()

    if not content_type.startswith(required_content_prefix) and suffix not in allowed_suffixes:
        label = "รูปภาพ" if kind == "image" else "วิดีโอ"
        raise HTTPException(status_code=400, detail=f"รองรับเฉพาะไฟล์{label}")

    if suffix not in allowed_suffixes:
        suffix = fallback_suffix

    USE_CASE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{slug}-{kind}-{uuid.uuid4().hex[:16]}{suffix}"
    destination = USE_CASE_UPLOADS_DIR / stored_name
    total = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    limit_mb = max_bytes // (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"ไฟล์ต้องมีขนาดไม่เกิน {limit_mb} MB",
                    )
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return stored_name, original_name, content_type, total


@app.get("/use-cases", response_class=HTMLResponse)
def use_cases_page(request: Request):
    return templates.TemplateResponse(
        request,
        "use_cases.html",
        {
            "request": request,
            "items": build_use_case_items(),
            "can_manage": can_manage_use_cases(request),
        },
    )


@app.post("/api/use-cases/{slug}/image")
async def upload_use_case_image(
    request: Request,
    slug: str,
    file: UploadFile = File(...),
):
    require_use_case_admin(request)
    if slug not in allowed_use_case_slugs():
        raise HTTPException(status_code=404, detail="ไม่พบสายงานนี้")

    stored_name, original_name, content_type, total = await save_use_case_upload(
        file=file,
        slug=slug,
        kind="image",
        allowed_suffixes={".jpg", ".jpeg", ".png", ".webp", ".gif"},
        required_content_prefix="image/",
        fallback_suffix=".jpg",
        max_bytes=15 * 1024 * 1024,
    )

    stored = read_use_case_store()
    old_item = stored.get(slug, {})
    if not isinstance(old_item, dict):
        old_item = {}
    delete_use_case_file(str(old_item.get("image_url") or ""))

    item = {
        **old_item,
        "image_url": f"/uploads/use_cases/{stored_name}",
        "image_name": original_name,
        "image_type": content_type or "image/jpeg",
        "image_size": total,
        "image_updated_at": now_iso(),
    }
    stored[slug] = item
    save_json(USE_CASES_FILE, stored)
    return {"ok": True, "slug": slug, **item}


@app.delete("/api/use-cases/{slug}/image")
def delete_use_case_image(request: Request, slug: str):
    require_use_case_admin(request)
    if slug not in allowed_use_case_slugs():
        raise HTTPException(status_code=404, detail="ไม่พบสายงานนี้")

    stored = read_use_case_store()
    item = stored.get(slug, {})
    if not isinstance(item, dict):
        item = {}
    delete_use_case_file(str(item.get("image_url") or ""))
    for key in ("image_url", "image_name", "image_type", "image_size", "image_updated_at"):
        item.pop(key, None)
    stored[slug] = item
    save_json(USE_CASES_FILE, stored)
    return {"ok": True, "slug": slug}


@app.post("/api/use-cases/{slug}/video")
async def upload_use_case_video(
    request: Request,
    slug: str,
    file: UploadFile = File(...),
):
    require_use_case_admin(request)
    if slug not in allowed_use_case_slugs():
        raise HTTPException(status_code=404, detail="ไม่พบสายงานนี้")

    stored_name, original_name, content_type, total = await save_use_case_upload(
        file=file,
        slug=slug,
        kind="video",
        allowed_suffixes={".mp4", ".webm", ".mov", ".m4v"},
        required_content_prefix="video/",
        fallback_suffix=".mp4",
        max_bytes=250 * 1024 * 1024,
    )

    stored = read_use_case_store()
    old_item = stored.get(slug, {})
    if not isinstance(old_item, dict):
        old_item = {}
    delete_use_case_file(str(old_item.get("video_url") or ""))

    item = {
        **old_item,
        "video_url": f"/uploads/use_cases/{stored_name}",
        "video_name": original_name,
        "video_type": content_type or "video/mp4",
        "video_size": total,
        "video_updated_at": now_iso(),
    }
    stored[slug] = item
    save_json(USE_CASES_FILE, stored)
    return {"ok": True, "slug": slug, **item}


@app.delete("/api/use-cases/{slug}/video")
def delete_use_case_video(request: Request, slug: str):
    require_use_case_admin(request)
    if slug not in allowed_use_case_slugs():
        raise HTTPException(status_code=404, detail="ไม่พบสายงานนี้")

    stored = read_use_case_store()
    item = stored.get(slug, {})
    if not isinstance(item, dict):
        item = {}
    delete_use_case_file(str(item.get("video_url") or ""))
    for key in ("video_url", "video_name", "video_type", "video_size", "video_updated_at", "updated_at"):
        item.pop(key, None)
    stored[slug] = item
    save_json(USE_CASES_FILE, stored)
    return {"ok": True, "slug": slug}


@app.get("/service", response_class=HTMLResponse)
async def service_page(request: Request):
    return templates.TemplateResponse(request, "service.html", {"request": request})

# >>> INFINI_COMMERCE_SUITE_2_8032_V1 >>>
from commerce_suite_8032 import install_commerce_suite

install_commerce_suite(
    app,
    base_dir=BASE_DIR,
    current_user_id=current_user_id,
    load_json=load_json,
    save_json=save_json,
    sheets_file=SHEETS_FILE,
)
# <<< INFINI_COMMERCE_SUITE_2_8032_V1 <<<

# === INFINI CLEAN: CENTRAL SHOP DIRECTORY ===
from infini_shop_directory_8033 import install_infini_shop_directory_8033
install_infini_shop_directory_8033(app)
