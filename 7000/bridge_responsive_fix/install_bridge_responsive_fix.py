from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

TAG_8032 = "INFINI_PUBLIC_8032_TO_7000_BRIDGE_V2"
TAG_7000 = "INFINI_PUBLIC_7000_AUTH_BRIDGE_V2"
TAG_DETAIL = "INFINI_DETAIL_RESPONSIVE_MENU_FIX_V2"
TAG_SUBPAGE = "INFINI_SUBPAGE_RESPONSIVE_MENU_FIX_V2"


def fail(message: str) -> None:
    print(f"❌ {message}")
    raise SystemExit(1)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"อ่านไฟล์ไม่ได้: {path} ({exc})")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    pos = text.find(anchor)
    if pos < 0:
        fail(f"หาโครงสำหรับ {label} ไม่พบ")
    pos += len(anchor)
    return text[:pos] + addition + text[pos:]


def patch_8032(path: Path) -> None:
    text = read_text(path)
    if TAG_8032 in text:
        print("ℹ️  8032 เชื่อมลิงก์อยู่แล้ว")
        return

    if "import time\n" not in text:
        text = text.replace("import shutil\n", "import shutil\nimport time\n", 1)
    if "from urllib.parse import quote, urlsplit, urlunsplit\n" not in text:
        marker = "from typing import Any\n"
        if marker not in text:
            fail("หา import ของ 8032 ไม่พบ")
        text = text.replace(
            marker,
            marker + "from urllib.parse import quote, urlsplit, urlunsplit\n",
            1,
        )

    anchor = 'INFINI_7000_ID_URL = os.getenv("INFINI_7000_ID_URL", "http://127.0.0.1:7000/id")\n'
    block = f'''\n# === {TAG_8032} ===\nPUBLIC_LINKS_FILE = DATA_DIR / "public_links.json"\n\ndef _read_public_links() -> dict:\n    try:\n        data = json.loads(PUBLIC_LINKS_FILE.read_text(encoding="utf-8"))\n        return data if isinstance(data, dict) else {{}}\n    except Exception:\n        return {{}}\n\ndef _clean_public_base(value: str, fallback: str) -> str:\n    raw = str(value or "").strip() or fallback\n    try:\n        parts = urlsplit(raw)\n        if parts.scheme in ("http", "https") and parts.netloc:\n            return urlunsplit((parts.scheme, parts.netloc, "", "", "")).rstrip("/")\n    except Exception:\n        pass\n    return fallback.rstrip("/")\n\ndef _public_7000_base() -> str:\n    configured = (\n        os.getenv("INFINI_7000_PUBLIC_URL")\n        or _read_public_links().get("public_7000_url")\n        or INFINI_7000_ID_URL\n    )\n    return _clean_public_base(configured, "http://127.0.0.1:7000")\n\ndef _bridge_url_for(user_id: str) -> str:\n    token = session_signer.dumps({{\n        "user_id": str(user_id),\n        "issued_at": int(time.time()),\n    }})\n    return (\n        _public_7000_base()\n        + "/auth/bridge?token="\n        + quote(token, safe="")\n        + "&next=%2Fid"\n    )\n# === END {TAG_8032} ===\n'''
    text = insert_after(text, anchor, block, "ตัวเชื่อม 8032 → 7000")

    old_register = 'response = RedirectResponse(INFINI_7000_ID_URL, status_code=303)\n    response.set_cookie(\n        "infini_session",\n        session_signer.dumps({"user_id": user_id}),'
    new_register = 'response = RedirectResponse(_bridge_url_for(user_id), status_code=303)\n    response.set_cookie(\n        "infini_session",\n        session_signer.dumps({"user_id": user_id}),'
    if old_register not in text:
        fail("หา redirect หลังสมัครของ 8032 ไม่พบ")
    text = text.replace(old_register, new_register, 1)

    old_login = 'response = RedirectResponse(INFINI_7000_ID_URL, status_code=303)\n    response.set_cookie(\n        "infini_session",\n        session_signer.dumps({"user_id": matched["id"]}),' 
    new_login = 'response = RedirectResponse(_bridge_url_for(matched["id"]), status_code=303)\n    response.set_cookie(\n        "infini_session",\n        session_signer.dumps({"user_id": matched["id"]}),' 
    if old_login not in text:
        fail("หา redirect หลังล็อกอินของ 8032 ไม่พบ")
    text = text.replace(old_login, new_login, 1)

    write_text(path, text)
    print("✅ เชื่อม 8032 → 7000 แบบข้ามโดเมนแล้ว")


def patch_id_entry(path: Path) -> None:
    text = read_text(path)
    if TAG_7000 in text:
        print("ℹ️  7000 มี Auth Bridge อยู่แล้ว")
        return

    if "import time\n" not in text:
        text = text.replace("import os\n", "import os\nimport time\n", 1)

    anchor = 'SESSION_SECRET_FILE = SHARED_DATA_DIR / "infini_session_secret.txt"\n'
    addition = 'PUBLIC_LINKS_FILE = SHARED_DATA_DIR / "public_links.json"\n'
    text = insert_after(text, anchor, addition, "ไฟล์ลิงก์สาธารณะ 7000")

    signer_anchor = '    return URLSafeSerializer(secret, salt="infini-session")\n'
    helper_block = f'''\n\n# === {TAG_7000} ===\ndef _read_public_links() -> dict:\n    try:\n        data = json.loads(PUBLIC_LINKS_FILE.read_text(encoding="utf-8"))\n        return data if isinstance(data, dict) else {{}}\n    except Exception:\n        return {{}}\n\ndef _public_8032_login_url() -> str:\n    base = str(\n        os.getenv("INFINI_8032_PUBLIC_URL")\n        or _read_public_links().get("public_8032_url")\n        or "http://127.0.0.1:8032"\n    ).strip().rstrip("/")\n    if not base.startswith(("http://", "https://")):\n        base = "http://127.0.0.1:8032"\n    return base + "/login"\n# === END {TAG_7000} ===\n'''
    text = insert_after(text, signer_anchor, helper_block, "ตัวรับ Auth Bridge ของ 7000")

    install_anchor = 'def install_id_entry_7000(app: FastAPI):\n'
    route_block = f'''    # === {TAG_7000}_ROUTE ===\n    @app.get("/auth/bridge")\n    async def id_auth_bridge(token: str = "", next: str = "/id"):\n        try:\n            payload = _session_signer().loads(token)\n        except BadSignature:\n            return RedirectResponse(_public_8032_login_url(), status_code=303)\n\n        user_id = str(payload.get("user_id") or "").strip()\n        issued_at = int(payload.get("issued_at") or 0)\n        if (\n            not user_id\n            or user_id not in _load_users()\n            or not issued_at\n            or abs(int(time.time()) - issued_at) > 600\n        ):\n            return RedirectResponse(_public_8032_login_url(), status_code=303)\n\n        safe_next = str(next or "/id")\n        if not safe_next.startswith("/") or safe_next.startswith("//"):\n            safe_next = "/id"\n\n        response = RedirectResponse(safe_next, status_code=303)\n        response.set_cookie(\n            "infini_session",\n            _session_signer().dumps({{"user_id": user_id}}),\n            httponly=True,\n            samesite="lax",\n            max_age=60 * 60 * 24 * 30,\n            path="/",\n        )\n        return response\n\n'''
    if install_anchor not in text:
        fail("หา install_id_entry_7000 ไม่พบ")
    text = text.replace(install_anchor, install_anchor + route_block, 1)

    text = text.replace(
        'return RedirectResponse("http://127.0.0.1:8032/login", status_code=303)',
        'return RedirectResponse(_public_8032_login_url(), status_code=303)',
    )

    write_text(path, text)
    print("✅ เพิ่มจุดรับล็อกอินจาก 8032 ใน 7000 แล้ว")


def patch_detail(path: Path) -> None:
    text = read_text(path)
    if TAG_DETAIL in text:
        print("ℹ️  กรอบสามจุดหน้ารายละเอียด Responsive อยู่แล้ว")
        return

    css = f'''\n/* === {TAG_DETAIL} === */\nhtml,body{{max-width:100%;overflow-x:hidden}}\n.page,.hero,.edPanel,.edGrid,.edField{{min-width:0;max-width:100%}}\n.edPanel{{width:100%;box-sizing:border-box;overflow:hidden}}\n.edGrid{{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}\n.edField select,.edField input{{min-width:0;max-width:100%;box-sizing:border-box}}\n.edField span,.edBtn{{overflow-wrap:anywhere;word-break:break-word}}\n@media(max-width:520px){{\n  .edPanel{{margin:10px 0;padding:10px;border-radius:16px}}\n  .edGrid{{grid-template-columns:minmax(0,1fr)}}\n  .edField.full{{grid-column:auto}}\n  .edActions{{grid-template-columns:minmax(0,1fr)}}\n  .edBtn.upload{{grid-column:auto}}\n  .edHead b{{font-size:17px}}\n}}\n/* === END {TAG_DETAIL} === */\n'''
    anchor = '@media(min-width:800px){.hero{min-height:520px}.emptyHero{min-height:520px}}\n'
    text = insert_after(text, anchor, css, "Responsive เมนูสามจุดหน้ารายละเอียด")
    write_text(path, text)
    print("✅ ปรับกรอบสามจุดหน้ารายละเอียดไม่ให้ล้นจอแล้ว")


def patch_subpage(path: Path) -> None:
    text = read_text(path)
    if TAG_SUBPAGE in text:
        print("ℹ️  กล่องจัดการการ์ดย่อย Responsive อยู่แล้ว")
        return

    css = f'''\n/* === {TAG_SUBPAGE} === */\nhtml,body{{max-width:100%;overflow-x:hidden}}\n.actionSheet{{\n  padding:max(10px,env(safe-area-inset-top)) max(10px,env(safe-area-inset-right))\n          max(10px,env(safe-area-inset-bottom)) max(10px,env(safe-area-inset-left));\n  overflow-y:auto;overflow-x:hidden;\n}}\n.actionBox{{\n  width:min(560px,calc(100vw - 20px));\n  max-width:calc(100vw - 20px);min-width:0;\n  margin:0 auto;box-sizing:border-box;overflow:hidden;\n}}\n.actionTitle,.actionBtn{{overflow-wrap:anywhere;word-break:break-word;white-space:normal}}\n@media(max-width:420px){{\n  .actionBox{{width:100%;max-width:100%;padding:10px;border-radius:18px}}\n  .actionBtn{{min-height:52px;margin:5px 0;font-size:16px;border-radius:15px}}\n  .actionTitle{{font-size:17px}}\n}}\n/* === END {TAG_SUBPAGE} === */\n'''
    anchor = '.actionBtn.delete{border-color:#b7463c;background:#2b0805;color:#ffb7ae}\n'
    text = insert_after(text, anchor, css, "Responsive กล่องจัดการการ์ดย่อย")
    write_text(path, text)
    print("✅ ปรับกล่องการ์ดย่อยไม่ให้หลุดกรอบทุกขนาดจอแล้ว")


def write_helper_scripts(root_8032: Path, root_7000: Path) -> None:
    setter = root_8032 / "set_infini_public_links.py"
    setter.write_text(
        '''from __future__ import annotations\n\nimport argparse\nimport json\nfrom pathlib import Path\nfrom urllib.parse import urlsplit, urlunsplit\n\nBASE = Path(__file__).resolve().parent\nPATH = BASE / "data" / "public_links.json"\n\ndef clean(value: str) -> str:\n    parts = urlsplit(value.strip())\n    if parts.scheme not in ("http", "https") or not parts.netloc:\n        raise ValueError("ลิงก์ต้องเริ่มด้วย http:// หรือ https://")\n    return urlunsplit((parts.scheme, parts.netloc, "", "", "")).rstrip("/")\n\ndef load() -> dict:\n    try:\n        data = json.loads(PATH.read_text(encoding="utf-8"))\n        return data if isinstance(data, dict) else {}\n    except Exception:\n        return {}\n\nparser = argparse.ArgumentParser()\nparser.add_argument("--7000", dest="url7000")\nparser.add_argument("--8032", dest="url8032")\nparser.add_argument("--show", action="store_true")\nargs = parser.parse_args()\n\ndata = load()\nif args.url7000:\n    data["public_7000_url"] = clean(args.url7000)\nif args.url8032:\n    data["public_8032_url"] = clean(args.url8032)\nPATH.parent.mkdir(parents=True, exist_ok=True)\nPATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n\nprint("✅ บันทึกลิงก์สาธารณะแล้ว")\nprint("7000:", data.get("public_7000_url", "ยังไม่ได้ตั้ง"))\nprint("8032:", data.get("public_8032_url", "ยังไม่ได้ตั้ง"))\n''',
        encoding="utf-8",
    )

    share7000 = root_7000 / "share_7000_and_link_8032.sh"
    share7000.write_text(
        '''#!/data/data/com.termux/files/usr/bin/bash\nset -u\nROOT7000="$(cd "$(dirname "$0")" && pwd)"\nROOT8032="$(dirname "$ROOT7000")"\nLOG="${TMPDIR:-$HOME}/infini_cf_7000_$$.log"\nrm -f "$LOG"\n\necho "กำลังสร้างลิงก์แชร์ 7000..."\ncloudflared tunnel --protocol http2 --url http://127.0.0.1:7000 2>&1 | tee "$LOG" &\nCFPID=$!\n\nURL=""\nfor _ in $(seq 1 60); do\n  URL=$(grep -Eo 'https://[-a-z0-9]+\\.trycloudflare\\.com' "$LOG" | tail -n 1 || true)\n  [ -n "$URL" ] && break\n  kill -0 "$CFPID" 2>/dev/null || break\n  sleep 1\ndone\n\nif [ -z "$URL" ]; then\n  echo "❌ ยังสร้างลิงก์ 7000 ไม่สำเร็จ"\n  kill "$CFPID" 2>/dev/null || true\n  exit 1\nfi\n\npython "$ROOT8032/set_infini_public_links.py" --7000 "$URL"\necho "✅ ลิงก์แชร์ 7000: $URL"\necho "เปิดหน้านี้ค้างไว้"\nwait "$CFPID"\n''',
        encoding="utf-8",
    )
    share7000.chmod(0o755)

    share8032 = root_8032 / "share_8032_and_link_7000.sh"
    share8032.write_text(
        '''#!/data/data/com.termux/files/usr/bin/bash\nset -u\nROOT8032="$(cd "$(dirname "$0")" && pwd)"\nLOG="${TMPDIR:-$HOME}/infini_cf_8032_$$.log"\nrm -f "$LOG"\n\necho "กำลังสร้างลิงก์แชร์ 8032..."\ncloudflared tunnel --protocol http2 --url http://127.0.0.1:8032 2>&1 | tee "$LOG" &\nCFPID=$!\n\nURL=""\nfor _ in $(seq 1 60); do\n  URL=$(grep -Eo 'https://[-a-z0-9]+\\.trycloudflare\\.com' "$LOG" | tail -n 1 || true)\n  [ -n "$URL" ] && break\n  kill -0 "$CFPID" 2>/dev/null || break\n  sleep 1\ndone\n\nif [ -z "$URL" ]; then\n  echo "❌ ยังสร้างลิงก์ 8032 ไม่สำเร็จ"\n  kill "$CFPID" 2>/dev/null || true\n  exit 1\nfi\n\npython "$ROOT8032/set_infini_public_links.py" --8032 "$URL"\necho "✅ ลิงก์สำหรับส่งให้คนอื่น: $URL"\necho "เปิดหน้านี้ค้างไว้"\nwait "$CFPID"\n''',
        encoding="utf-8",
    )
    share8032.chmod(0o755)
    print("✅ เพิ่มคำสั่งแชร์ที่บันทึกลิงก์ให้อัตโนมัติแล้ว")


def main() -> None:
    root_7000 = Path.cwd().resolve()
    if not (root_7000 / "id_entry_7000.py").exists():
        fail("ให้รันตัวติดตั้งจากโฟลเดอร์ infini_remote_pro_v1")

    root_8032 = root_7000.parent
    main_8032 = root_8032 / "main.py"
    if not main_8032.exists():
        fail(f"ไม่พบ main.py ของ 8032 ที่ {main_8032}")

    targets = [
        main_8032,
        root_7000 / "id_entry_7000.py",
        root_7000 / "detail_swipe_7000.py",
        root_7000 / "subpage_7000.py",
    ]
    for target in targets:
        if not target.exists():
            fail(f"ไม่พบไฟล์ {target}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root_7000 / f"backup_before_bridge_responsive_{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(main_8032, backup / "8032_main.py")
    for target in targets[1:]:
        shutil.copy2(target, backup / target.name)

    patch_8032(main_8032)
    patch_id_entry(root_7000 / "id_entry_7000.py")
    patch_detail(root_7000 / "detail_swipe_7000.py")
    patch_subpage(root_7000 / "subpage_7000.py")
    write_helper_scripts(root_8032, root_7000)

    print("")
    print("✅ ติดตั้งครบ 2 เรื่องแล้ว")
    print("  1) 8032 ล็อกอินแล้วส่งเข้า 7000 ข้ามลิงก์ Cloudflare ได้")
    print("  2) เมนูสามจุด/กรอบการ์ดย่อยไม่ล้นจอเครื่องอื่น")
    print(f"📦 สำรองเดิมไว้ที่: {backup}")


if __name__ == "__main__":
    main()
