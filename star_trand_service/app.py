from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Any
import hashlib
from storage import get_config, save_config, get_memory, update_memory
from engine import execute, STYLE_AGENTS

app = FastAPI(title="INFINI STAR TRAND", version="1.0")


def _mask(v: str) -> str:
    if not v: return ""
    if len(v) < 9: return "••••••••"
    return v[:3] + "••••••••" + v[-3:]


def _memory_key(user_key: str, scope: str, account_label: str) -> str:
    raw = f"{user_key or 'local'}::{scope or '/'}::{account_label or ''}"
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:24]

@app.get("/health")
async def health():
    cfg = get_config()
    return {"ok": True, "service": "STAR_TRAND_V1", "llm_configured": bool(cfg.get("api_key")), "styles": STYLE_AGENTS}

@app.get("/v1/config")
async def config_get():
    cfg = get_config()
    return {"ok": True, "base_url": cfg.get("base_url", "https://api.openai.com/v1"), "model": cfg.get("model", "gpt-5-mini"), "api_configured": bool(cfg.get("api_key")), "api_masked": _mask(str(cfg.get("api_key") or ""))}

@app.post("/v1/config")
async def config_post(request: Request):
    p = await request.json()
    old = get_config()
    key = str(p.get("api_key") or "").strip()
    cfg = save_config({
        "base_url": str(p.get("base_url") or old.get("base_url") or "https://api.openai.com/v1").strip(),
        "model": str(p.get("model") or old.get("model") or "gpt-5-mini").strip(),
        "api_key": key if key else old.get("api_key", ""),
    })
    return {"ok": True, "api_configured": bool(cfg.get("api_key")), "api_masked": _mask(str(cfg.get("api_key") or ""))}

@app.post("/v1/memory")
async def memory_post(request: Request):
    p = await request.json()
    key = _memory_key(str(p.get("user_key") or "local"), str(p.get("scope") or "/"), str(p.get("account_label") or ""))
    mem = update_memory(key, p.get("patch") if isinstance(p.get("patch"), dict) else {})
    return {"ok": True, "memory_key": key, "memory": mem}

@app.get("/v1/memory")
async def memory_get(user_key: str = "local", scope: str = "/", account_label: str = ""):
    key = _memory_key(user_key, scope, account_label)
    return {"ok": True, "memory_key": key, "memory": get_memory(key)}

@app.post("/v1/command")
async def command(request: Request):
    p: dict[str, Any] = await request.json()
    text = str(p.get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty command"}, status_code=400)
    user_key = str(p.get("user_key") or "local")
    scope = str(p.get("scope") or "/")
    account_label = str(p.get("account_label") or "")
    context = p.get("context") if isinstance(p.get("context"), dict) else {}
    context.setdefault("scope", scope)
    context.setdefault("account_label", account_label)
    key = _memory_key(user_key, scope, account_label)
    result = execute(text, key, context, p.get("parsed_command") if isinstance(p.get("parsed_command"), dict) else {}, p.get("market_data") if isinstance(p.get("market_data"), dict) else None)
    return result
