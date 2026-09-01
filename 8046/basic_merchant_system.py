from fastapi import Form
from fastapi.responses import HTMLResponse
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import hashlib
import hmac
import html
import json
import secrets
import threading


def setup_basic_merchant_system(app):
    """Simple merchant settlement for INFINI basic rewards."""
    base = Path(__file__).resolve().parent
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    card_file = data_dir / "point_card_system.json"
    admin_pin_file = data_dir / "basic_merchant_admin_pin.txt"
    lock = threading.Lock()

    if not admin_pin_file.exists():
        admin_pin_file.write_text(f"{secrets.randbelow(900000) + 100000}", encoding="utf-8")

    try:
        print(f"[INFINI BASIC] Admin PIN: {admin_pin_file.read_text(encoding='utf-8').strip()}")
    except Exception:
        pass

    def now_iso():
        return datetime.now(timezone.utc).isoformat()

    def safe(value):
        return html.escape(str(value or ""), quote=True)

    def save_state(state):
        tmp = card_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(card_file)

    def load_state():
        if not card_file.exists():
            state = {
                "version": 3,
                "wallet": {
                    "available_inf": 100000,
                    "reserved_inf": 0,
                    "redeemed_inf": 0,
                    "system_fee_inf": 0,
                },
                "templates": [],
                "campaigns": [],
                "copies": [],
                "basic_merchants": [],
                "basic_settlements": [],
            }
            save_state(state)
            return state

        state = json.loads(card_file.read_text(encoding="utf-8"))
        state.setdefault("wallet", {})
        state["wallet"].setdefault("available_inf", 0)
        state["wallet"].setdefault("reserved_inf", 0)
        state["wallet"].setdefault("redeemed_inf", 0)
        state["wallet"].setdefault("system_fee_inf", 0)
        state.setdefault("copies", [])
        state.setdefault("campaigns", [])
        state.setdefault("templates", [])
        state.setdefault("basic_merchants", [])
        state.setdefault("basic_settlements", [])
        return state

    def hash_pin(pin, salt):
        return hashlib.pbkdf2_hmac(
            "sha256",
            (pin or "").encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()

    def verify_pin(pin, merchant):
        expected = str(merchant.get("pin_hash", ""))
        actual = hash_pin(pin, str(merchant.get("pin_salt", "")))
        return bool(expected) and hmac.compare_digest(expected, actual)

    def find_merchant(state, merchant_code):
        target = (merchant_code or "").strip().upper()
        return next(
            (
                m
                for m in state.get("basic_merchants", [])
                if str(m.get("code", "")).upper() == target
            ),
            None,
        )

    def normalize_card_code(raw):
        value = (raw or "").strip()
        if not value:
            return ""
        if "://" in value:
            try:
                parsed = urlparse(value)
                parts = [p for p in parsed.path.split("/") if p]
                if len(parts) >= 3 and parts[-2] == "card":
                    return parts[-1]
            except Exception:
                return value
        if "/tower/card/" in value:
            return value.split("/tower/card/", 1)[1].split("?", 1)[0].split("#", 1)[0].strip("/")
        return value

    def find_card(state, code):
        target = (code or "").strip()
        target_upper = target.upper()
        for card in state.get("copies", []):
            if str(card.get("token", "")) == target:
                return card
            if str(card.get("serial", "")).upper() == target_upper:
                return card
        return None

    def shell(title, body):
        return HTMLResponse(f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{safe(title)}</title>
<style>
*{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
body{{margin:0;background:radial-gradient(circle at top,#2b0b59,#070713 55%,#020205);color:#fff;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:900px;margin:auto;padding:16px 16px 90px}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:16px}}
.top a{{color:#dfc5ff;text-decoration:none;font-weight:900}}
.panel{{border:1px solid rgba(159,79,255,.7);border-radius:25px;background:linear-gradient(145deg,rgba(14,16,40,.97),rgba(40,14,78,.91));padding:18px;margin-bottom:15px;box-shadow:0 0 24px rgba(128,43,255,.18)}}
h1,h2,h3{{margin-top:0}} p{{color:#cbbfdb;line-height:1.55}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:13px}}
.choice{{display:block;text-decoration:none;color:#fff;min-height:150px}}
.choice b{{font-size:23px;color:#e6cfff}}
.choice span{{display:block;color:#bcb0cb;margin-top:9px;line-height:1.45}}
label{{display:block;color:#eadcff;font-weight:900;margin:8px 0 5px}}
input,textarea{{width:100%;padding:13px;border-radius:14px;border:1px solid rgba(170,90,255,.62);background:#080b18;color:#fff;font:inherit}}
textarea{{min-height:170px;resize:vertical}}
.btn{{display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(190,120,255,.78);border-radius:15px;background:linear-gradient(135deg,#742ce7,#a64cff);color:#fff;padding:12px 16px;font-weight:900;text-decoration:none;font:inherit;cursor:pointer;margin-top:11px}}
.btn.alt{{background:#0b1020;color:#dfccff}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.stat{{padding:14px;border:1px solid rgba(159,79,255,.42);border-radius:17px;background:#080b18}}
.stat small{{display:block;color:#aaa0ba}} .stat b{{display:block;color:#7dffd0;font-size:21px;margin-top:5px}}
.ok{{border-color:rgba(74,255,175,.62);background:linear-gradient(145deg,rgba(9,58,41,.82),rgba(12,17,34,.96))}}
.bad{{border-color:rgba(255,93,121,.6);background:linear-gradient(145deg,rgba(78,15,34,.82),rgba(12,17,34,.96))}}
code{{display:block;overflow:auto;padding:11px;border-radius:12px;background:#050711;color:#7dffd0;margin:8px 0}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{padding:10px 7px;border-bottom:1px solid rgba(170,90,255,.23);text-align:left;vertical-align:top}}
.pill{{display:inline-block;padding:5px 9px;border-radius:999px;border:1px solid rgba(80,255,180,.5);color:#7dffd0;font-size:12px;font-weight:900}}
@media(max-width:650px){{.grid{{grid-template-columns:1fr}}.stats{{grid-template-columns:1fr}}table{{font-size:12px}}}}
</style></head><body><main class="wrap">{body}</main></body></html>""")

    @app.get("/tower/basic", response_class=HTMLResponse)
    def basic_home():
        state = load_state()
        merchants = [m for m in state["basic_merchants"] if m.get("status") == "approved"]
        settlements = state["basic_settlements"]
        total_paid = sum(int(s.get("amount_thb", 0)) for s in settlements)
        total_cards = sum(int(s.get("card_count", 0)) for s in settlements)
        body = f"""
        <div class="top"><a href="/tower/cards">← CARD SYSTEM</a><b>BASIC REWARD</b></div>
        <section class="panel"><h1>ระบบรับการ์ดจากร้านค้า</h1>
        <p>ร้านค้าที่ผ่านระบบนำลิงก์หรือรหัสการ์ดมาวางทีละบรรทัด ระบบตรวจ นับ และรวมมูลค่าให้อัตโนมัติ</p>
        <div class="stats"><div class="stat"><small>ร้านค้าที่ผ่าน</small><b>{len(merchants):,}</b></div>
        <div class="stat"><small>การ์ดที่รับแล้ว</small><b>{total_cards:,}</b></div>
        <div class="stat"><small>ยอดร้านค้ารวม</small><b>{total_paid:,} บาท</b></div></div></section>
        <div class="grid">
        <a class="panel choice" href="/tower/basic/merchant"><b>ร้านค้านำการ์ดมาแลก</b><span>วางรหัสหรือ URL ระบบนับจำนวนและยอดให้เอง</span></a>
        <a class="panel choice" href="/tower/basic/settlements"><b>ประวัติชุดที่รับ</b><span>ดูจำนวนการ์ด ยอดรวม และเลขชุดรับแลก</span></a>
        <a class="panel choice" href="/tower/basic/admin/merchants"><b>อนุมัติร้านค้า</b><span>เจ้าของระบบเพิ่มร้านและออกรหัสเข้าใช้งาน</span></a>
        <a class="panel choice" href="/tower/rewards/special"><b>รางวัลพิเศษ</b><span>แลกกับ Point Tower โดยตรง แยกจากร้านค้า</span></a>
        </div>"""
        return shell("Basic Reward", body)

    @app.get("/tower/basic/admin/merchants", response_class=HTMLResponse)
    def merchant_admin_form():
        state = load_state()
        rows = "".join(
            f"<tr><td>{safe(m.get('code'))}</td><td>{safe(m.get('name'))}</td><td><span class='pill'>{safe(m.get('status'))}</span></td><td>{safe(m.get('created_at', ''))[:10]}</td></tr>"
            for m in reversed(state.get("basic_merchants", []))
        ) or '<tr><td colspan="4">ยังไม่มีร้านค้า</td></tr>'
        body = f"""
        <div class="top"><a href="/tower/basic">← BASIC REWARD</a><b>อนุมัติร้านค้า</b></div>
        <section class="panel"><h1>เพิ่มร้านค้าที่ผ่านระบบ</h1>
        <p>Admin PIN แสดงใน Termux ตอนรัน และเก็บที่ <code>data/basic_merchant_admin_pin.txt</code></p>
        <form method="post" action="/tower/basic/admin/merchants">
        <label>Admin PIN</label><input name="admin_pin" inputmode="numeric" required>
        <label>ชื่อร้านค้า</label><input name="shop_name" maxlength="100" required>
        <label>ช่องทางติดต่อ</label><input name="contact" maxlength="160" placeholder="เบอร์โทร / LINE / อีเมล">
        <button class="btn" type="submit">อนุมัติและออกรหัสร้าน</button></form></section>
        <section class="panel"><h2>ร้านค้าในระบบ</h2><table><thead><tr><th>รหัส</th><th>ชื่อร้าน</th><th>สถานะ</th><th>วันที่</th></tr></thead><tbody>{rows}</tbody></table></section>"""
        return shell("อนุมัติร้านค้า", body)

    @app.post("/tower/basic/admin/merchants", response_class=HTMLResponse)
    def merchant_admin_submit(admin_pin: str = Form(...), shop_name: str = Form(...), contact: str = Form("")):
        expected_pin = admin_pin_file.read_text(encoding="utf-8").strip()
        if not hmac.compare_digest((admin_pin or "").strip(), expected_pin):
            return shell("PIN ไม่ถูกต้อง", '<div class="top"><a href="/tower/basic/admin/merchants">← กลับ</a></div><section class="panel bad"><h1>Admin PIN ไม่ถูกต้อง</h1></section>')
        name = (shop_name or "").strip()[:100]
        if not name:
            return shell("ข้อมูลไม่ครบ", '<section class="panel bad"><h1>กรุณาใส่ชื่อร้าน</h1></section>')
        with lock:
            state = load_state()
            code = "SHOP-" + secrets.token_hex(3).upper()
            pin = f"{secrets.randbelow(900000) + 100000}"
            salt = secrets.token_hex(16)
            state["basic_merchants"].append({
                "code": code, "name": name, "contact": (contact or "").strip()[:160],
                "status": "approved", "pin_salt": salt, "pin_hash": hash_pin(pin, salt),
                "created_at": now_iso(),
            })
            save_state(state)
        body = f"""<div class="top"><a href="/tower/basic/admin/merchants">← ร้านค้า</a><b>อนุมัติแล้ว</b></div>
        <section class="panel ok"><h1>ร้านค้าพร้อมใช้งาน</h1><p>ส่งรหัสสองรายการนี้ให้ร้าน</p>
        <label>รหัสร้าน</label><code>{safe(code)}</code><label>PIN ร้าน</label><code>{safe(pin)}</code>
        <a class="btn" href="/tower/basic/merchant">ไปหน้าแลกการ์ด</a></section>"""
        return shell("ร้านค้าพร้อมใช้งาน", body)

    @app.get("/tower/basic/merchant", response_class=HTMLResponse)
    def merchant_settlement_form():
        body = """
        <div class="top"><a href="/tower/basic">← BASIC REWARD</a><b>ร้านค้าแลกการ์ด</b></div>
        <section class="panel"><h1>ส่งการ์ดให้ระบบตรวจ</h1>
        <p>วาง URL, Token หรือเลขการ์ดทีละบรรทัด ไม่ต้องกรอกจำนวน ระบบนับให้เอง</p>
        <form method="post" action="/tower/basic/merchant">
        <label>รหัสร้าน</label><input name="merchant_code" placeholder="SHOP-XXXXXX" autocapitalize="characters" required>
        <label>PIN ร้าน</label><input name="merchant_pin" type="password" inputmode="numeric" required>
        <label>การ์ดที่รับมา</label><textarea name="card_codes" placeholder="https://.../tower/card/xxxxx&#10;INF-12345678-0001&#10;xxxxx" required></textarea>
        <button class="btn" type="submit">ตรวจและรวมยอด</button></form></section>"""
        return shell("ร้านค้าแลกการ์ด", body)

    @app.post("/tower/basic/merchant", response_class=HTMLResponse)
    def merchant_settlement_submit(merchant_code: str = Form(...), merchant_pin: str = Form(...), card_codes: str = Form(...)):
        raw_lines = [line.strip() for line in (card_codes or "").splitlines() if line.strip()]
        if not raw_lines:
            return shell("ไม่มีการ์ด", '<section class="panel bad"><h1>ยังไม่ได้ใส่การ์ด</h1></section>')
        if len(raw_lines) > 500:
            return shell("มากเกินไป", '<section class="panel bad"><h1>รับได้ไม่เกิน 500 ใบต่อชุด</h1></section>')
        codes, seen = [], set()
        for raw in raw_lines:
            code = normalize_card_code(raw)
            key = code.upper()
            if code and key not in seen:
                seen.add(key)
                codes.append(code)
        with lock:
            state = load_state()
            merchant = find_merchant(state, merchant_code)
            if not merchant or merchant.get("status") != "approved" or not verify_pin(merchant_pin, merchant):
                return shell("ร้านค้าไม่ผ่าน", '<div class="top"><a href="/tower/basic/merchant">← กลับ</a></div><section class="panel bad"><h1>รหัสร้านหรือ PIN ไม่ถูกต้อง</h1></section>')
            valid_cards, errors = [], []
            for code in codes:
                card = find_card(state, code)
                if not card:
                    errors.append((code, "ไม่พบการ์ด"))
                elif card.get("status") != "active":
                    errors.append((str(card.get("serial", code)), "การ์ดถูกใช้แล้วหรือไม่พร้อมแลก"))
                else:
                    valid_cards.append(card)
            if errors:
                error_rows = "".join(f"<tr><td>{safe(code)}</td><td>{safe(reason)}</td></tr>" for code, reason in errors)
                return shell("ตรวจไม่ผ่าน", f"""<div class="top"><a href="/tower/basic/merchant">← กลับ</a><b>ยังไม่ปิดการ์ด</b></div>
                <section class="panel bad"><h1>พบการ์ดที่ตรวจไม่ผ่าน</h1><p>ระบบยังไม่รับทั้งชุด แก้รายการแล้วส่งใหม่</p>
                <table><thead><tr><th>รหัส</th><th>สาเหตุ</th></tr></thead><tbody>{error_rows}</tbody></table></section>""")
            total_inf = sum(int(card.get("value_inf", 0)) for card in valid_cards)
            wallet = state["wallet"]
            if total_inf <= 0:
                return shell("ยอดไม่ถูกต้อง", '<section class="panel bad"><h1>มูลค่าการ์ดไม่ถูกต้อง</h1></section>')
            if int(wallet.get("reserved_inf", 0)) < total_inf:
                return shell("ยอดสำรองไม่ครบ", '<section class="panel bad"><h1>INF สำรองในระบบไม่ครบ</h1><p>ระบบจึงยังไม่ปิดการ์ดชุดนี้</p></section>')
            settlement_id = "SET-" + secrets.token_hex(5).upper()
            redeemed_at = now_iso()
            serials = []
            for card in valid_cards:
                card["status"] = "redeemed"
                card["redeemed_at"] = redeemed_at
                card["redeemed_by_merchant"] = merchant["code"]
                card["settlement_id"] = settlement_id
                card["redemption_channel"] = "basic_merchant"
                serials.append(str(card.get("serial", "")))
            wallet["reserved_inf"] = int(wallet.get("reserved_inf", 0)) - total_inf
            wallet["redeemed_inf"] = int(wallet.get("redeemed_inf", 0)) + total_inf
            settlement = {
                "id": settlement_id, "merchant_code": merchant["code"], "merchant_name": merchant["name"],
                "card_count": len(valid_cards), "card_serials": serials, "amount_inf": total_inf,
                "rate_thb_per_inf": 1, "amount_thb": total_inf,
                "status": "pending_payment", "created_at": redeemed_at,
            }
            state["basic_settlements"].append(settlement)
            save_state(state)
        body = f"""<div class="top"><a href="/tower/basic">← BASIC REWARD</a><b>{safe(settlement_id)}</b></div>
        <section class="panel ok" style="text-align:center"><h1>รับการ์ดเข้าระบบแล้ว</h1>
        <div class="stats"><div class="stat"><small>จำนวนการ์ด</small><b>{len(valid_cards):,} ใบ</b></div>
        <div class="stat"><small>มูลค่ารวม</small><b>{total_inf:,} INF</b></div>
        <div class="stat"><small>ยอดจ่ายร้าน MVP</small><b>{total_inf:,} บาท</b></div></div>
        <p>ระบบปิดการ์ดทุกใบแล้ว จึงใช้ซ้ำไม่ได้</p><span class="pill">รอเจ้าของระบบจ่ายเงินให้ร้าน</span><br>
        <a class="btn" href="/tower/basic/settlement/{safe(settlement_id)}">ดูรายละเอียดชุดนี้</a></section>"""
        return shell("รับการ์ดแล้ว", body)

    @app.get("/tower/basic/settlements", response_class=HTMLResponse)
    def settlements_list():
        state = load_state()
        records = list(reversed(state.get("basic_settlements", [])))
        rows = "".join(
            f"<tr><td><a style='color:#ddc8ff' href='/tower/basic/settlement/{safe(s.get('id'))}'>{safe(s.get('id'))}</a></td><td>{safe(s.get('merchant_name'))}</td><td>{int(s.get('card_count', 0)):,}</td><td>{int(s.get('amount_thb', 0)):,} บาท</td><td>{safe(s.get('status'))}</td></tr>"
            for s in records
        ) or '<tr><td colspan="5">ยังไม่มีรายการ</td></tr>'
        body = f"""<div class="top"><a href="/tower/basic">← BASIC REWARD</a><b>ประวัติการรับการ์ด</b></div>
        <section class="panel"><table><thead><tr><th>เลขชุด</th><th>ร้าน</th><th>ใบ</th><th>ยอด</th><th>สถานะ</th></tr></thead><tbody>{rows}</tbody></table></section>"""
        return shell("ประวัติรับการ์ด", body)

    @app.get("/tower/basic/settlement/{settlement_id}", response_class=HTMLResponse)
    def settlement_detail(settlement_id: str):
        state = load_state()
        record = next((s for s in state.get("basic_settlements", []) if s.get("id") == settlement_id), None)
        if not record:
            return shell("ไม่พบรายการ", '<section class="panel bad"><h1>ไม่พบเลขชุดนี้</h1></section>')
        serial_rows = "".join(f"<tr><td>{safe(serial)}</td></tr>" for serial in record.get("card_serials", []))
        body = f"""<div class="top"><a href="/tower/basic/settlements">← ประวัติ</a><b>{safe(record.get('id'))}</b></div>
        <section class="panel"><h1>{safe(record.get('merchant_name'))}</h1>
        <div class="stats"><div class="stat"><small>จำนวน</small><b>{int(record.get('card_count', 0)):,} ใบ</b></div>
        <div class="stat"><small>มูลค่า</small><b>{int(record.get('amount_inf', 0)):,} INF</b></div>
        <div class="stat"><small>ยอดจ่ายร้าน</small><b>{int(record.get('amount_thb', 0)):,} บาท</b></div></div>
        <p>สถานะ: <span class="pill">{safe(record.get('status'))}</span></p></section>
        <section class="panel"><h2>เลขการ์ดในชุด</h2><table><tbody>{serial_rows}</tbody></table></section>"""
        return shell("รายละเอียดชุดรับการ์ด", body)
