from __future__ import annotations

from pathlib import Path
import json
import shutil
import sys

from user_scope_7000 import save_registry, user_space_dir

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"


def load_users() -> tuple[Path | None, dict]:
    candidates = [
        BASE / "data" / "users.json",
        BASE.parent / "data" / "users.json",
        Path.home() / "downloads" / "data" / "users.json",
    ]
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            return path, data
    return None, {}


def main() -> int:
    wanted = (sys.argv[1] if len(sys.argv) > 1 else "Simonlaeng").strip().lower()
    users_path, users = load_users()
    matched = None
    for user in users.values():
        if str(user.get("username", "")).strip().lower() == wanted:
            matched = user
            break

    if not matched:
        print(f"❌ ไม่พบบัญชี {wanted} ใน users.json")
        if users_path:
            print(f"ไฟล์ผู้ใช้: {users_path}")
            print("บัญชีที่พบ:")
            for user in users.values():
                print("-", user.get("username"), user.get("id"))
        else:
            print("❌ ไม่พบ users.json ของระบบ 8032")
        return 1

    owner_key = str(matched.get("id") or "").strip()
    if not owner_key:
        print("❌ บัญชีนี้ไม่มี user_id")
        return 1

    registry = {
        "version": 1,
        "owner_key": owner_key,
        "owner_username": matched.get("username", ""),
    }
    save_registry(BASE, registry)
    owner_dir = user_space_dir(BASE, owner_key)

    legacy_files = [
        "remote_show_state.json",
        "detail_swipe_7000.json",
        "id_home.json",
        "creative_room_top.json",
        "final_creative_top.json",
        "simple_creative_top.json",
    ]
    copied = []
    kept = []
    for name in legacy_files:
        src = DATA / name
        dst = owner_dir / name
        if dst.exists():
            kept.append(name)
        elif src.exists():
            shutil.copy2(src, dst)
            copied.append(name)

    print("✅ ผูกพื้นที่เดิมกับบัญชี:", matched.get("username"))
    print("✅ owner_key:", owner_key)
    print("✅ โฟลเดอร์ส่วนตัว:", owner_dir)
    if copied:
        print("✅ คัดลอกข้อมูลเดิม:", ", ".join(copied))
    if kept:
        print("ℹ️ มีข้อมูลส่วนตัวอยู่แล้ว ไม่ได้เขียนทับ:", ", ".join(kept))
    print("✅ สมาชิกคนอื่นจะเริ่มจาก Creative Room ว่างของตนเอง")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
