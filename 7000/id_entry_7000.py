from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from pathlib import Path
from itsdangerous import BadSignature, URLSafeSerializer
import uuid
import json
import os
import time

# === INFINI_7000_SHARED_ID_BRIDGE_V1 ===
BASE_DIR = Path(__file__).resolve().parent
# Must point at 8032/ (where 8032/main.py keeps its data folder), not the
# project root — the old default here had no "data" folder to find at all,
# which desynced session secrets between 7000 and 8032 and broke login.
INFINI_8032_ROOT = Path(
    os.getenv("INFINI_8032_ROOT", str(BASE_DIR.parent / "8032"))
).expanduser().resolve()
SHARED_DATA_DIR = INFINI_8032_ROOT / "data"
USERS_FILE = SHARED_DATA_DIR / "users.json"
SESSION_SECRET_FILE = SHARED_DATA_DIR / "infini_session_secret.txt"
PUBLIC_LINKS_FILE = SHARED_DATA_DIR / "public_links.json"
LEGACY_STATE_FILE = BASE_DIR / "id_entry_7000_state.json"
USER_STATE_DIR = BASE_DIR / "data" / "id_users"
LEGACY_CLAIM_FILE = USER_STATE_DIR / ".legacy_claimed"
UPLOAD_DIR = BASE_DIR / "id_entry_7000_uploads"
USER_STATE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _session_signer() -> URLSafeSerializer:
    if not SESSION_SECRET_FILE.exists():
        SHARED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_SECRET_FILE.write_text(
            os.getenv("INFINI_SESSION_SECRET") or "change-this-secret-before-public-use",
            encoding="utf-8",
        )
    secret = SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()
    return URLSafeSerializer(secret, salt="infini-session")


# === INFINI_PUBLIC_7000_AUTH_BRIDGE_V2 ===
def _read_public_links() -> dict:
    try:
        data = json.loads(PUBLIC_LINKS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _public_8032_login_url() -> str:
    # proxy.py serves the 8032 app at the "/8032" path prefix on the SAME
    # public domain as this 7000 app, so a relative path always works
    # correctly in production. INFINI_8032_PUBLIC_URL / public_links.json
    # are kept only as an override for local/standalone (non-proxied) runs.
    override = str(
        os.getenv("INFINI_8032_PUBLIC_URL")
        or _read_public_links().get("public_8032_url")
        or ""
    ).strip().rstrip("/")
    if override.startswith(("http://", "https://")):
        return override + "/login"
    return "/8032/login"
# === END INFINI_PUBLIC_7000_AUTH_BRIDGE_V2 ===


def _load_users() -> dict:
    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _current_user_id(request: Request) -> str | None:
    token = request.cookies.get("infini_session")
    if not token:
        return None
    try:
        payload = _session_signer().loads(token)
    except BadSignature:
        return None
    user_id = str(payload.get("user_id") or "").strip()
    if not user_id or user_id not in _load_users():
        return None
    return user_id


def _require_user_id(request: Request) -> str:
    user_id = _current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบผ่าน INFINI")
    return user_id


def _safe_user_id(user_id: str) -> str:
    return "".join(ch for ch in user_id if ch.isalnum() or ch in "-_")[:80] or "member"


def _member_identity(user_id: str) -> dict:
    member = _load_users().get(user_id, {})
    username = str(member.get("username") or "INFINI MEMBER")
    infini_id = str(member.get("infini_id") or "").strip()
    if not infini_id:
        raw = user_id.removeprefix("user_").replace("-", "").replace("_", "")
        infini_id = "INF-" + (raw[:8] or "00000001").upper()
    return {
        "displayName": username,
        "username": username,
        "infiniId": infini_id,
        "level": "MEMBER",
    }


def _state_path(user_id: str) -> Path:
    return USER_STATE_DIR / f"{_safe_user_id(user_id)}.json"


def _load_user_state(user_id: str) -> dict:
    path = _state_path(user_id)
    data = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}
    elif LEGACY_STATE_FILE.exists() and not LEGACY_CLAIM_FILE.exists():
        try:
            legacy = json.loads(LEGACY_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(legacy, dict):
                data = legacy
                LEGACY_CLAIM_FILE.write_text(user_id, encoding="utf-8")
        except Exception:
            data = {}
    identity = _member_identity(user_id)
    data.setdefault("displayName", identity["displayName"])
    data["username"] = identity["username"]
    data["infiniId"] = identity["infiniId"]
    data["level"] = identity["level"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _save_user_state(user_id: str, data: dict) -> dict:
    clean = dict(data or {})
    identity = _member_identity(user_id)
    clean.setdefault("displayName", identity["displayName"])
    clean["username"] = identity["username"]
    clean["infiniId"] = identity["infiniId"]
    clean["level"] = identity["level"]
    path = _state_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean, ensure_ascii=False), encoding="utf-8")
    return clean
# === END INFINI_7000_SHARED_ID_BRIDGE_V1 ===

ID_ENTRY_HTML = r'''
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>INFINI ID HOME</title>
<style>
:root{
  --bg:#050505;
  --panel:#0b0b0d;
  --panel2:#101014;
  --line:rgba(255,255,255,.11);
  --accent:#ff8a1f;
  --accent2:#ffc067;
  --text:#f7f7f7;
  --muted:#9d9da5;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;min-height:100%;background:#000;color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
body{overflow-x:hidden}
a{color:inherit}
button,input,textarea{font:inherit}
.app{min-height:100vh;background:radial-gradient(circle at 75% 0,rgba(255,116,0,.12),transparent 28%),linear-gradient(#050505,#000);padding-bottom:104px}
.topbar{position:sticky;top:0;z-index:60;height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:rgba(0,0,0,.88);border-bottom:1px solid var(--line);backdrop-filter:blur(16px)}
.brand{display:flex;align-items:center;gap:9px;font-weight:950;letter-spacing:.08em;font-size:14px}
.brandMark{width:28px;height:28px;border:1px solid rgba(255,138,31,.7);border-radius:9px;display:grid;place-items:center;color:var(--accent);font-size:17px}
.topActions{display:flex;gap:8px}.iconBtn{width:38px;height:38px;border:1px solid var(--line);border-radius:12px;background:#0b0b0d;color:#ddd;display:grid;place-items:center;text-decoration:none}
.wrap{max-width:720px;margin:auto;padding:14px 14px 30px}
.hero{position:relative;min-height:360px;border:1px solid rgba(255,138,31,.36);border-radius:28px;overflow:hidden;background:radial-gradient(circle at 70% 20%,#2b1609,#0b0b0d 55%,#050505);box-shadow:0 22px 70px rgba(0,0,0,.48);cursor:pointer;touch-action:pan-y;user-select:none;-webkit-user-select:none}
.heroMedia{position:absolute;inset:0}.heroMedia img,.heroMedia video{width:100%;height:100%;object-fit:cover;display:block}.heroMedia:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.06),rgba(0,0,0,.22) 52%,rgba(0,0,0,.9))}
.heroEmpty{position:absolute;inset:0;display:grid;place-items:center;text-align:center;color:#777}.heroEmpty b{display:block;color:#ddd;margin-top:8px}.heroEmpty .plus{font-size:38px;color:var(--accent)}
.heroContent{position:relative;z-index:3;min-height:360px;display:flex;align-items:flex-end;justify-content:space-between;gap:14px;padding:20px;pointer-events:none}
.heroIdentity{min-width:0;max-width:76%;text-shadow:0 3px 18px #000}.eyebrow{font-size:11px;color:var(--accent);font-weight:950;letter-spacing:.14em}.profileName{font-size:27px;font-weight:1000;line-height:1.05;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.profileMeta{font-size:12px;color:#e2e2e5;margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.uploadWord{flex:0 0 auto;color:#fff;font-size:12px;font-weight:950;letter-spacing:.05em;text-shadow:0 2px 12px #000;pointer-events:auto;cursor:pointer;font-family:inherit;outline:none;-webkit-tap-highlight-color:transparent}.hero.pressing{border-color:rgba(255,138,31,.82);transform:scale(.997)}
.section{margin-top:16px}.sectionHead{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 2px 10px}.sectionHead h2{margin:0;font-size:15px;letter-spacing:.02em}.sectionHead span,.sectionHead a{color:#888;font-size:12px;text-decoration:none}
.tools{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.tool{min-width:0;min-height:112px;padding:12px 7px;border:1px solid var(--line);border-radius:19px;background:linear-gradient(160deg,#111116,#08080a);text-decoration:none;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px}.tool:active{transform:scale(.97)}.toolIcon{width:43px;height:43px;border-radius:14px;display:grid;place-items:center;border:1px solid rgba(255,138,31,.28);background:rgba(255,138,31,.08);color:var(--accent);font-size:20px}.tool b{font-size:12px}.tool small{display:block;color:#777;font-size:9px;line-height:1.2}
.creative-card{position:relative;min-height:205px;display:flex;flex-direction:column;justify-content:flex-end;padding:18px;border:1px solid rgba(255,138,31,.38);border-radius:24px;overflow:hidden;background:radial-gradient(circle at 75% 20%,rgba(255,120,0,.2),transparent 35%),linear-gradient(145deg,#15100c,#080809 65%);cursor:pointer;touch-action:pan-y;user-select:none;-webkit-user-select:none;transition:transform .12s ease,border-color .12s ease}.creative-card.pressing{transform:scale(.991);border-color:rgba(255,138,31,.8)}.creativeMedia{position:absolute;inset:0}.creativeMedia img,.creativeMedia video{width:100%;height:100%;object-fit:cover;display:block}.creative-card:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.08) 15%,rgba(0,0,0,.9));pointer-events:none}.creativeText{position:relative;z-index:2;max-width:78%;pointer-events:none}.creativeText .mini{color:var(--accent);font-size:10px;font-weight:950;letter-spacing:.12em}.creativeText h2{margin:4px 0 6px;font-size:26px}.creativeText p{margin:0;color:#aaa;font-size:12px;line-height:1.5}.creativeUpload{position:absolute;right:18px;bottom:18px;z-index:3;color:#fff;font-size:12px;font-weight:950;letter-spacing:.04em;text-shadow:0 2px 12px #000;pointer-events:none}
.zones{display:grid;grid-template-columns:1fr 1fr;gap:12px}.zoneCard{position:relative;min-width:0;border:1px solid rgba(255,255,255,.13);border-radius:22px;background:#0b0b0d;overflow:hidden;cursor:pointer;touch-action:pan-y;user-select:none;-webkit-user-select:none;transition:transform .12s ease,border-color .12s ease}.zoneCard:active,.zoneCard.pressing{transform:scale(.982);border-color:rgba(255,138,31,.7)}.zoneMedia{position:relative;height:190px;background:linear-gradient(145deg,#151519,#08080a);display:grid;place-items:center;color:#75757d;text-align:center;overflow:hidden}.zoneMedia img,.zoneMedia video{width:100%;height:100%;object-fit:cover;display:block}.zoneMedia:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.02),rgba(0,0,0,.1));pointer-events:none}.zonePlaceholder{position:relative;z-index:1;padding:18px;color:#777;font-size:11px;line-height:1.4}.zonePlaceholder .zonePlus{display:block;color:var(--accent);font-size:30px;line-height:1;margin-bottom:8px}.zonePlaceholder strong{display:block;color:#d6d6da;font-size:12px;margin-bottom:4px}.zoneFooter{min-height:67px;padding:11px 13px 12px;border-top:1px solid rgba(255,255,255,.08);background:linear-gradient(180deg,#0c0c0f,#070708);display:flex;align-items:flex-end;justify-content:space-between;gap:8px}.zoneName{min-width:0}.zoneName b{display:block;color:var(--accent);font-size:12px;letter-spacing:.06em}.zoneName span{display:block;color:#aaa;font-size:10px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.zoneUpload{flex:0 0 auto;color:#fff;font-size:11px;font-weight:950;letter-spacing:.03em}
.latest{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(142px,42%);gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:4px}.workCard{scroll-snap-align:start;min-height:184px;border:1px solid var(--line);border-radius:19px;background:#0b0b0d;overflow:hidden;text-decoration:none}.workMedia{height:118px;background:#111;display:grid;place-items:center;color:#555}.workMedia img,.workMedia video{width:100%;height:100%;object-fit:cover;display:block}.workCopy{padding:10px}.workCopy b{display:block;font-size:12px}.workCopy span{display:block;color:#777;font-size:10px;margin-top:4px}.addWork{border-style:dashed;display:grid;place-items:center;text-align:center;color:#999;background:#08080a}.addWork strong{display:block;font-size:30px;color:var(--accent);font-weight:400}.addWork span{font-size:11px}
.profilePanel{display:none;margin-top:12px;padding:15px;border:1px solid var(--line);border-radius:22px;background:#0b0b0d}.profilePanel.show{display:block}.formGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.field label{display:block;color:#999;font-size:10px;margin:0 0 5px}.field input,.field textarea{width:100%;border:1px solid var(--line);border-radius:13px;background:#050506;color:#fff;padding:11px;outline:none}.field textarea{min-height:86px;resize:vertical}.field.full{grid-column:1/-1}.saveBtn{width:100%;min-height:48px;margin-top:10px;border:0;border-radius:14px;background:linear-gradient(135deg,#ff9d2f,#ff7411);color:#160800;font-weight:1000}
.bottomNav{position:fixed;left:50%;bottom:10px;z-index:80;width:min(680px,calc(100% - 20px));transform:translateX(-50%);display:grid;grid-template-columns:repeat(5,1fr);align-items:center;padding:8px;border:1px solid var(--line);border-radius:24px;background:rgba(7,7,8,.93);backdrop-filter:blur(18px);box-shadow:0 15px 40px rgba(0,0,0,.55)}.navItem{min-height:48px;border:0;background:transparent;color:#898990;text-decoration:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;font-size:9px}.navItem .nicon{font-size:18px;color:var(--accent)}.navItem.active{color:var(--accent)}.navPlus{width:54px;height:54px;margin:auto;border:1px solid rgba(255,138,31,.75);border-radius:18px;background:#0b0b0d;color:var(--accent);font-size:28px;box-shadow:0 0 24px rgba(255,120,0,.15)}
.uploadSheet{position:fixed;inset:0;z-index:120;display:none;flex-direction:column;background:#050506}.uploadSheet.show{display:flex}.sheetTop{height:60px;display:flex;align-items:center;justify-content:space-between;padding:0 15px;border-bottom:1px solid var(--line)}.sheetTop h2{margin:0;font-size:15px}.sheetClose{width:40px;height:40px;border:1px solid var(--line);border-radius:12px;background:#0b0b0d;color:#fff}.sheetBody{flex:1;overflow:auto;padding:16px}.uploadPreview{min-height:48vh;border:1px dashed rgba(255,138,31,.45);border-radius:24px;background:#0b0b0d;display:grid;place-items:center;text-align:center;color:#777;overflow:hidden}.uploadPreview img,.uploadPreview video{width:100%;height:48vh;object-fit:contain;background:#000}.sheetChoices{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}.choice{min-height:58px;border:1px solid var(--line);border-radius:15px;background:#0b0b0d;color:#ddd;font-weight:900}.choice.active{border-color:var(--accent);color:var(--accent2);background:rgba(255,138,31,.08)}.sheetSubmit{width:100%;min-height:54px;margin-top:12px;border:0;border-radius:16px;background:linear-gradient(135deg,#ff9d2f,#ff7411);color:#180800;font-weight:1000}.sheetSubmit:disabled{opacity:.45}.hidden{display:none!important}.toast{position:fixed;top:70px;left:50%;z-index:200;transform:translateX(-50%);display:none;padding:10px 14px;border:1px solid rgba(255,138,31,.45);border-radius:999px;background:#18100b;color:#ffd2a4;font-size:12px;font-weight:900}.toast.show{display:block}
.web-overlay{position:fixed;inset:0;z-index:160;display:none;flex-direction:column;background:#030303}.web-top{height:64px;display:flex;gap:8px;padding:10px;background:#000;border-bottom:1px solid var(--line)}.web-top input{flex:1;border-radius:14px;border:1px solid var(--line);background:#0b0b0d;color:white;padding:0 13px}.web-top button{border:1px solid var(--line);border-radius:13px;background:#0b0b0d;color:#fff;padding:0 13px}.web-frame{flex:1;border:0;background:white}
@media(max-width:520px){.zoneMedia{height:174px}.tools{grid-template-columns:repeat(5,1fr);gap:6px}.tool{min-height:104px;padding:10px 4px}.toolIcon{width:40px;height:40px}.tool b{font-size:10px}.hero{min-height:340px}.heroContent{min-height:340px}.profileName{font-size:21px}.formGrid{grid-template-columns:1fr}.field.full{grid-column:auto}.latest{grid-auto-columns:46%}}

/* === ZONE CARD FULL IMAGE PATCH === */
.zone-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:16px;
}

.zone-card,
.zone-box,
.zone-tile{
  position:relative !important;
  overflow:hidden !important;
  border-radius:24px !important;
  min-height:280px !important;
  background:#111 !important;
  border:1.5px solid rgba(255,140,40,.28) !important;
}

.zone-card img,
.zone-box img,
.zone-tile img,
.zone-thumb img,
.zone-photo img,
.zone-cover img,
.zone-preview img{
  position:absolute !important;
  inset:0 !important;
  width:100% !important;
  height:100% !important;
  object-fit:cover !important;
  display:block !important;
  border-radius:inherit !important;
}

.zone-thumb,
.zone-photo,
.zone-cover,
.zone-preview{
  position:absolute !important;
  inset:0 !important;
  width:100% !important;
  height:100% !important;
  overflow:hidden !important;
  border-radius:inherit !important;
}

.zone-card::after,
.zone-box::after,
.zone-tile::after{
  content:"";
  position:absolute;
  left:0; right:0; bottom:0;
  height:42%;
  background:linear-gradient(to top, rgba(0,0,0,.82), rgba(0,0,0,.18), rgba(0,0,0,0));
  pointer-events:none;
}

.zone-card .zone-info,
.zone-box .zone-info,
.zone-tile .zone-info,
.zone-card .zone-meta,
.zone-box .zone-meta,
.zone-tile .zone-meta,
.zone-card .zone-bottom,
.zone-box .zone-bottom,
.zone-tile .zone-bottom{
  position:absolute !important;
  left:16px !important;
  right:16px !important;
  bottom:14px !important;
  z-index:3 !important;
}

.zone-card .zone-title,
.zone-box .zone-title,
.zone-tile .zone-title{
  font-size:15px !important;
  font-weight:800 !important;
  line-height:1.15 !important;
  color:#ff9a3c !important;
  text-transform:uppercase !important;
  margin:0 0 4px 0 !important;
}

.zone-card .zone-subtitle,
.zone-box .zone-subtitle,
.zone-tile .zone-subtitle{
  color:rgba(255,255,255,.78) !important;
  font-size:12px !important;
  margin:0 !important;
}

.zone-card .zone-upload,
.zone-box .zone-upload,
.zone-tile .zone-upload{
  color:#fff !important;
  font-size:13px !important;
}


/* === INFINI ID POLISH + MINI EDITOR V1 === */
.app{padding-bottom:calc(150px + env(safe-area-inset-bottom))}
.wrap{padding:18px 16px 40px}
.hero{min-height:390px;max-height:560px;aspect-ratio:1/1.03}
.heroContent{min-height:390px;padding:22px}
.profileName{font-size:30px;letter-spacing:-.02em}
.profileMeta{font-size:13px}
.uploadWord{padding:8px 11px;border:1px solid rgba(255,255,255,.26);border-radius:999px;background:rgba(0,0,0,.34)}
.section{margin-top:22px}
.sectionHead{margin:0 3px 12px}.sectionHead h2{font-size:17px}.sectionHead span,.sectionHead a{font-size:12px}
.tools{grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;padding:2px 1px 6px}
.tool{min-height:116px;padding:11px 4px;border-radius:21px;justify-content:flex-start;gap:8px}
.toolIcon{width:43px;height:43px;flex:0 0 43px;border-radius:15px;font-size:20px}
.tool b{font-size:10.5px;line-height:1.2;min-height:26px;display:flex;align-items:center;justify-content:center}
.tool small{font-size:8.6px;line-height:1.25;min-height:22px}
.creative-card{min-height:235px;border-radius:26px}
.zones{gap:14px}.zoneCard{border-radius:24px}.zoneMedia{height:200px}.zoneFooter{min-height:72px;padding:12px 14px 13px}
.latest{padding-bottom:8px}.workCard{min-height:190px}
.bottomNav{bottom:calc(10px + env(safe-area-inset-bottom));width:min(680px,calc(100% - 24px));padding:9px 8px}
.iconBtn{transition:transform .12s ease,border-color .12s ease}.iconBtn:active{transform:scale(.94);border-color:rgba(255,138,31,.7)}

.controlSheet{position:fixed;inset:0;z-index:190;display:none;align-items:flex-end;background:rgba(0,0,0,.62);backdrop-filter:blur(5px)}
.controlSheet.show{display:flex}
.controlPanel{width:100%;max-height:86vh;overflow:auto;padding:16px 16px calc(24px + env(safe-area-inset-bottom));border:1px solid rgba(255,138,31,.32);border-bottom:0;border-radius:28px 28px 0 0;background:linear-gradient(180deg,#15100c,#070708 45%,#030303);box-shadow:0 -24px 70px rgba(0,0,0,.6)}
.controlTop{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}
.controlTop h2{margin:0;font-size:20px}.controlClose{width:42px;height:42px;border:1px solid var(--line);border-radius:14px;background:#0b0b0d;color:#fff}
.controlHint{margin:0 0 14px;color:#a8a8ae;font-size:12px;line-height:1.5}
.controlGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.controlAction{min-height:112px;padding:14px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,#111116,#09090b);color:#fff;text-align:left}
.controlAction strong{display:block;color:var(--accent);font-size:15px;margin-bottom:7px}.controlAction span{display:block;color:#999;font-size:11px;line-height:1.45}
.controlAction.wide{grid-column:1/-1;min-height:58px;text-align:center;color:#ffb7a8;border-color:rgba(255,102,74,.3)}

.layoutEditorBar{position:fixed;left:50%;bottom:calc(10px + env(safe-area-inset-bottom));z-index:230;width:min(700px,calc(100% - 18px));transform:translateX(-50%);display:none;padding:10px;border:1px solid rgba(255,138,31,.52);border-radius:22px;background:rgba(9,7,6,.96);backdrop-filter:blur(18px);box-shadow:0 18px 50px rgba(0,0,0,.65)}
.layoutEditorBar.show{display:block}
.editorSelected{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:2px 3px 9px;color:#ffd2a4;font-size:12px;font-weight:900}
.editorSelected small{color:#8f8f95;font-weight:700}
.editorTools{display:flex;gap:6px;overflow-x:auto;padding-bottom:8px;scrollbar-width:none}.editorTools::-webkit-scrollbar{display:none}
.editorBtn{flex:0 0 auto;min-width:42px;height:40px;padding:0 10px;border:1px solid var(--line);border-radius:12px;background:#111115;color:#eee;font-size:13px;font-weight:900}
.editorBtn:active{transform:scale(.95);border-color:var(--accent)}
.editorActions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.editorCancel,.editorSave{min-height:44px;border-radius:13px;font-weight:1000}.editorCancel{border:1px solid var(--line);background:#101014;color:#ddd}.editorSave{border:0;background:linear-gradient(135deg,#ffad43,#ff7814);color:#180800}
.editSelection{position:fixed;z-index:225;display:none;pointer-events:none;border:2px solid #ff9a2c;border-radius:6px;box-shadow:0 0 0 2px rgba(0,0,0,.5),0 0 24px rgba(255,120,0,.3)}
.editSelection.show{display:block}
.editResizeHandle{position:absolute;right:-13px;bottom:-13px;width:28px;height:28px;border:2px solid #140700;border-radius:9px;background:#ff9a2c;pointer-events:auto;touch-action:none;box-shadow:0 5px 16px rgba(0,0,0,.5)}
.editResizeHandle:before{content:"↘";position:absolute;inset:0;display:grid;place-items:center;color:#1b0800;font-size:14px;font-weight:1000}
body.layout-editing .bottomNav,body.layout-editing .infini-pic-upload{display:none!important}
body.layout-editing .heroContent,body.layout-editing .heroIdentity,body.layout-editing .creativeText,body.layout-editing .zoneFooter,body.layout-editing .zoneName{pointer-events:auto!important}
body.layout-editing [data-edit-id]{outline:1px dashed rgba(255,154,44,.36);outline-offset:2px;cursor:move!important;pointer-events:auto!important}
body.layout-editing [data-edit-id] img,body.layout-editing [data-edit-id] video{pointer-events:none!important}
body.layout-editing{padding-bottom:190px}

@media(max-width:520px){
  .wrap{padding:14px 14px 36px}.hero{min-height:350px;aspect-ratio:.92/1}.heroContent{min-height:350px;padding:19px}.profileName{font-size:25px}
  .tools{grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}.tool{min-height:110px;padding:10px 2px}.toolIcon{width:39px;height:39px;flex-basis:39px}.tool b{font-size:9.5px}.tool small{font-size:7.8px}.creative-card{min-height:220px}.zoneMedia{height:178px}.zones{gap:10px}
  .controlGrid{grid-template-columns:1fr}.controlAction.wide{grid-column:auto}
}

</style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand"><span class="brandMark">∞</span><span>INFINI ID</span></div>
    <div class="topActions">
      <button class="iconBtn" type="button" onclick="openSearch()" aria-label="ค้นหา">⌕</button>
      <button class="iconBtn" type="button" onclick="openControlCenter()" aria-label="ตั้งค่าและจัดหน้า">⚙</button>
      <a class="iconBtn" id="topbarLogoutBtn" href="/logout" aria-label="ออกจากระบบ" title="ออกจากระบบ">⏻</a>
    </div>
  </header>

  <main class="wrap">
    <section class="hero" id="idCoverBox" role="button" tabindex="0" aria-label="กดค้างเพื่ออัปโหลดภาพปก INFINI ID">
      <div class="heroMedia" id="heroMedia"></div>
      <div class="heroEmpty" id="idCoverEmpty"><div><div class="plus">＋</div><b>เพิ่มภาพปก INFINI ID</b></div></div>
      <div class="heroContent">
        <div class="heroIdentity">
          <div class="eyebrow">DIGITAL SPACE</div>
          <div class="profileName" id="profileNameView">INFINI MEMBER</div>
          <div class="profileMeta" id="profileMetaView">INF-000001 · MEMBER</div>
        </div>
        <button type="button" class="uploadWord" id="idCoverUploadBtn" aria-label="อัปโหลดภาพปก INFINI ID">⇧ อัปโหลด</button>
      </div>
    </section>

    <section class="profilePanel" id="profilePanel">
      <div class="formGrid">
        <div class="field"><label>ชื่อแสดงผล</label><input id="displayName" placeholder="INFINI MEMBER"></div>
        <div class="field"><label>USERNAME</label><input id="username" placeholder="infini"></div>
        <div class="field"><label>INFINI ID</label><input id="infiniId" placeholder="INF-000001"></div>
        <div class="field"><label>สถานะ / บทบาท</label><input id="level" placeholder="MEMBER"></div>
        <div class="field full"><label>คำอธิบาย</label><textarea id="bio" placeholder="เขียนรายละเอียดของตัวเอง ร้าน หรือโปรเจกต์"></textarea></div>
      </div>
      <button class="saveBtn" type="button" onclick="saveProfile()">บันทึกโปรไฟล์</button>
    </section>

    <section class="section">
      <div class="sectionHead"><h2>ทางลัด</h2><span>ใช้งานระบบเดิม</span></div>
      <div class="tools">
        <a class="tool" href="/friend-chat"><span class="toolIcon">◌</span><b>แชท</b><small>เพื่อนและคำขอ</small></a>
        <a class="tool" href="/poster"><span class="toolIcon">▢</span><b>โปสเตอร์</b><small>Mini App + เผยแพร่</small></a>
        <a class="tool" href="/"><span class="toolIcon">▣</span><b>ครีเอทีฟ</b><small>คลังและห้องงาน</small></a>
        <button class="tool" type="button" onclick="openUpload('gallery')"><span class="toolIcon">⇧</span><b>อัปโหลด</b><small>รูปหรือวิดีโอ</small></button>
        <a class="tool" href="/ai-chat"><span class="toolIcon">✦</span><b>AI</b><small>แชทและจัดร้าน</small></a>
        <a class="tool" href="/shop-scene-builder"><span class="toolIcon">▦</span><b>จัดร้าน V4</b><small>ฉากและสินค้า</small></a>
        <a class="tool" href="/image-generator"><span class="toolIcon">◉</span><b>สร้างภาพ</b><small>เลือกค่าย + API Key</small></a>
        <a class="tool" id="pointTowerLink" href="/8046/tower"><span class="toolIcon">★</span><b>Point</b><small>แต้มและการ์ด</small></a>
        <a class="tool" id="idHubLink" href="/id-hub"><span class="toolIcon">∞</span><b>รวมไอดี</b><small>สมาชิกทั้งหมด</small></a>
        <a class="tool" id="commerceSuiteLink" href="/8032/commerce"><span class="toolIcon">฿</span><b>Commerce</b><small>สินค้า ออเดอร์ และจอง</small></a>
        <a class="tool" id="logoutLink" href="/logout"><span class="toolIcon">⏻</span><b>ออกจากระบบ</b><small>สลับไปใช้ ID อื่น</small></a>
      </div>
    </section>

    <section class="section">
      <div class="sectionHead"><h2>พื้นที่สร้างสรรค์</h2><a href="/">เปิดคลังทั้งหมด</a></div>
      <article class="creative-card" id="creativeCard" role="link" tabindex="0" data-href="/creative-gate" aria-label="แตะเพื่อเข้า Creative Room กดค้างเพื่ออัปโหลดภาพ">
        <div class="creativeMedia" id="creativeMedia"></div>
        <div class="creativeText"><div class="mini">YOUR CONTENT SPACE</div><h2>CREATIVE ROOM</h2></div>
      </article>
    </section>

    <section class="section">
      <div class="sectionHead"><h2>โซนของฉัน</h2><a href="/zone-hub">ดู Zone Hub</a></div>
      <div class="zones" id="zoneGrid">
        <article class="zoneCard" role="link" tabindex="0" data-zone="private" data-href="/zone/private" aria-label="ZONE 1 PRIVATE ส่วนตัว — แตะเพื่อเข้า กดค้างเพื่ออัปโหลดรูป">
          <div class="zoneMedia" id="zoneMediaPrivate"><div class="zonePlaceholder"><span class="zonePlus">＋</span><strong>เพิ่มรูปโซน</strong></div></div>
          <div class="zoneFooter"><div class="zoneName"><b>ZONE 1 · PRIVATE</b><span>ส่วนตัว</span></div><span class="zoneUpload">อัปโหลด</span></div>
        </article>
        <article class="zoneCard" role="link" tabindex="0" data-zone="office" data-href="/zone/office" aria-label="ZONE 2 OFFICE ออฟฟิศ — แตะเพื่อเข้า กดค้างเพื่ออัปโหลดรูป">
          <div class="zoneMedia" id="zoneMediaOffice"><div class="zonePlaceholder"><span class="zonePlus">＋</span><strong>เพิ่มรูปโซน</strong></div></div>
          <div class="zoneFooter"><div class="zoneName"><b>ZONE 2 · OFFICE</b><span>ออฟฟิศ</span></div><span class="zoneUpload">อัปโหลด</span></div>
        </article>
        <article class="zoneCard" role="link" tabindex="0" data-zone="shop" data-href="/zone/shop" aria-label="ZONE 3 SHOP ร้านค้า — แตะเพื่อเข้า กดค้างเพื่ออัปโหลดรูป">
          <div class="zoneMedia" id="zoneMediaShop"><div class="zonePlaceholder"><span class="zonePlus">＋</span><strong>เพิ่มรูปโซน</strong></div></div>
          <div class="zoneFooter"><div class="zoneName"><b>ZONE 3 · SHOP</b><span>ร้านค้า</span></div><span class="zoneUpload">อัปโหลด</span></div>
        </article>
        <article class="zoneCard" role="link" tabindex="0" data-zone="showcase" data-href="/zone/portfolio" aria-label="ZONE 4 SHOWCASE ผลงาน — แตะเพื่อเข้า กดค้างเพื่ออัปโหลดรูป">
          <div class="zoneMedia" id="zoneMediaShowcase"><div class="zonePlaceholder"><span class="zonePlus">＋</span><strong>เพิ่มรูปโซน</strong></div></div>
          <div class="zoneFooter"><div class="zoneName"><b>ZONE 4 · SHOWCASE</b><span>ผลงาน</span></div><span class="zoneUpload">อัปโหลด</span></div>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="sectionHead"><h2>ผลงานล่าสุด</h2><label id="galleryAddLabel" style="cursor:pointer"><span>เพิ่มรูป</span><input id="galleryInput" class="hidden" type="file" accept="image/*,video/*" multiple></label></div>
      <div class="latest" id="latestGrid"></div>
    </section>
  </main>

  <nav class="bottomNav">
    <a class="navItem active" href="/id-home"><span class="nicon">⌂</span><span>หน้าหลัก</span></a>
    <a class="navItem" href="/friend-chat"><span class="nicon">◌</span><span>แชท</span></a>
    <button class="navPlus" type="button" onclick="openUpload('gallery')">＋</button>
    <a class="navItem" href="/"><span class="nicon">▣</span><span>ครีเอทีฟ</span></a>
    <a class="navItem" href="/zone-hub"><span class="nicon">◇</span><span>โซน</span></a>
  </nav>
</div>

<div class="uploadSheet" id="uploadSheet">
  <div class="sheetTop"><button class="sheetClose" type="button" onclick="closeUpload()">←</button><h2 id="uploadTitle">อัปโหลด</h2><span style="width:40px"></span></div>
  <div class="sheetBody">
    <div class="uploadPreview" id="uploadPreview" onclick="document.getElementById('sheetFile').click()"><div><div style="font-size:38px;color:var(--accent)">＋</div><b>เลือกรูปหรือวิดีโอ</b><div style="font-size:11px;margin-top:7px">แตะพื้นที่นี้เพื่อเลือกไฟล์</div></div></div>
    <input id="sheetFile" class="hidden" type="file" accept="image/*,video/*">
    <input id="directFile" class="hidden" type="file" accept="image/*,video/*">
    <div class="sheetChoices" id="sheetChoices"><button class="choice active" id="choiceGallery" type="button" onclick="setUploadTarget('gallery')">เพิ่มเข้าคลัง</button><button class="choice" id="choiceCover" type="button" onclick="setUploadTarget('cover')">ใช้เป็นภาพปก</button></div>
    <button class="sheetSubmit" id="sheetSubmit" type="button" onclick="submitSheet()" disabled>บันทึกและเผยแพร่</button>
  </div>
</div>


<div class="controlSheet" id="controlSheet" onclick="if(event.target===this)closeControlCenter()">
  <div class="controlPanel">
    <div class="controlTop"><h2>ตั้งค่า INFINI ID</h2><button class="controlClose" type="button" onclick="closeControlCenter()">✕</button></div>
    <p class="controlHint">เลือกแก้ข้อมูล หรือเข้าโหมดจัดหน้าเพื่อขยับและย่อ–ขยายของบนหน้าจอเอง ค่าที่บันทึกจะยังอยู่หลังรีเฟรช</p>
    <div class="controlGrid">
      <button class="controlAction" type="button" onclick="openProfileFromControl()"><strong>แก้ข้อมูลโปรไฟล์</strong><span>ชื่อ, USERNAME, INFINI ID, บทบาท และคำอธิบาย</span></button>
      <button class="controlAction" type="button" onclick="startLayoutEditor()"><strong>จัดหน้าเอง</strong><span>แตะชิ้นที่ต้องการ แล้วลาก ขยาย ปรับตัวหนังสือ หรือเปลี่ยนการแสดงรูป</span></button>
      <button class="controlAction wide" type="button" onclick="resetAllLayout()">คืนค่าการจัดหน้าเดิมทั้งหมด</button>
    </div>
  </div>
</div>

<div class="editSelection" id="editSelection"><div class="editResizeHandle" id="editResizeHandle" aria-label="ลากเพื่อย่อขยาย"></div></div>
<div class="layoutEditorBar" id="layoutEditorBar">
  <div class="editorSelected"><span id="editorSelectedName">แตะชิ้นที่ต้องการแก้</span><small>ลากชิ้นได้เลย</small></div>
  <div class="editorTools">
    <button class="editorBtn" type="button" onclick="nudgeSelected(-3,0)">←</button>
    <button class="editorBtn" type="button" onclick="nudgeSelected(0,-3)">↑</button>
    <button class="editorBtn" type="button" onclick="nudgeSelected(0,3)">↓</button>
    <button class="editorBtn" type="button" onclick="nudgeSelected(3,0)">→</button>
    <button class="editorBtn" type="button" onclick="changeSelectedFont(-1)">A−</button>
    <button class="editorBtn" type="button" onclick="changeSelectedFont(1)">A＋</button>
    <button class="editorBtn" type="button" onclick="changeSelectedDimension('width',-6)">W−</button>
    <button class="editorBtn" type="button" onclick="changeSelectedDimension('width',6)">W＋</button>
    <button class="editorBtn" type="button" onclick="changeSelectedDimension('height',-6)">H−</button>
    <button class="editorBtn" type="button" onclick="changeSelectedDimension('height',6)">H＋</button>
    <button class="editorBtn" type="button" onclick="changeSelectedPadding(-1)">ขอบ−</button>
    <button class="editorBtn" type="button" onclick="changeSelectedPadding(1)">ขอบ＋</button>
    <button class="editorBtn" type="button" onclick="toggleSelectedFit()">รูปเต็ม/พอดี</button>
    <button class="editorBtn" type="button" onclick="resetSelectedLayout()">คืนชิ้นนี้</button>
  </div>
  <div class="editorActions"><button class="editorCancel" type="button" onclick="cancelLayoutEditor()">ยกเลิก</button><button class="editorSave" type="button" onclick="saveLayoutEditor()">บันทึกการจัดหน้า</button></div>
</div>

<div class="toast" id="toast"></div>
<div class="web-overlay" id="webOverlay"><div class="web-top"><input id="webInput" placeholder="ค้นหาเว็บ..."><button onclick="runSearch()">ค้นหา</button><button onclick="closeSearch()">ปิด</button></div><iframe class="web-frame" id="webFrame"></iframe></div>

<script>
let STATE={};
let uploadTarget='gallery';
let selectedFile=null;
const $=id=>document.getElementById(id);

function toast(msg){const t=$('toast');t.textContent=msg;t.classList.add('show');clearTimeout(t._t);t._t=setTimeout(()=>t.classList.remove('show'),1500)}
function mediaEl(src,type){let el;if(String(type||'').startsWith('video')){el=document.createElement('video');el.controls=true;el.loop=true;el.muted=true;el.playsInline=true}else{el=document.createElement('img')}el.src=src;return el}
function uploadFile(file){const form=new FormData();form.append('file',file);return fetch('/api/id-entry/upload',{method:'POST',body:form}).then(r=>r.json())}
function saveState(){return fetch('/api/id-entry/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(STATE||{})})}
function initials(name){const s=String(name||'').trim();return s?s.slice(0,2).toUpperCase():'∞'}
function applyProfile(){const name=STATE.displayName||'INFINI MEMBER',id=STATE.infiniId||'INF-000001',level=STATE.level||'MEMBER';$('profileNameView').textContent=name;$('profileMetaView').textContent=id+' · '+level;['displayName','username','infiniId','level','bio'].forEach(k=>{if($(k))$(k).value=STATE[k]||''})}
function applyCover(){const media=$('heroMedia');media.innerHTML='';if(STATE.idCover){media.appendChild(mediaEl(STATE.idCover.src,STATE.idCover.type));$('idCoverEmpty').style.display='none'}else{$('idCoverEmpty').style.display='grid'}}
function applyCreativeCover(){const media=$('creativeMedia');if(!media)return;media.innerHTML='';const item=STATE.creativeCover;if(item&&item.src){const el=mediaEl(item.src,item.type);if(el.tagName==='VIDEO'){el.controls=false;el.autoplay=true;el.muted=true;el.loop=true;el.playsInline=true}media.appendChild(el)}}
function applyZoneCovers(){const covers=STATE.zoneCovers||{};const map={private:'zoneMediaPrivate',office:'zoneMediaOffice',shop:'zoneMediaShop',showcase:'zoneMediaShowcase'};Object.entries(map).forEach(([key,id])=>{const box=$(id);if(!box)return;box.innerHTML='';const item=covers[key];if(item&&item.src){const el=mediaEl(item.src,item.type);if(el.tagName==='VIDEO'){el.controls=false;el.autoplay=true;el.muted=true;el.loop=true;el.playsInline=true}box.appendChild(el)}else{box.innerHTML='<div class="zonePlaceholder"><span class="zonePlus">＋</span><strong>เพิ่มรูปโซน</strong></div>'}})}
function renderLatest(){const grid=$('latestGrid');grid.innerHTML='';const items=(STATE.gallery||[]).slice(-6).reverse();items.forEach((item,i)=>{const card=document.createElement('div');card.className='workCard';const m=document.createElement('div');m.className='workMedia';m.appendChild(mediaEl(item.src,item.type));const c=document.createElement('div');c.className='workCopy';c.innerHTML='<b>ผลงาน '+(items.length-i)+'</b><span>จากคลัง INFINI ID</span>';card.append(m,c);grid.appendChild(card)});const add=document.createElement('button');add.type='button';add.className='workCard addWork';add.innerHTML='<div><strong>＋</strong><span>เพิ่มผลงานใหม่</span></div>';add.onclick=()=>openUpload('gallery');grid.appendChild(add)}
function applyState(){applyProfile();applyCover();applyCreativeCover();applyZoneCovers();renderLatest();setTimeout(()=>applyLayout(STATE.layout||{}),0)}
function loadState(){fetch('/api/id-entry/state?t='+Date.now(),{cache:'no-store'}).then(r=>r.json()).then(d=>{STATE=d||{};applyState()}).catch(()=>applyState())}
function toggleProfile(){$('profilePanel').classList.toggle('show');if($('profilePanel').classList.contains('show'))$('profilePanel').scrollIntoView({behavior:'smooth',block:'center'})}
async function saveProfile(){['displayName','username','infiniId','level','bio'].forEach(k=>STATE[k]=$(k).value);await saveState();applyProfile();$('profilePanel').classList.remove('show');toast('บันทึกโปรไฟล์แล้ว')}
function openUpload(target='gallery'){uploadTarget=target;selectedFile=null;$('sheetFile').value='';$('uploadPreview').innerHTML='<div><div style="font-size:38px;color:var(--accent)">＋</div><b>เลือกรูปหรือวิดีโอ</b><div style="font-size:11px;margin-top:7px">แตะพื้นที่นี้เพื่อเลือกไฟล์</div></div>';$('sheetSubmit').disabled=true;setUploadTarget(target);$('uploadTitle').textContent=target.startsWith('zone-')?'อัปโหลดรูปโซน':'อัปโหลด';$('uploadSheet').classList.add('show')}
function closeUpload(){$('uploadSheet').classList.remove('show');selectedFile=null}
function setUploadTarget(target){uploadTarget=target;const zoneMode=target.startsWith('zone-');$('sheetChoices').style.display=zoneMode?'none':'grid';$('choiceGallery').classList.toggle('active',target==='gallery');$('choiceCover').classList.toggle('active',target==='cover')}
let directUploadTarget='';
function openDirectUpload(target){directUploadTarget=target;const input=$('directFile');input.value='';input.click()}
function bindPressTarget(el,target,href=''){
  let timer=null,longReady=false,moved=false,startX=0,startY=0;
  const clear=()=>{if(timer){clearTimeout(timer);timer=null}el.classList.remove('pressing')};
  el.addEventListener('contextmenu',e=>e.preventDefault());
  el.addEventListener('pointerdown',e=>{
    if(e.pointerType==='mouse'&&e.button!==0)return;
    longReady=false;moved=false;startX=e.clientX;startY=e.clientY;
    el.classList.add('pressing');
    timer=setTimeout(()=>{longReady=true;el.classList.remove('pressing');if(navigator.vibrate)navigator.vibrate(35)},280);
  });
  el.addEventListener('pointermove',e=>{
    if(Math.abs(e.clientX-startX)>28||Math.abs(e.clientY-startY)>28){moved=true;clear()}
  });
  el.addEventListener('pointerup',e=>{
    const upload=longReady&&!moved;
    const go=!longReady&&!moved&&href;
    clear();
    if(upload){e.preventDefault();openDirectUpload(target);return}
    if(go){e.preventDefault();location.href=href}
  });
  el.addEventListener('pointercancel',clear);
  el.addEventListener('pointerleave',e=>{if(e.pointerType==='mouse')clear()});
  el.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&href){e.preventDefault();location.href=href}});
}
function bindLongPressUploads(){
  bindPressTarget($('idCoverBox'),'cover','');
  bindPressTarget($('creativeCard'),'creative',$('creativeCard').dataset.href);
  document.querySelectorAll('.zoneCard[data-zone]').forEach(card=>bindPressTarget(card,'zone-'+card.dataset.zone,card.dataset.href));

  // Reliable fallback: a normal, always-visible, single-tap button for
  // uploading the ID cover photo. The long-press gesture above still
  // works too (kept for people who like it / for the small camera-icon
  // buttons elsewhere), but requiring a 280ms hold with under 16px of
  // finger movement as the ONLY way to upload was too easy to miss or
  // mis-trigger on a real touchscreen — this button always just works.
  const coverBtn = $('idCoverUploadBtn');
  if (coverBtn) {
    coverBtn.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      openDirectUpload('cover');
    });
  }

  // Same fix for each zone card: the "อัปโหลด" text in the footer used
  // to be purely decorative (just a visual hint for the long-press
  // gesture on the whole card). Make it a real, independently-tappable
  // upload shortcut too, without affecting the card's normal tap-to-open
  // navigation for the rest of the card.
  document.querySelectorAll('.zoneCard[data-zone] .zoneUpload').forEach(el => {
    const card = el.closest('.zoneCard[data-zone]');
    if (!card) return;
    el.style.pointerEvents = 'auto';
    el.style.cursor = 'pointer';
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.addEventListener('pointerdown', e => { e.stopPropagation(); });
    el.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      openDirectUpload('zone-' + card.dataset.zone);
    });
  });
}

$('directFile').addEventListener('change',async e=>{
  const file=e.target.files&&e.target.files[0];if(!file)return;
  toast('กำลังอัปโหลด...');
  try{
    const res=await uploadFile(file);if(!res.ok)throw new Error(res.error||'upload failed');
    const item={src:res.url+'?t='+Date.now(),type:res.type};
    if(directUploadTarget==='cover')STATE.idCover=item;
    else if(directUploadTarget==='creative')STATE.creativeCover=item;
    else if(directUploadTarget.startsWith('zone-')){const key=directUploadTarget.slice(5);STATE.zoneCovers=STATE.zoneCovers||{};STATE.zoneCovers[key]=item}
    await saveState();applyState();toast('อัปโหลดแล้ว');
  }catch(err){console.error(err);toast('อัปโหลดไม่สำเร็จ')}
  finally{e.target.value=''}
});
$('sheetFile').addEventListener('change',e=>{const f=e.target.files&&e.target.files[0];if(!f)return;selectedFile=f;const url=URL.createObjectURL(f);const preview=$('uploadPreview');preview.innerHTML='';preview.appendChild(mediaEl(url,f.type));$('sheetSubmit').disabled=false});
async function submitSheet(){if(!selectedFile)return;const btn=$('sheetSubmit');btn.disabled=true;btn.textContent='กำลังอัปโหลด...';try{const res=await uploadFile(selectedFile);if(!res.ok)throw new Error(res.error||'upload failed');const item={src:res.url+'?t='+Date.now(),type:res.type};if(uploadTarget==='cover')STATE.idCover=item;else if(uploadTarget==='creative')STATE.creativeCover=item;else if(uploadTarget.startsWith('zone-')){const key=uploadTarget.slice(5);STATE.zoneCovers=STATE.zoneCovers||{};STATE.zoneCovers[key]=item}else{STATE.gallery=STATE.gallery||[];STATE.gallery.push(item)}await saveState();applyState();closeUpload();toast('อัปโหลดแล้ว')}catch(e){console.error(e);toast('อัปโหลดไม่สำเร็จ')}finally{btn.textContent='บันทึกและเผยแพร่';btn.disabled=false}}
$('galleryInput').addEventListener('change',async e=>{const files=[...e.target.files];if(!files.length)return;STATE.gallery=STATE.gallery||[];toast('กำลังอัปโหลด...');for(const file of files){const res=await uploadFile(file);if(res.ok)STATE.gallery.push({src:res.url+'?t='+Date.now(),type:res.type})}await saveState();renderLatest();toast('เพิ่มเข้าคลังแล้ว');e.target.value=''})
function openSearch(){$('webOverlay').style.display='flex'}function closeSearch(){$('webOverlay').style.display='none'}function runSearch(){const q=$('webInput').value.trim();if(q)$('webFrame').src='https://www.google.com/search?igu=1&q='+encodeURIComponent(q)}
(function(){const a=$('pointTowerLink');if(a){a.href='/8046/tower'}})();
(function(){const a=$('commerceSuiteLink');if(a){a.href='/8032/commerce'}})();

/* === INFINI ID MINI EDITOR V1 === */
let EDIT_MODE=false,EDIT_SELECTED=null,EDIT_LAYOUT={},EDIT_SNAPSHOT={};
let EDIT_DRAG=null,EDIT_RESIZE=null;

function openControlCenter(){
  $('controlSheet').classList.add('show');
}
function closeControlCenter(){
  $('controlSheet').classList.remove('show');
}
function openProfileFromControl(){
  closeControlCenter();
  if(!$('profilePanel').classList.contains('show'))toggleProfile();
}
function cloneData(value){return JSON.parse(JSON.stringify(value||{}))}
function markEditTarget(el,id,label,kind='box'){
  if(!el)return;
  el.dataset.editId=id;el.dataset.editLabel=label;el.dataset.editKind=kind;
}
function setupEditorTargets(){
  markEditTarget($('idCoverBox'),'id-cover','การ์ด INFINI ID','box');
  markEditTarget($('profileNameView'),'profile-name','ชื่อบนการ์ด','text');
  markEditTarget($('profileMetaView'),'profile-meta','รหัสและสถานะ','text');
  markEditTarget(document.querySelector('.uploadWord'),'cover-upload-word','คำว่าอัปโหลด','text');
  document.querySelectorAll('.sectionHead h2').forEach((el,i)=>markEditTarget(el,'section-title-'+i,'หัวข้อส่วน '+(i+1),'text'));
  document.querySelectorAll('.tool').forEach((el,i)=>markEditTarget(el,'shortcut-'+i,'ทางลัด '+(i+1),'box'));
  document.querySelectorAll('.toolIcon').forEach((el,i)=>markEditTarget(el,'shortcut-icon-'+i,'ไอคอนทางลัด '+(i+1),'text'));
  markEditTarget($('creativeCard'),'creative-card','การ์ด CREATIVE ROOM','box');
  markEditTarget(document.querySelector('#creativeCard h2'),'creative-title','ชื่อ CREATIVE ROOM','text');
  document.querySelectorAll('.zoneCard').forEach((el,i)=>markEditTarget(el,'zone-card-'+i,'การ์ดโซน '+(i+1),'box'));
  document.querySelectorAll('.zoneName b').forEach((el,i)=>markEditTarget(el,'zone-title-'+i,'ชื่อโซน '+(i+1),'text'));
  document.querySelectorAll('.zoneName span').forEach((el,i)=>markEditTarget(el,'zone-subtitle-'+i,'คำใต้ชื่อโซน '+(i+1),'text'));
  document.querySelectorAll('.workCard').forEach((el,i)=>markEditTarget(el,'work-card-'+i,'ผลงาน '+(i+1),'box'));
}
function clearEditorInline(el){
  if(!el)return;
  ['transform','width','height','fontSize','lineHeight','padding','zIndex'].forEach(k=>el.style[k]='');
  el.querySelectorAll('img,video').forEach(m=>m.style.objectFit='');
}
function applyOneLayout(el,cfg){
  if(!el||!cfg)return;
  const x=Number(cfg.x||0),y=Number(cfg.y||0);
  if(x||y){el.style.transform=`translate3d(${x}px,${y}px,0)`;el.style.zIndex='8'}else{el.style.transform='';el.style.zIndex=''}
  el.style.width=cfg.width?Math.max(24,Number(cfg.width))+'px':'';
  el.style.height=cfg.height?Math.max(24,Number(cfg.height))+'px':'';
  el.style.fontSize=cfg.fontSize?Math.max(8,Number(cfg.fontSize))+'px':'';
  el.style.lineHeight=cfg.lineHeight?String(cfg.lineHeight):'';
  el.style.padding=cfg.padding!==undefined&&cfg.padding!==null?Math.max(0,Number(cfg.padding))+'px':'';
  if(cfg.fit)el.querySelectorAll('img,video').forEach(m=>m.style.objectFit=cfg.fit);
}
function applyLayout(layout){
  setupEditorTargets();
  document.querySelectorAll('[data-edit-id]').forEach(el=>{clearEditorInline(el);const cfg=(layout||{})[el.dataset.editId];if(cfg)applyOneLayout(el,cfg)});
  updateSelectionBox();
}
function currentCfg(){
  if(!EDIT_SELECTED)return null;
  const id=EDIT_SELECTED.dataset.editId;
  if(!EDIT_LAYOUT[id])EDIT_LAYOUT[id]={};
  return EDIT_LAYOUT[id];
}
function selectEditable(el){
  EDIT_SELECTED=el;
  $('editorSelectedName').textContent=el?el.dataset.editLabel:'แตะชิ้นที่ต้องการแก้';
  updateSelectionBox();
}
function updateSelectionBox(){
  const box=$('editSelection');
  if(!EDIT_MODE||!EDIT_SELECTED||!document.body.contains(EDIT_SELECTED)){box.classList.remove('show');return}
  const r=EDIT_SELECTED.getBoundingClientRect();
  if(r.width<2||r.height<2){box.classList.remove('show');return}
  box.style.left=r.left+'px';box.style.top=r.top+'px';box.style.width=r.width+'px';box.style.height=r.height+'px';box.classList.add('show');
}
function startLayoutEditor(){
  closeControlCenter();setupEditorTargets();
  EDIT_SNAPSHOT=cloneData(STATE.layout||{});EDIT_LAYOUT=cloneData(STATE.layout||{});EDIT_MODE=true;EDIT_SELECTED=null;
  document.body.classList.add('layout-editing');$('layoutEditorBar').classList.add('show');$('editorSelectedName').textContent='แตะชิ้นที่ต้องการแก้';
  applyLayout(EDIT_LAYOUT);toast('โหมดจัดหน้า: แตะแล้วลากได้เลย');
}
function finishLayoutEditor(){
  EDIT_MODE=false;EDIT_SELECTED=null;EDIT_DRAG=null;EDIT_RESIZE=null;
  document.body.classList.remove('layout-editing');$('layoutEditorBar').classList.remove('show');$('editSelection').classList.remove('show');
}
async function saveLayoutEditor(){
  STATE.layout=cloneData(EDIT_LAYOUT);await saveState();finishLayoutEditor();applyLayout(STATE.layout);toast('บันทึกการจัดหน้าแล้ว');
}
function cancelLayoutEditor(){
  EDIT_LAYOUT=cloneData(EDIT_SNAPSHOT);applyLayout(EDIT_LAYOUT);finishLayoutEditor();toast('ยกเลิกการแก้แล้ว');
}
async function resetAllLayout(){
  if(!confirm('คืนค่าขนาดและตำแหน่งทั้งหมดเป็นค่าเดิมใช่ไหม'))return;
  STATE.layout={};EDIT_LAYOUT={};await saveState();applyLayout({});closeControlCenter();toast('คืนค่าหน้าเดิมแล้ว');
}
function resetSelectedLayout(){
  if(!EDIT_SELECTED)return toast('แตะเลือกชิ้นก่อน');
  delete EDIT_LAYOUT[EDIT_SELECTED.dataset.editId];clearEditorInline(EDIT_SELECTED);updateSelectionBox();
}
function nudgeSelected(dx,dy){
  const c=currentCfg();if(!c)return toast('แตะเลือกชิ้นก่อน');c.x=Number(c.x||0)+dx;c.y=Number(c.y||0)+dy;applyOneLayout(EDIT_SELECTED,c);updateSelectionBox();
}
function changeSelectedFont(delta){
  const c=currentCfg();if(!c)return toast('แตะเลือกชิ้นก่อน');const now=parseFloat(getComputedStyle(EDIT_SELECTED).fontSize)||16;c.fontSize=Math.max(8,Math.min(80,Number(c.fontSize||now)+delta));applyOneLayout(EDIT_SELECTED,c);updateSelectionBox();
}
function changeSelectedDimension(prop,delta){
  const c=currentCfg();if(!c)return toast('แตะเลือกชิ้นก่อน');const r=EDIT_SELECTED.getBoundingClientRect();const now=prop==='width'?r.width:r.height;c[prop]=Math.max(24,Number(c[prop]||now)+delta);applyOneLayout(EDIT_SELECTED,c);updateSelectionBox();
}
function changeSelectedPadding(delta){
  const c=currentCfg();if(!c)return toast('แตะเลือกชิ้นก่อน');const now=parseFloat(getComputedStyle(EDIT_SELECTED).paddingTop)||0;c.padding=Math.max(0,Math.min(60,Number(c.padding===undefined?now:c.padding)+delta));applyOneLayout(EDIT_SELECTED,c);updateSelectionBox();
}
function toggleSelectedFit(){
  const c=currentCfg();if(!c)return toast('แตะเลือกชิ้นก่อน');if(!EDIT_SELECTED.querySelector('img,video'))return toast('ชิ้นนี้ไม่มีรูป');c.fit=c.fit==='contain'?'cover':'contain';applyOneLayout(EDIT_SELECTED,c);toast(c.fit==='contain'?'รูปพอดีกรอบ':'รูปเต็มกรอบ');
}

document.addEventListener('pointerdown',e=>{
  if(!EDIT_MODE)return;
  if(e.target.closest('#layoutEditorBar,#editSelection,#controlSheet'))return;
  const el=e.target.closest('[data-edit-id]');
  if(!el)return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();selectEditable(el);
  const c=currentCfg(),r=el.getBoundingClientRect();
  EDIT_DRAG={pointerId:e.pointerId,startX:e.clientX,startY:e.clientY,x:Number(c.x||0),y:Number(c.y||0),width:r.width,height:r.height};
  try{el.setPointerCapture(e.pointerId)}catch(_){ }
},true);
document.addEventListener('pointermove',e=>{
  if(!EDIT_MODE||!EDIT_DRAG||e.pointerId!==EDIT_DRAG.pointerId)return;
  e.preventDefault();const c=currentCfg();c.x=EDIT_DRAG.x+(e.clientX-EDIT_DRAG.startX);c.y=EDIT_DRAG.y+(e.clientY-EDIT_DRAG.startY);applyOneLayout(EDIT_SELECTED,c);updateSelectionBox();
},true);
document.addEventListener('pointerup',e=>{if(EDIT_DRAG&&e.pointerId===EDIT_DRAG.pointerId)EDIT_DRAG=null},true);
document.addEventListener('pointercancel',()=>{EDIT_DRAG=null},true);

$('editResizeHandle').addEventListener('pointerdown',e=>{
  if(!EDIT_MODE||!EDIT_SELECTED)return;e.preventDefault();e.stopPropagation();
  const c=currentCfg(),r=EDIT_SELECTED.getBoundingClientRect();EDIT_RESIZE={pointerId:e.pointerId,startX:e.clientX,startY:e.clientY,width:Number(c.width||r.width),height:Number(c.height||r.height)};
  try{e.target.setPointerCapture(e.pointerId)}catch(_){ }
});
$('editResizeHandle').addEventListener('pointermove',e=>{
  if(!EDIT_RESIZE||e.pointerId!==EDIT_RESIZE.pointerId)return;e.preventDefault();e.stopPropagation();const c=currentCfg();c.width=Math.max(24,EDIT_RESIZE.width+(e.clientX-EDIT_RESIZE.startX));c.height=Math.max(24,EDIT_RESIZE.height+(e.clientY-EDIT_RESIZE.startY));applyOneLayout(EDIT_SELECTED,c);updateSelectionBox();
});
$('editResizeHandle').addEventListener('pointerup',e=>{if(EDIT_RESIZE&&e.pointerId===EDIT_RESIZE.pointerId)EDIT_RESIZE=null});
$('editResizeHandle').addEventListener('pointercancel',()=>{EDIT_RESIZE=null});
window.addEventListener('scroll',updateSelectionBox,true);window.addEventListener('resize',updateSelectionBox);


setupEditorTargets();
bindLongPressUploads();
loadState();
</script>
</body>
</html>

'''
GATE_HTML = r'''
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>CREATIVE GATE</title>
<style>
*{box-sizing:border-box}
html,body{
  margin:0;
  width:100%;
  min-height:100%;
  background:#050100;
  color:#fff;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
body{overflow-x:hidden}
.page{
  min-height:100vh;
  background:radial-gradient(circle at top,#170800,#050100 45%,#000);
  padding-bottom:150px;
}
.topbar{
  position:sticky;
  top:0;
  z-index:30;
  height:58px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:0 14px;
  background:rgba(0,0,0,.9);
  border-bottom:1px solid rgba(255,132,0,.35);
}
.brand{
  color:#ff8a1c;
  font-weight:900;
  letter-spacing:.12em;
  font-size:14px;
}
.btn,label.btn{
  border:1px solid rgba(255,132,0,.62);
  background:rgba(0,0,0,.78);
  color:#ffc17d;
  border-radius:999px;
  padding:10px 14px;
  font-size:13px;
  font-weight:900;
  text-decoration:none;
  display:inline-flex;
  align-items:center;
  justify-content:center;
}
.btn.orange{
  background:#ff9a1f;
  color:#050505;
  border:0;
}
input[type=file]{display:none}
.gate-wrap{
  padding:14px 14px 150px;
}
.gate-card{
  height:calc(100vh - 210px);
  min-height:520px;
  border-radius:30px;
  border:1px solid rgba(255,132,0,.62);
  background:#050505;
  overflow:hidden;
  position:relative;
}
.gate-card img,.gate-card video{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;
}
.empty{
  height:100%;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  text-align:center;
  padding:24px;
  background:
    linear-gradient(to top,rgba(0,0,0,.92),rgba(0,0,0,.18)),
    radial-gradient(circle at top,#301400,#050505 70%);
}
.empty h1{
  margin:0 0 10px;
  color:#ff9a2c;
  font-size:40px;
  letter-spacing:.08em;
}
.empty p{
  margin:0;
  color:#aaa;
  font-size:14px;
}
.actions{
  position:absolute;
  left:18px;
  right:18px;
  bottom:18px;
  z-index:20;
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
}
.actions label,.actions button{
  min-height:62px;
}
</style>
</head>
<body>
<div class="page">
  <div class="topbar">
    <a class="btn" href="/id-home">← ID Home</a>
    <div class="brand">CREATIVE GATE</div>
    <button class="btn" onclick="alert('ค้นหายังอยู่หน้า ID Home')">ค้นหา</button>
  </div>

  <div class="gate-wrap">
    <div class="gate-card" id="gateCard">
      <div class="empty" id="gateEmpty">
        <h1>CREATIVE<br>GATE</h1>
        <p>อัปโหลดรูปตึก / Space Box / ประตูเข้า Creative Room</p>
      </div>

      <div class="actions">
        <label class="btn">
          อัปโหลดรูปตึก
          <input id="gateInput" type="file" accept="image/*,video/*">
        </label>
        <button class="btn orange" onclick="location.href='/'">เข้าตึก</button>
      </div>
    </div>
  </div>
</div>

<script>
let STATE={};

function mediaEl(src,type){
  let el;
  if(String(type||"").startsWith("video")){
    el=document.createElement("video");
    el.controls=true; el.loop=true; el.muted=true; el.playsInline=true;
  }else{
    el=document.createElement("img");
  }
  el.src=src;
  return el;
}

function setGate(src,type){
  const card=document.getElementById("gateCard");
  const empty=document.getElementById("gateEmpty");
  card.querySelectorAll("img,video").forEach(x=>x.remove());
  if(empty) empty.style.display="none";
  card.insertBefore(mediaEl(src,type), card.firstChild);
}

function uploadFile(file){
  const form=new FormData();
  form.append("file", file);
  return fetch("/api/id-entry/upload",{method:"POST",body:form}).then(r=>r.json());
}
function saveState(){
  return fetch("/api/id-entry/state",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(STATE||{})
  });
}
function loadState(){
  fetch("/api/id-entry/state?t="+Date.now())
    .then(r=>r.json())
    .then(d=>{
      STATE=d||{};
      if(STATE.gate) setGate(STATE.gate.src,STATE.gate.type);
    });
}

document.getElementById("gateInput").addEventListener("change", async e=>{
  const file=e.target.files[0];
  if(!file) return;

  const res=await uploadFile(file);
  if(!res.ok){
    alert("อัปโหลดไม่สำเร็จ");
    return;
  }

  STATE.gate={src:res.url+"?t="+Date.now(),type:res.type};
  await saveState();
  setGate(STATE.gate.src,STATE.gate.type);
});

loadState();
</script>
</body>
</html>
'''

def install_id_entry_7000(app: FastAPI):
    # === INFINI_PUBLIC_7000_AUTH_BRIDGE_V2_ROUTE ===
    @app.get("/auth/bridge")
    async def id_auth_bridge(token: str = "", next: str = "/id"):
        try:
            payload = _session_signer().loads(token)
        except BadSignature:
            return RedirectResponse(_public_8032_login_url(), status_code=303)

        user_id = str(payload.get("user_id") or "").strip()
        issued_at = int(payload.get("issued_at") or 0)
        if (
            not user_id
            or user_id not in _load_users()
            or not issued_at
            or abs(int(time.time()) - issued_at) > 600
        ):
            return RedirectResponse(_public_8032_login_url(), status_code=303)

        safe_next = str(next or "/id")
        if not safe_next.startswith("/") or safe_next.startswith("//"):
            safe_next = "/id"

        response = RedirectResponse(safe_next, status_code=303)
        response.set_cookie(
            "infini_session",
            _session_signer().dumps({"user_id": user_id}),
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
        )
        return response

    @app.post("/api/id-entry/upload")
    async def id_entry_upload(request: Request, file: UploadFile = File(...)):
        user_id = _require_user_id(request)
        content_type = file.content_type or "application/octet-stream"
        original_filename = file.filename or ""
        ext = Path(original_filename).suffix.lower()

        if not ext:
            if content_type.startswith("image/"):
                ext = ".jpg"
            elif content_type.startswith("video/"):
                ext = ".mp4"
            else:
                ext = ".bin"

        raw = await file.read()

        stored_bytes, stored_ext, was_optimized = raw, ext, False
        try:
            from image_optimize_7000 import is_optimizable_image, optimize_image_bytes
            if is_optimizable_image(original_filename or f"x{ext}"):
                stored_bytes, stored_ext, was_optimized = optimize_image_bytes(
                    raw, original_filename or f"x{ext}"
                )
        except Exception:
            pass  # never block an upload over the optimizer failing

        owner_dir = UPLOAD_DIR / _safe_user_id(user_id)
        owner_dir.mkdir(parents=True, exist_ok=True)
        base = uuid.uuid4().hex
        name = f"{base}{stored_ext}"
        out = owner_dir / name
        out.write_bytes(stored_bytes)

        if was_optimized:
            (owner_dir / f"{base}__original{ext}").write_bytes(raw)

        return JSONResponse({
            "ok": True,
            "url": f"/id-entry-media/{_safe_user_id(user_id)}/{name}",
            "type": content_type
        })

    @app.get("/id-entry-media/{owner}/{name}")
    async def id_entry_media_owner(owner: str, name: str):
        path = UPLOAD_DIR / _safe_user_id(owner) / Path(name).name
        if not path.exists():
            return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
        return FileResponse(path)

    @app.get("/id-entry-media/{name}")
    async def id_entry_media(name: str):
        path = UPLOAD_DIR / Path(name).name
        if not path.exists():
            return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
        return FileResponse(path)

    @app.get("/api/id-entry/state")
    async def id_entry_get_state(request: Request):
        user_id = _require_user_id(request)
        return JSONResponse(_load_user_state(user_id))

    @app.post("/api/id-entry/state")
    async def id_entry_save_state(request: Request):
        user_id = _require_user_id(request)
        try:
            data = await request.json()
            saved = _save_user_state(user_id, data if isinstance(data, dict) else {})
            return JSONResponse({"ok": True, "state": saved})
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    @app.get("/id-home", response_class=HTMLResponse)
    async def id_home(request: Request):
        if not _current_user_id(request):
            return RedirectResponse(_public_8032_login_url(), status_code=303)
        return HTMLResponse(ID_ENTRY_HTML)

    @app.get("/id", response_class=HTMLResponse)
    async def id_home_short(request: Request):
        if not _current_user_id(request):
            return RedirectResponse(_public_8032_login_url(), status_code=303)
        return HTMLResponse(ID_ENTRY_HTML)

    @app.get("/logout")
    async def infini_logout():
        # Clears the shared "infini_session" cookie (same origin as 8032 via
        # proxy.py, so this logs the user out of both 7000 and 8032 at once)
        # and sends them back to the login page for a different ID.
        response = RedirectResponse(_public_8032_login_url(), status_code=303)
        response.delete_cookie("infini_session")
        return response

    @app.get("/creative-gate", response_class=HTMLResponse)
    async def creative_gate():
        return HTMLResponse(GATE_HTML)
