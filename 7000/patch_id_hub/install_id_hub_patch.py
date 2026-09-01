from __future__ import annotations

from pathlib import Path
from datetime import datetime
import py_compile
import re
import shutil
import sys

ROOT = Path.cwd().resolve()
PATCH_DIR = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
ID_ENTRY = ROOT / "id_entry_7000.py"
MODULE = ROOT / "id_hub_7000.py"
USER_SCOPE = ROOT / "user_scope_7000.py"


def fail(message: str) -> None:
    print(f"❌ {message}")
    raise SystemExit(1)


if not MAIN.exists() or not ID_ENTRY.exists():
    fail("กรุณารันคำสั่งนี้จากโฟลเดอร์ infini_remote_pro_v1")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = ROOT / f"backup_before_id_hub_{stamp}"
backup.mkdir(parents=True, exist_ok=True)
for path in (MAIN, ID_ENTRY, MODULE, USER_SCOPE):
    if path.exists():
        shutil.copy2(path, backup / path.name)

# Install the new module.
shutil.copy2(PATCH_DIR / "id_hub_7000.py", MODULE)

# The source archive showed user_scope_7000.py missing from the direct 7000 copy.
# Restore it only when it is actually absent; never overwrite a working current file.
if not USER_SCOPE.exists():
    fallback = PATCH_DIR / "user_scope_7000.py"
    if not fallback.exists():
        fail("ไม่พบ user_scope_7000.py สำหรับกู้คืน")
    shutil.copy2(fallback, USER_SCOPE)
    print("✅ กู้คืน user_scope_7000.py ที่หายไป")

main_text = MAIN.read_text(encoding="utf-8")
if "install_id_hub_7000(app)" not in main_text:
    marker = "from id_entry_7000 import install_id_entry_7000\ninstall_id_entry_7000(app)\n"
    if marker not in main_text:
        fail("หาจุดเชื่อม id_entry_7000 ใน main.py ไม่พบ")
    addition = marker + "\nfrom id_hub_7000 import install_id_hub_7000\ninstall_id_hub_7000(app)\n"
    main_text = main_text.replace(marker, addition, 1)
    MAIN.write_text(main_text, encoding="utf-8")
    print("✅ เชื่อมหน้า รวมไอดี เข้ากับ main.py")
else:
    print("ℹ️ main.py มีระบบรวมไอดีอยู่แล้ว")

entry_text = ID_ENTRY.read_text(encoding="utf-8")
if 'id="idHubLink"' not in entry_text:
    lines = entry_text.splitlines(keepends=True)
    inserted = False
    for index, line in enumerate(lines):
        if 'id="pointTowerLink"' in line and 'class="tool"' in line:
            indent = re.match(r"\s*", line).group(0)
            card = (
                f'{indent}<a class="tool" id="idHubLink" href="/id-hub">'
                '<span class="toolIcon">∞</span><b>รวมไอดี</b>'
                '<small>สมาชิกทั้งหมด</small></a>\n'
            )
            lines.insert(index + 1, card)
            inserted = True
            break
    if not inserted:
        fail("หาช่อง Point ใน id_entry_7000.py ไม่พบ")
    ID_ENTRY.write_text("".join(lines), encoding="utf-8")
    print("✅ เพิ่มช่อง รวมไอดี ข้าง Point")
else:
    print("ℹ️ ช่องรวมไอดีมีอยู่แล้ว")

for path in (MAIN, ID_ENTRY, MODULE, USER_SCOPE):
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        fail(f"ตรวจโค้ดไม่ผ่าน: {path.name}: {exc}")

print("✅ ติดตั้งระบบรวมไอดีสำเร็จ")
print(f"📦 สำรองไฟล์เดิมไว้ที่: {backup}")
print("📍 หน้าใหม่: /id-hub")
print("📍 สมาชิกใหม่จาก 8032 จะต่อท้ายอัตโนมัติ")
