#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

BASE = Path(__file__).resolve().parent
MAIN = BASE / "main.py"
SUBPAGE = BASE / "subpage_7000.py"
FRIEND = BASE / "friend_chat_entry_7000.py"
FRIEND_NEW = BASE / "friend_chat_entry_7000_v2.py"

required = [MAIN, SUBPAGE, FRIEND, FRIEND_NEW]
missing = [p.name for p in required if not p.exists()]
if missing:
    raise SystemExit("ไม่พบไฟล์: " + ", ".join(missing))

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backups = {}

def backup(path: Path):
    target = path.with_name(f"{path.name}.before_easy_upload_friend_{stamp}")
    shutil.copy2(path, target)
    backups[path] = target
    return target

def restore_all():
    for original, saved in backups.items():
        if saved.exists():
            shutil.copy2(saved, original)

try:
    backup(MAIN)
    backup(SUBPAGE)
    backup(FRIEND)

    # หน้า Creative Room หลัก: ลดกดค้างจาก 650ms เหลือ 280ms
    main_text = MAIN.read_text(encoding="utf-8")
    if "},280);" not in main_text:
        main_pattern = (
            r'(longTimer\s*=\s*setTimeout\(\(\)=>\{\s*'
            r'longPressed\s*=\s*true;\s*onLong\(\);\s*\},)'
            r'650(\);)'
        )
        main_text, main_count = re.subn(
            main_pattern,
            r'\g<1>280\2',
            main_text,
            count=1,
            flags=re.S,
        )
        if main_count != 1:
            raise RuntimeError("ไม่พบจุดกดค้าง 650ms ใน main.py")
        MAIN.write_text(main_text, encoding="utf-8")

    # หน้า Subpage: ลดกดค้างจาก 600ms เหลือ 280ms
    sub_text = SUBPAGE.read_text(encoding="utf-8")
    sub_pattern = (
        r'(longPressed\s*=\s*true;\s*uploadItem\(item\);\s*\},)'
        r'(?:600|650)(\);)'
    )
    if not re.search(
        r'longPressed\s*=\s*true;\s*uploadItem\(item\);\s*\},280\);',
        sub_text,
        flags=re.S,
    ):
        sub_text, sub_count = re.subn(
            sub_pattern,
            r'\g<1>280\2',
            sub_text,
            count=1,
            flags=re.S,
        )
        if sub_count != 1:
            raise RuntimeError("ไม่พบจุดกดค้างใน subpage_7000.py")
        SUBPAGE.write_text(sub_text, encoding="utf-8")

    # เปลี่ยนเฉพาะโมดูล FRIEND / CHAT
    shutil.copy2(FRIEND_NEW, FRIEND)

    # ตรวจ syntax ก่อนจบ
    for path in [MAIN, SUBPAGE, FRIEND]:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

except Exception as exc:
    restore_all()
    raise SystemExit(f"ติดตั้งไม่สำเร็จ จึงกู้ไฟล์เดิมแล้ว: {exc}")

print("ติดตั้งสำเร็จ")
print("- กดค้างอัปโหลดเร็วขึ้น: 280 มิลลิวินาที")
print("- เพิ่มปุ่ม ขอเป็นเพื่อน / เปิดคำขอ / รับเป็นเพื่อน")
print("- ไม่แตะรูป ข้อมูล Point Tower หรือระบบ Thumbnail")
print("เปิด FRIEND / CHAT: http://127.0.0.1:7000/friend-chat")
