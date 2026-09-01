import os, json, hashlib, random
from datetime import datetime
from fastapi import Request, Form, UploadFile, File, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

DATA_FILE = "members.json"
UPLOAD_DIR = "uploads/profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_db():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def setup_member_system(app):
    if os.path.exists("uploads"):
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    @app.get("/register", response_class=HTMLResponse)
    async def reg_page():
        return "<h3>Register Page Ready</h3><a href='/login'>Login</a>"
