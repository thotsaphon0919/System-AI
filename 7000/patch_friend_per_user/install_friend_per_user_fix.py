from pathlib import Path
from datetime import datetime
import json
import py_compile
import shutil

ROOT = Path.cwd().resolve()
PATCH = Path(__file__).resolve().parent
TARGET = ROOT / "friend_chat_entry_7000.py"
ALT = ROOT / "friend_chat_entry_7000_v2.py"
MAIN = ROOT / "main.py"
DATA = ROOT / "data" / "friend_chat_entry" / "friend_requests.json"

if not MAIN.exists() or not TARGET.exists():
    raise SystemExit("❌ กรุณารันจากโฟลเดอร์ infini_remote_pro_v1")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = ROOT / f"backup_before_friend_per_user_{stamp}"
backup.mkdir(parents=True, exist_ok=True)
for path in (TARGET, ALT, DATA):
    if path.exists():
        dest = backup / path.name
        shutil.copy2(path, dest)

# Reset only the old V2 global request format. New V3 account-pair data is preserved.
if DATA.exists():
    try:
        raw = json.loads(DATA.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    rows = raw.get("requests") if isinstance(raw, dict) and isinstance(raw.get("requests"), list) else []
    legacy = any(not isinstance(r, dict) or not r.get("from_user_id") or not r.get("to_user_id") for r in rows)
    if legacy:
        DATA.write_text(json.dumps({"version": 3, "requests": []}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("✅ แยกรายชื่อเพื่อนใหม่ และเก็บข้อมูลรวมเดิมไว้ในโฟลเดอร์สำรอง")

shutil.copy2(PATCH / "friend_chat_entry_7000.py", TARGET)
if ALT.exists():
    shutil.copy2(PATCH / "friend_chat_entry_7000.py", ALT)

py_compile.compile(str(TARGET), doraise=True)
py_compile.compile(str(MAIN), doraise=True)
print("✅ แก้ระบบเพื่อนแยกตาม INFINI ID แล้ว")
print("✅ สมาชิกใหม่จะไม่ติดเพื่อนของ Simonlaeng")
print("✅ กดชื่อเพื่อนแล้วเข้า Public ID ได้")
print("✅ ปุ่มสีส้มกลับเป็น 'ขอเป็นเพื่อน' เสมอ")
print(f"📦 สำรองของเดิมไว้ที่: {backup}")
