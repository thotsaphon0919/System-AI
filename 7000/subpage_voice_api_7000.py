from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import os
import re
import time

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    import broker_adapters_7000 as broker_adapters
except Exception:
    broker_adapters = None

MODULE_NAME = "INFINI_SUBPAGE_VOICE_API_V1"
BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "subpage_voice_api.json"
RULES_DB = DATA_DIR / "subpage_voice_trading_rules.json"
CUSTOMERS_DB = DATA_DIR / "subpage_voice_customers.json"
PENDING_TTL_SECONDS = 90  # how long a "confirm before send" command stays valid



def _load() -> dict[str, Any]:
    try:
        data = json.loads(DB.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"items": {}}
    except Exception:
        return {"items": {}}


def _save(data: dict[str, Any]) -> None:
    tmp = DB.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DB)
    try:
        os.chmod(DB, 0o600)
    except Exception:
        pass


def _load_rules() -> dict[str, Any]:
    try:
        data = json.loads(RULES_DB.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"items": {}}
    except Exception:
        return {"items": {}}


def _save_rules(data: dict[str, Any]) -> None:
    tmp = RULES_DB.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(RULES_DB)
    try:
        os.chmod(RULES_DB, 0o600)
    except Exception:
        pass


def _default_rules() -> dict[str, Any]:
    return {
        "max_qty_per_order": None,     # e.g. 5000 -> block single orders bigger than this
        "max_order_value": None,       # e.g. 100000 -> block qty*price above this baht value
        "stop_loss_pct": None,         # informational: reminder only, not auto-enforced on price
        "daily_loss_limit": None,      # baht; informational for now (needs realised P&L tracking)
        "blacklist_symbols": [],       # symbols this user never wants to trade
        "require_confirmation": True,  # if False, BUY/SELL/CANCEL send immediately (not recommended)
        "notes": "",                   # free-text reminder read back before risky trades
    }


def _check_rules(cmd: dict[str, Any], rules: dict[str, Any]) -> list[str]:
    """Return a list of Thai-language warnings for anything this command
    violates. An empty list means the command is clean."""
    warnings: list[str] = []
    action = cmd.get("action")
    symbol = (cmd.get("symbol") or "").upper()
    qty = cmd.get("qty")
    price = cmd.get("price")

    if action not in ("BUY", "SELL"):
        return warnings

    blacklist = {s.upper() for s in (rules.get("blacklist_symbols") or [])}
    if symbol and symbol in blacklist:
        warnings.append(f"{symbol} อยู่ในรายการหุ้นที่คุณตั้งไว้ว่าห้ามเทรด")

    max_qty = rules.get("max_qty_per_order")
    if max_qty and isinstance(qty, (int, float)) and qty > max_qty:
        warnings.append(f"จำนวน {qty:g} หุ้น เกินเพดานที่ตั้งไว้ {max_qty:g} หุ้นต่อคำสั่ง")

    max_value = rules.get("max_order_value")
    if max_value and isinstance(qty, (int, float)) and isinstance(price, (int, float)):
        order_value = qty * price
        if order_value > max_value:
            warnings.append(
                f"มูลค่าคำสั่งประมาณ {order_value:,.0f} บาท เกินเพดาน {max_value:,.0f} บาทที่ตั้งไว้"
            )

    notes = str(rules.get("notes") or "").strip()
    if notes and action == "BUY":
        warnings.append(f"อย่าลืม: {notes}")

    return warnings


# In-memory "awaiting confirmation" store. Keyed by scope key. A command
# that touches real money (BUY/SELL/CANCEL) is held here until the user
# says "ยืนยัน"/"confirm" — this exists specifically because a single
# misheard word from speech recognition must never place a real trade
# on its own. Not persisted to disk on purpose: if the server restarts,
# any pending confirmation is simply gone, which is the safe failure mode.
_PENDING: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------
# Multi-customer directory — lets ONE page manage SEVERAL customers'
# accounts (each with its own broker connection, aliases, and trading
# rules), switching between them by voice ("ลูกค้าสมชาย ซื้อ AOT 1000")
# instead of needing a separate page per customer.
#
# Backward compatible: pages that never register any customers keep
# working exactly as before, using the single broker/account/rules
# config stored via _load()/_load_rules() (see command() below).
# ---------------------------------------------------------------------

def _load_customers() -> dict[str, Any]:
    try:
        data = json.loads(CUSTOMERS_DB.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"items": {}}
    except Exception:
        return {"items": {}}


def _save_customers(data: dict[str, Any]) -> None:
    tmp = CUSTOMERS_DB.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CUSTOMERS_DB)
    try:
        os.chmod(CUSTOMERS_DB, 0o600)
    except Exception:
        pass


def _new_customer_id(name: str, existing: dict[str, Any]) -> str:
    base = re.sub(r"[^a-zA-Z0-9ก-๙]+", "_", (name or "customer").strip()).strip("_") or "customer"
    base = base[:40]
    cid = base
    n = 2
    while cid in existing:
        cid = f"{base}_{n}"
        n += 1
    return cid


def _match_customer_prefix(text: str, customers: dict[str, Any]) -> tuple[str | None, str]:
    """
    If `text` starts with a registered customer's name (optionally after
    the word "ลูกค้า"/"customer"), return (customer_id, remaining_text).
    Otherwise return (None, text) unchanged. Longest name match wins so
    "สมชาย ใจดี" doesn't get short-matched by a customer named just
    "สมชาย" if both exist.
    """
    t = text.strip()
    if not t or not customers:
        return None, text

    m = re.match(r"^(?:ลูกค้า|customer)\s*[:：]?\s*(.+)$", t, re.IGNORECASE)
    search_in = m.group(1).strip() if m else t

    best_id, best_name = None, ""
    for cid, c in customers.items():
        name = str((c or {}).get("name") or "").strip()
        if name and search_in.lower().startswith(name.lower()) and len(name) > len(best_name):
            best_id, best_name = cid, name

    if best_id is None:
        return None, text

    rest = search_in[len(best_name):].strip(" ,:：-")
    return best_id, rest


_MEM_REMEMBER_RE = re.compile(
    r"^(?:จำไว้(?:ว่า|นะ)?|จำว่า|help\s*remember)\s*(.+?)\s*(?:คือ|=|เท่ากับ|equals?|is)\s*(.+)$",
    re.IGNORECASE,
)
_MEM_UPDATE_RE = re.compile(r"^(?:แก้ไข|แก้)\s*(.+?)\s*เป็น\s*(.+)$", re.IGNORECASE)
_MEM_FORGET_RE = re.compile(r"^(?:ลืมคำ(?:ว่า)?|ลบคำ(?:ว่า)?|forget)\s*(.+)$", re.IGNORECASE)
_MEM_READ_RE = re.compile(
    r"^(?:อ่านคำที่จำไว้|อ่านความจำ|คำที่จำไว้มีอะไรบ้าง|list\s*memory)\s*$",
    re.IGNORECASE,
)


def _parse_memory_command(text: str) -> dict[str, Any] | None:
    """
    Voice-driven alias memory, separate from the trading command parser.
    Lets a user teach/forget/list personal shorthand by speaking, instead
    of only being able to type it into the "สอนภาษาของฉัน" textarea.
    Returns None if `text` isn't a memory command at all.
    """
    t = text.strip()

    m = _MEM_REMEMBER_RE.match(t)
    if m:
        word, value = m.group(1).strip(), m.group(2).strip()
        if word and value:
            return {"mem_action": "REMEMBER", "word": word, "value": value}

    m = _MEM_UPDATE_RE.match(t)
    if m:
        word, value = m.group(1).strip(), m.group(2).strip()
        if word and value:
            return {"mem_action": "REMEMBER", "word": word, "value": value}

    m = _MEM_FORGET_RE.match(t)
    if m:
        word = m.group(1).strip()
        if word:
            return {"mem_action": "FORGET", "word": word}

    if _MEM_READ_RE.match(t):
        return {"mem_action": "READ"}

    return None


def _user_key(request: Request) -> str:
    raw = request.cookies.get("infini_session") or request.cookies.get("session") or "local"
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16]


def _scope_key(request: Request, scope: str) -> str:
    scope = (scope or request.url.path or "/").strip()[:300]
    return f"{_user_key(request)}::{scope}"


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    return value[:3] + "••••••••" + value[-3:]


def _replace_aliases(text: str, aliases: dict[str, str]) -> str:
    out = text
    for src in sorted(aliases, key=len, reverse=True):
        dst = str(aliases.get(src) or "").strip()
        if src.strip() and dst:
            out = re.sub(re.escape(src.strip()), dst, out, flags=re.I)
    return out


def _num(s: str | None):
    if not s:
        return None
    s = s.replace(",", "").strip()
    try:
        return float(s) if "." in s else int(s)
    except Exception:
        return None


_CONFIRM_WORDS = re.compile(r"(ยืนยัน|ตกลง|โอเค|\bokay\b|\bok\b|\bconfirm\b|\byes\b|ใช่)", re.I)
_DENY_WORDS = re.compile(r"(ไม่ใช่|ไม่ยืนยัน|ยกเลิกคำสั่งนี้|\bno\b|cancel this|\bdeny\b)", re.I)


def _is_confirmation(text: str) -> bool:
    return bool(_CONFIRM_WORDS.search((text or "").strip()))


def _is_denial(text: str) -> bool:
    return bool(_DENY_WORDS.search((text or "").strip()))


def _parse_command(text: str, account_label: str, aliases: dict[str, str]) -> dict[str, Any]:
    raw = (text or "").strip()
    t = _replace_aliases(raw, aliases).strip()
    low = t.lower()

    action = "ASK"
    if re.search(r"\b(cancel|ยกเลิก|ถอน|ล้าง)\b", low):
        action = "CANCEL"
    elif re.search(r"\b(sell|ขาย|offer)\b", low):
        action = "SELL"
    elif re.search(r"\b(buy|ซื้อ|bid|บิด|เคาะซื้อ)\b", low):
        action = "BUY"
    elif re.search(r"(พอร์ต|portfolio|ถืออะไร|position)", low):
        action = "PORTFOLIO"
    elif re.search(r"(ออเดอร์|order|คำสั่งค้าง)", low):
        action = "ORDERS"
    elif re.search(r"(ราคา|price|quote|bid.?offer)", low):
        action = "QUOTE"
    elif re.search(r"(volume|วอลุ่ม|มูลค่า)", low):
        action = "VOLUME"

    target = account_label or "CURRENT_SHEET"
    m = re.search(r"(?:บัญชี|แอคเคาท์|account)\s*([0-9]+)\s*(?:-|ถึง|to)\s*([0-9]+)", low)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a <= b and b - a <= 200:
            target = list(range(a, b + 1))
    else:
        m = re.search(r"(?:บัญชี|แอคเคาท์|account)\s*([0-9]+)", low)
        if m:
            target = [int(m.group(1))]
        elif re.search(r"(ทุกบัญชี|ทั้งหมดทุกบัญชี|all accounts)", low):
            target = "ALL_ACCOUNTS"

    # หุ้นไทย/US: พยายามจับ token ตัวพิมพ์ใหญ่ก่อน แล้วค่อยตัวอักษรหลังคำซื้อ/ขาย/ราคา
    symbol = None
    tokens = re.findall(r"\b[A-Z][A-Z0-9\.\-]{1,11}\b", t)
    stop = {"BUY", "SELL", "CANCEL", "ORDER", "API", "AI", "ALL"}
    for tok in tokens:
        if tok.upper() not in stop:
            symbol = tok.upper()
            break
    if not symbol:
        m = re.search(r"(?:ซื้อ|ขาย|บิด|bid|buy|sell|ราคา|quote)\s+([A-Za-z][A-Za-z0-9\.\-]{1,11})", t, re.I)
        if m:
            symbol = m.group(1).upper()

    qty = None
    price = None
    m = re.search(r"(?:จำนวน|qty|quantity|หุ้น)\s*([0-9][0-9,]*)", low)
    if m:
        qty = _num(m.group(1))
    else:
        # รูปแบบ AOT 1000 @ 40.50
        m = re.search(r"\b[A-Za-z][A-Za-z0-9\.\-]{1,11}\b\s+([0-9][0-9,]*)", t)
        if m:
            qty = _num(m.group(1))

    m = re.search(r"(?:ราคา|price|@|ที่)\s*([0-9]+(?:\.[0-9]+)?)", low)
    if m:
        price = _num(m.group(1))

    return {
        "raw": raw,
        "normalized_text": t,
        "action": action,
        "target": target,
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "account_context": account_label or "",
        "ready_for_broker": bool(action in {"BUY", "SELL", "CANCEL"}),
        "created_at": int(time.time()),
    }


INJECT = r'''
<!-- INFINI_SUBPAGE_VOICE_API_V1 -->
<style>
#ivx-panel{margin:16px auto 18px;max-width:760px;border:1px solid rgba(255,133,28,.58);border-radius:24px;background:linear-gradient(180deg,#100803,#050505);color:#fff;padding:14px;box-shadow:0 0 26px rgba(255,128,20,.10);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
#ivx-panel *{box-sizing:border-box}
#ivx-panel .ivx-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}
#ivx-panel .ivx-title{font-weight:1000;font-size:18px;color:#ff9b38}
#ivx-panel .ivx-status{font-size:12px;color:#aaa}
#ivx-panel .ivx-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
#ivx-panel input,#ivx-panel textarea{width:100%;border:1px solid rgba(255,137,39,.30);border-radius:15px;background:#0b0b0b;color:#fff;padding:12px;font:inherit;outline:none}
#ivx-panel label{display:block;color:#c9b7a6;font-size:12px;font-weight:800;margin:4px 0 6px}
#ivx-panel .ivx-btnrow{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
#ivx-panel button{border:1px solid rgba(255,137,39,.45);border-radius:15px;background:#16100c;color:#fff;padding:11px 14px;font-weight:900}
#ivx-panel button.ivx-primary{background:#ff8a1f;color:#100700;border-color:#ff8a1f}
#ivx-panel button.ivx-mic{min-width:150px;background:#241004;color:#ffb36e}
#ivx-panel button.ivx-mic.on{background:#ff8a1f;color:#100700;box-shadow:0 0 18px rgba(255,138,31,.35)}
#ivx-panel .ivx-heard{margin-top:10px;border:1px solid rgba(255,255,255,.08);border-radius:15px;background:#080808;padding:10px;min-height:48px;color:#ddd;line-height:1.45}
#ivx-panel .ivx-result{margin-top:8px;color:#ffbd7d;font-size:13px;line-height:1.45}
#ivx-panel details{margin-top:10px;border-top:1px solid rgba(255,255,255,.07);padding-top:9px}
#ivx-panel summary{color:#baaaa0;font-weight:800;cursor:pointer}
@media(max-width:620px){#ivx-panel{margin:12px 10px 16px}.ivx-grid{grid-template-columns:1fr!important}}
</style>
<div id="ivx-panel">
  <div class="ivx-head">
    <div class="ivx-title">🎙️ VOICE + API ของแผ่นนี้</div>
    <div class="ivx-status" id="ivx-status">พร้อม</div>
  </div>
  <details open>
    <summary>👥 ลูกค้าในหน้านี้ <span id="ivx-cust-active-label" style="color:#ffbd7d;font-weight:900"></span></summary>
    <div id="ivx-cust-list" style="display:flex;flex-wrap:wrap;gap:8px;margin:10px 0"></div>
    <div class="ivx-grid">
      <div>
        <label>ชื่อลูกค้าใหม่/แก้ไข</label>
        <input id="ivx-cust-name" placeholder="เช่น สมชาย">
      </div>
      <div>
        <label>Broker ของลูกค้านี้</label>
        <input id="ivx-cust-broker" placeholder="เช่น Bualuang">
      </div>
    </div>
    <div class="ivx-grid" style="margin-top:8px">
      <div>
        <label>เลขบัญชี</label>
        <input id="ivx-cust-account" placeholder="เช่น 1234567-8">
      </div>
      <div>
        <label>API Key / Token (JSON หรือ token เดียว)</label>
        <input id="ivx-cust-api" type="password" autocomplete="off" placeholder="ใส่เฉพาะตอนตั้ง/เปลี่ยน">
      </div>
    </div>
    <div class="ivx-btnrow">
      <button class="ivx-primary" id="ivx-cust-save">บันทึกลูกค้ารายนี้</button>
      <button id="ivx-cust-clear">ล้างฟอร์ม (เพิ่มลูกค้าใหม่)</button>
    </div>
    <div class="ivx-heard" style="margin-top:8px;font-size:12.5px">
      พูดสลับลูกค้าได้เลย เช่น <b>"ลูกค้าสมชาย ซื้อ AOT 1000"</b> — ระบบจะสลับไปหาสมชายและส่งคำสั่งซื้อในประโยคเดียวกัน หรือพูดแค่ <b>"ลูกค้าสมชาย"</b> เพื่อสลับเฉยๆ ก่อนก็ได้
    </div>
  </details>
  <div class="ivx-grid" style="margin-top:12px">
    <div>
      <label>Broker / API ชุดนี้ (โหมดบัญชีเดียว — ถ้าไม่ได้เพิ่มลูกค้าหลายคนด้านบน)</label>
      <input id="ivx-broker" placeholder="เช่น Broker 1">
    </div>
    <div>
      <label>แผ่นนี้ดูแลบัญชี</label>
      <input id="ivx-account" placeholder="เช่น 17 หรือ ลูกค้า A">
    </div>
  </div>
  <label style="margin-top:10px">API Key / Token</label>
  <input id="ivx-api" type="password" autocomplete="off" placeholder="ใส่เฉพาะตอนตั้ง/เปลี่ยน ••••••••">
  <div class="ivx-btnrow">
    <button class="ivx-primary" id="ivx-save">บันทึกการเชื่อม</button>
    <button class="ivx-mic" id="ivx-mic">🎤 เปิดไมค์</button>
    <button id="ivx-stop">■ หยุดฟัง</button>
  </div>
  <div class="ivx-heard" id="ivx-heard">พูดคำสั่งได้เลย เช่น "บัญชี 17 เช็กพอร์ต" หรือ "ซื้อ AOT จำนวน 1000 ราคา 40.50"</div>
  <div class="ivx-result" id="ivx-result"></div>
  <details>
    <summary>สอนภาษาของฉัน</summary>
    <label>รูปแบบ: คำที่ฉันพูด = คำมาตรฐาน (1 บรรทัดต่อ 1 คำ)</label>
    <textarea id="ivx-alias" rows="4" placeholder="หนึ่งไม้=10000\nล้าง=CANCEL\nบิด=BUY"></textarea>
  </details>
  <details>
    <summary>กฎการเทรดของฉัน (ระบบจะเตือน/บล็อกอัตโนมัติ)</summary>
    <div class="ivx-grid">
      <div>
        <label>จำนวนหุ้นสูงสุดต่อคำสั่ง</label>
        <input id="ivx-rule-maxqty" type="number" placeholder="เช่น 5000">
      </div>
      <div>
        <label>มูลค่าสูงสุดต่อคำสั่ง (บาท)</label>
        <input id="ivx-rule-maxvalue" type="number" placeholder="เช่น 100000">
      </div>
    </div>
    <label style="margin-top:10px">หุ้นที่ห้ามเทรด (คั่นด้วยจุลภาค)</label>
    <input id="ivx-rule-blacklist" placeholder="เช่น XYZ, ABC">
    <label style="margin-top:10px">หมายเหตุ/เตือนใจตัวเอง</label>
    <input id="ivx-rule-notes" placeholder="เช่น อย่าเข้าซื้อไล่ราคา">
    <div class="ivx-btnrow">
      <label style="display:flex;align-items:center;gap:8px;margin:0">
        <input id="ivx-rule-confirm" type="checkbox" style="width:auto" checked>
        ต้องพูดยืนยันก่อนส่งคำสั่งจริงทุกครั้ง (แนะนำให้เปิดไว้)
      </label>
    </div>
    <div class="ivx-btnrow">
      <button class="ivx-primary" id="ivx-rule-save">บันทึกกฎการเทรด</button>
    </div>
  </details>
</div>
<script>
(()=>{
  if(window.__INFINI_VOICE_API_V1)return;
  window.__INFINI_VOICE_API_V1=true;
  const $=id=>document.getElementById(id);
  const scope=location.pathname+location.search;
  let listening=false, rec=null, finalText="";

  function aliasObject(){
    const out={};
    ($("ivx-alias").value||"").split(/\n+/).forEach(line=>{
      const p=line.split("=");
      if(p.length>=2){const k=p.shift().trim();const v=p.join("=").trim();if(k&&v)out[k]=v;}
    });
    return out;
  }
  function aliasText(obj){return Object.entries(obj||{}).map(([k,v])=>`${k}=${v}`).join("\n")}
  async function jfetch(url,opt={}){
    const r=await fetch(url,{headers:{"Content-Type":"application/json",...(opt.headers||{})},...opt});
    if(!r.ok)throw new Error(await r.text());
    return await r.json();
  }
  async function loadCfg(){
    try{
      const d=await jfetch(`/infini-voice-api/config?scope=${encodeURIComponent(scope)}`);
      $("ivx-broker").value=d.broker_name||"";
      $("ivx-account").value=d.account_label||"";
      $("ivx-alias").value=aliasText(d.aliases||{});
      $("ivx-status").textContent=d.api_configured?`API เชื่อมแล้ว ${d.api_masked||""}`:"ยังไม่ได้ใส่ API";
    }catch(e){$("ivx-status").textContent="โหลดค่าตั้งไม่สำเร็จ"}
  }
  async function saveCfg(){
    $("ivx-status").textContent="กำลังบันทึก...";
    try{
      const d=await jfetch("/infini-voice-api/config",{method:"POST",body:JSON.stringify({
        scope,
        broker_name:$("ivx-broker").value.trim(),
        account_label:$("ivx-account").value.trim(),
        api_key:$("ivx-api").value.trim(),
        aliases:aliasObject()
      })});
      $("ivx-api").value="";
      $("ivx-status").textContent=d.api_configured?`บันทึกแล้ว • API ${d.api_masked||""}`:"บันทึกแล้ว";
    }catch(e){$("ivx-status").textContent="บันทึกไม่สำเร็จ"}
  }
  function speak(text){
    if(!text || !window.speechSynthesis)return;
    try{
      window.speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(text);
      u.lang="th-TH";
      window.speechSynthesis.speak(u);
    }catch(_e){}
  }
  async function sendCommand(text){
    if(!text.trim())return;
    $("ivx-heard").textContent=text;
    $("ivx-result").textContent="กำลังแปลคำสั่ง...";
    try{
      const d=await jfetch("/infini-voice-api/command",{method:"POST",body:JSON.stringify({scope,text})});
      const c=d.command||{};
      const target=Array.isArray(c.target)?c.target.join(","):c.target;
      let statusLine=`เข้าใจ → ${c.action||"ASK"} | ${c.symbol||"-"} | จำนวน ${c.qty??"-"} | ราคา ${c.price??"-"} | เป้าหมาย ${target||"-"}`;
      if(d.blocked)statusLine="🚫 ถูกบล็อกโดยกฎการเทรดของคุณ";
      else if(d.awaiting_confirmation)statusLine="⏳ รอคำยืนยัน — พูด \"ยืนยัน\" หรือ \"ไม่ใช่\"";
      else if(d.executed)statusLine="✅ "+(d.broker_result?.speak||"ดำเนินการแล้ว");
      $("ivx-result").textContent=statusLine;
      if(d.speak)speak(d.speak);
      window.dispatchEvent(new CustomEvent("infini-voice-command",{detail:c}));
      if(typeof window.infiniHandleVoiceCommand==="function"){
        try{window.infiniHandleVoiceCommand(c)}catch(_e){}
      }
    }catch(e){$("ivx-result").textContent="แปลคำสั่งไม่สำเร็จ: "+e.message}
  }
  function stop(){
    listening=false;
    $("ivx-mic").classList.remove("on");
    $("ivx-mic").textContent="🎤 เปิดไมค์";
    try{rec&&rec.stop()}catch(_e){}
  }
  function start(){
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){
      $("ivx-result").textContent="เบราว์เซอร์นี้ยังไม่รองรับ Speech Recognition — เปิดด้วย Chrome/Android ก่อน";
      return;
    }
    if(!rec){
      rec=new SR();
      rec.lang="th-TH";
      rec.continuous=true;
      rec.interimResults=true;
      rec.maxAlternatives=1;
      rec.onresult=(ev)=>{
        let interim="";
        for(let i=ev.resultIndex;i<ev.results.length;i++){
          const txt=ev.results[i][0].transcript;
          if(ev.results[i].isFinal){finalText+=txt.trim()+" "; sendCommand(finalText.trim()); finalText="";}
          else interim+=txt;
        }
        if(interim)$("ivx-heard").textContent="กำลังฟัง: "+interim;
      };
      rec.onerror=(ev)=>{$("ivx-result").textContent="ไมค์: "+(ev.error||"error")};
      rec.onend=()=>{if(listening){setTimeout(()=>{try{rec.start()}catch(_e){}},250)}};
    }
    listening=true;
    $("ivx-mic").classList.add("on");
    $("ivx-mic").textContent="● กำลังฟัง";
    $("ivx-result").textContent="พูดได้เลย";
    try{rec.start()}catch(_e){}
  }
  async function loadRules(){
    try{
      const d=await jfetch(`/infini-voice-api/rules?scope=${encodeURIComponent(scope)}`);
      const r=d.rules||{};
      $("ivx-rule-maxqty").value=r.max_qty_per_order??"";
      $("ivx-rule-maxvalue").value=r.max_order_value??"";
      $("ivx-rule-blacklist").value=(r.blacklist_symbols||[]).join(", ");
      $("ivx-rule-notes").value=r.notes||"";
      $("ivx-rule-confirm").checked=r.require_confirmation!==false;
    }catch(e){}
  }
  async function saveRules(){
    try{
      await jfetch("/infini-voice-api/rules",{method:"POST",body:JSON.stringify({
        scope,
        rules:{
          max_qty_per_order:$("ivx-rule-maxqty").value?Number($("ivx-rule-maxqty").value):null,
          max_order_value:$("ivx-rule-maxvalue").value?Number($("ivx-rule-maxvalue").value):null,
          blacklist_symbols:$("ivx-rule-blacklist").value.split(",").map(s=>s.trim().toUpperCase()).filter(Boolean),
          notes:$("ivx-rule-notes").value.trim(),
          require_confirmation:$("ivx-rule-confirm").checked,
        }
      })});
      $("ivx-result").textContent="บันทึกกฎการเทรดแล้ว";
    }catch(e){$("ivx-result").textContent="บันทึกกฎไม่สำเร็จ"}
  }
  let activeCustomerId=null, customersCache=[];
  function renderCustomers(){
    const box=$("ivx-cust-list");
    box.innerHTML="";
    if(!customersCache.length){
      box.innerHTML='<div style="color:#8a8380;font-size:12.5px">ยังไม่มีลูกค้าในหน้านี้ — กรอกฟอร์มด้านล่างเพื่อเพิ่มคนแรก</div>';
    }
    customersCache.forEach(c=>{
      const b=document.createElement("button");
      b.textContent=(c.id===activeCustomerId?"● ":"")+c.name+(c.api_configured?"":" (ยังไม่ตั้ง API)");
      if(c.id===activeCustomerId){b.style.background="#ff8a1f";b.style.color="#100700";b.style.borderColor="#ff8a1f";}
      b.addEventListener("click",()=>switchCustomer(c.id));
      const del=document.createElement("span");
      del.textContent=" ✕";
      del.style.cursor="pointer";del.style.opacity="0.6";del.style.marginLeft="6px";
      del.title="ลบลูกค้ารายนี้";
      del.addEventListener("click",(ev)=>{ev.stopPropagation();deleteCustomer(c.id)});
      b.appendChild(del);
      box.appendChild(b);
    });
    $("ivx-cust-active-label").textContent=activeCustomerId?("• กำลังเลือก: "+(customersCache.find(c=>c.id===activeCustomerId)?.name||"")):"";
  }
  async function loadCustomers(){
    try{
      const d=await jfetch(`/infini-voice-api/customers?scope=${encodeURIComponent(scope)}`);
      customersCache=d.customers||[];
      activeCustomerId=d.active||null;
      renderCustomers();
    }catch(e){}
  }
  async function switchCustomer(cid){
    try{
      await jfetch("/infini-voice-api/customers/switch",{method:"POST",body:JSON.stringify({scope,customer_id:cid})});
      activeCustomerId=cid;
      renderCustomers();
      const name=customersCache.find(c=>c.id===cid)?.name||"";
      $("ivx-result").textContent=`สลับไปลูกค้า ${name} แล้ว`;
    }catch(e){}
  }
  async function deleteCustomer(cid){
    try{
      await jfetch("/infini-voice-api/customers/delete",{method:"POST",body:JSON.stringify({scope,customer_id:cid})});
      await loadCustomers();
    }catch(e){}
  }
  function clearCustomerForm(){
    $("ivx-cust-name").value="";$("ivx-cust-broker").value="";$("ivx-cust-account").value="";$("ivx-cust-api").value="";
  }
  async function saveCustomer(){
    const name=$("ivx-cust-name").value.trim();
    if(!name){$("ivx-result").textContent="ใส่ชื่อลูกค้าก่อนครับ";return}
    try{
      await jfetch("/infini-voice-api/customers",{method:"POST",body:JSON.stringify({
        scope, name,
        broker_name:$("ivx-cust-broker").value.trim(),
        account_label:$("ivx-cust-account").value.trim(),
        api_key:$("ivx-cust-api").value.trim(),
      })});
      clearCustomerForm();
      await loadCustomers();
      $("ivx-result").textContent=`บันทึกลูกค้า ${name} แล้ว`;
    }catch(e){$("ivx-result").textContent="บันทึกลูกค้าไม่สำเร็จ"}
  }
  $("ivx-cust-save")?.addEventListener("click",saveCustomer);
  $("ivx-cust-clear")?.addEventListener("click",clearCustomerForm);
  $("ivx-save")?.addEventListener("click",saveCfg);
  $("ivx-rule-save")?.addEventListener("click",saveRules);
  $("ivx-mic")?.addEventListener("click",()=>listening?stop():start());
  $("ivx-stop")?.addEventListener("click",stop);
  loadCfg();
  loadRules();
  loadCustomers();
})();
</script>
'''


def _execute_broker_command(
    cmd: dict[str, Any], broker_name: str, api_key_raw: str, account_label: str
) -> dict[str, Any]:
    """
    Turn a parsed voice command into a real broker API call (if a broker
    is configured) and produce Thai text ready for text-to-speech.
    Never raises — any failure comes back as {"ok": False, "speak": "..."}.
    """
    action = cmd.get("action")
    symbol = cmd.get("symbol") or ""
    qty = cmd.get("qty")
    price = cmd.get("price")

    if broker_adapters is None:
        return {"ok": False, "speak": "ยังไม่ได้เชื่อมต่อโบรกเกอร์ในระบบนี้"}
    if not (broker_name and api_key_raw):
        return {"ok": False, "speak": "ยังไม่ได้ตั้งค่าโบรกเกอร์และ API key สำหรับแผ่นนี้"}

    try:
        adapter = broker_adapters.get_adapter(broker_name, api_key_raw)
    except Exception as e:
        return {"ok": False, "speak": f"ตั้งค่าโบรกเกอร์ไม่ถูกต้อง: {e}"}

    account_no = account_label or ""
    try:
        if action == "PORTFOLIO":
            rows = adapter.get_portfolio(account_no)
            speak = f"พอร์ตมี {len(rows)} รายการ" if rows else "พอร์ตว่างเปล่า"
            return {"ok": True, "speak": speak, "data": rows}

        if action == "ORDERS":
            rows = adapter.get_orders(account_no)
            speak = f"มีออเดอร์ค้าง {len(rows)} รายการ" if rows else "ไม่มีออเดอร์ค้างอยู่"
            return {"ok": True, "speak": speak, "data": rows}

        if action in ("QUOTE", "VOLUME"):
            if not symbol:
                return {"ok": False, "speak": "ไม่ได้ยินชื่อหุ้นครับ พูดอีกครั้งได้ไหม"}
            q = adapter.get_quote(symbol)
            last = q.get("last") or q.get("lastPrice") or "-"
            speak = f"{symbol} ราคาล่าสุด {last}"
            return {"ok": True, "speak": speak, "data": q}

        if action == "BUY" or action == "SELL":
            if not (symbol and qty):
                return {"ok": False, "speak": "ข้อมูลไม่ครบ ต้องมีชื่อหุ้นและจำนวนหุ้นครับ"}
            result = adapter.place_order(
                account_no=account_no, symbol=symbol, side=action,
                volume=int(qty), price=price,
                price_type="LIMIT" if price else "ATO",
            )
            speak = result.message or ("ส่งคำสั่งสำเร็จ" if result.ok else "ส่งคำสั่งไม่สำเร็จ")
            return {"ok": result.ok, "speak": speak, "order_id": result.broker_order_id, "raw": result.raw}

        if action == "CANCEL":
            order_no = str(cmd.get("order_no") or "").strip()
            if not order_no:
                return {"ok": False, "speak": "บอกเลขที่ออเดอร์ที่จะยกเลิกด้วยครับ"}
            result = adapter.cancel_order(account_no, order_no)
            return {"ok": result.ok, "speak": result.message}

        return {"ok": True, "speak": "ยังไม่เข้าใจคำสั่งนี้ครับ ลองพูดใหม่อีกครั้ง"}

    except Exception as e:
        # BrokerError or anything unexpected — never crash the request,
        # just tell the user (out loud) that something went wrong.
        return {"ok": False, "speak": f"เชื่อมต่อโบรกเกอร์ไม่สำเร็จ: {e}"}


class _InjectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype.lower():
            return response
        if response.headers.get("content-encoding"):
            return response
        try:
            chunks = [chunk async for chunk in response.body_iterator]
            body = b"".join(chunks)
            text = body.decode("utf-8")
        except Exception:
            return response

        markers = ("TOOL LIBRARY", "เพิ่มความสามารถ", "บันทึกความสามารถ", "เพิ่มหน้าถัดไป")
        if "INFINI_SUBPAGE_VOICE_API_V1" not in text and any(m in text for m in markers):
            if "</body>" in text:
                text = text.replace("</body>", INJECT + "</body>", 1)
            else:
                text += INJECT
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(content=text, status_code=response.status_code, headers=headers, media_type="text/html")


def install_subpage_voice_api_7000(app):
    if getattr(app.state, "infini_subpage_voice_api_v1", False):
        return
    app.state.infini_subpage_voice_api_v1 = True

    async def get_config(request: Request, scope: str = ""):
        data = _load()
        key = _scope_key(request, scope)
        item = data.setdefault("items", {}).get(key, {})
        api_key = str(item.get("api_key") or "")
        return JSONResponse({
            "ok": True,
            "broker_name": item.get("broker_name", ""),
            "account_label": item.get("account_label", ""),
            "aliases": item.get("aliases", {}),
            "api_configured": bool(api_key),
            "api_masked": _mask(api_key),
        })

    async def save_config(request: Request):
        payload = await request.json()
        scope = str(payload.get("scope") or "")
        data = _load()
        key = _scope_key(request, scope)
        items = data.setdefault("items", {})
        old = items.get(key, {}) if isinstance(items.get(key, {}), dict) else {}
        new_key = str(payload.get("api_key") or "").strip()
        aliases = payload.get("aliases") if isinstance(payload.get("aliases"), dict) else {}
        item = {
            "broker_name": str(payload.get("broker_name") or "").strip()[:120],
            "account_label": str(payload.get("account_label") or "").strip()[:120],
            "api_key": new_key if new_key else str(old.get("api_key") or ""),
            "aliases": {str(k)[:80]: str(v)[:120] for k, v in list(aliases.items())[:100]},
            "updated_at": int(time.time()),
        }
        items[key] = item
        _save(data)
        return JSONResponse({"ok": True, "api_configured": bool(item["api_key"]), "api_masked": _mask(item["api_key"])})

    async def command(request: Request):
        payload = await request.json()
        scope = str(payload.get("scope") or "")
        text = str(payload.get("text") or "").strip()
        if not text:
            return JSONResponse({"ok": False, "error": "empty command"}, status_code=400)

        skey = _scope_key(request, scope)

        # --- Step 0: resolve which "customer" (broker/account config) this
        # utterance applies to. If this page has registered customers,
        # a spoken "ลูกค้า <ชื่อ> ..." prefix switches the active one; a
        # plain command with no prefix keeps using whichever customer was
        # last active. Pages with no customers registered fall back to
        # the original single-account behavior unchanged. ---
        customers_all = _load_customers()
        cust_scope = customers_all.setdefault("items", {}).setdefault(
            skey, {"customers": {}, "active": None}
        )
        customers = cust_scope.get("customers") or {}

        active_switch_speak = None
        if customers:
            matched_id, remaining = _match_customer_prefix(text, customers)
            if matched_id:
                if cust_scope.get("active") != matched_id:
                    # switching customer mid-session: any trade pending
                    # confirmation belonged to the PREVIOUS customer and
                    # must not be confirmable against the new one.
                    _PENDING.pop(skey, None)
                cust_scope["active"] = matched_id
                _save_customers(customers_all)
                cust_name = customers[matched_id].get("name") or matched_id
                if not remaining:
                    return JSONResponse({
                        "ok": True, "command": {"action": "SWITCH_CUSTOMER"}, "executed": False,
                        "speak": f"สลับไปลูกค้า {cust_name} แล้วครับ พร้อมรับคำสั่งต่อไปเลย",
                        "active_customer": {"id": matched_id, "name": cust_name},
                        "module": MODULE_NAME,
                    })
                text = remaining
                active_switch_speak = f"(ลูกค้า {cust_name}) "

        active_id = cust_scope.get("active")
        active_customer = customers.get(active_id) if active_id else None

        if active_customer:
            aliases = active_customer.get("aliases") or {}
            account_label = str(active_customer.get("account_label") or "")
            broker_name = str(active_customer.get("broker_name") or "")
            api_key_raw = str(active_customer.get("api_key") or "")
            rules = active_customer.get("rules") or _default_rules()
        else:
            # No customers registered for this page — original behavior.
            data = _load()
            item = data.setdefault("items", {}).get(skey, {})
            aliases = item.get("aliases", {}) if isinstance(item, dict) else {}
            account_label = str(item.get("account_label") or "") if isinstance(item, dict) else ""
            broker_name = str(item.get("broker_name") or "") if isinstance(item, dict) else ""
            api_key_raw = str(item.get("api_key") or "") if isinstance(item, dict) else ""
            rules_all = _load_rules()
            rules = rules_all.get("items", {}).get(skey) or _default_rules()

        # --- Step 1: is something already waiting on a yes/no? ---
        pending = _PENDING.get(skey)
        if pending and time.time() - pending["created_at"] < PENDING_TTL_SECONDS:
            if _is_denial(text):
                del _PENDING[skey]
                return JSONResponse({
                    "ok": True, "command": pending["cmd"], "executed": False,
                    "speak": "ยกเลิกคำสั่งแล้ว ยังไม่ได้ส่งอะไรออกไปครับ",
                    "module": MODULE_NAME,
                })
            if _is_confirmation(text):
                del _PENDING[skey]
                result = _execute_broker_command(
                    pending["cmd"], broker_name, api_key_raw, account_label
                )
                return JSONResponse({
                    "ok": True, "command": pending["cmd"], "executed": True,
                    "broker_result": result, "speak": result.get("speak", ""),
                    "module": MODULE_NAME,
                })
            # anything else while pending: drop the stale pending command
            # and fall through to parse this new utterance fresh.
            del _PENDING[skey]

        # --- Step 2: memory command? ("จำไว้ว่า...", "ลืมคำว่า...", "อ่านคำที่จำไว้") ---
        mem_cmd = _parse_memory_command(text)
        if mem_cmd:
            live_aliases = dict(aliases) if isinstance(aliases, dict) else {}
            prefix = active_switch_speak or ""

            if mem_cmd["mem_action"] == "READ":
                if not live_aliases:
                    speak = prefix + "ยังไม่มีคำที่จำไว้เลยครับ"
                else:
                    parts = [f"{k} คือ {v}" for k, v in live_aliases.items()]
                    speak = prefix + "คำที่จำไว้มีดังนี้ " + " และ ".join(parts)
                return JSONResponse({
                    "ok": True, "command": {"action": "MEMORY_READ", "aliases": live_aliases},
                    "executed": False, "speak": speak, "module": MODULE_NAME,
                })

            if mem_cmd["mem_action"] == "FORGET":
                word = mem_cmd["word"]
                existed = word in live_aliases
                live_aliases.pop(word, None)
                speak = prefix + (f"ลืมคำว่า {word} แล้วครับ" if existed else f"ไม่เจอคำว่า {word} ในความจำครับ")
            else:  # REMEMBER
                word, value = mem_cmd["word"], mem_cmd["value"]
                live_aliases[word] = value
                speak = prefix + f"จำไว้แล้วครับ {word} คือ {value}"

            # persist back to whichever store aliases came from
            if active_customer:
                active_customer["aliases"] = live_aliases
                _save_customers(customers_all)
            else:
                data = _load()
                item = data.setdefault("items", {}).setdefault(skey, {})
                item["aliases"] = live_aliases
                _save(data)

            return JSONResponse({
                "ok": True, "command": {"action": mem_cmd["mem_action"], "aliases": live_aliases},
                "executed": False, "speak": speak, "module": MODULE_NAME,
            })

        # --- Step 3: parse the new utterance normally ---
        cmd = _parse_command(text, account_label, aliases if isinstance(aliases, dict) else {})
        warnings = _check_rules(cmd, rules)
        cmd["rule_warnings"] = warnings
        prefix = active_switch_speak or ""

        if cmd.get("action") in ("BUY", "SELL", "CANCEL"):
            if warnings and any(
                "ห้ามเทรด" in w or "เกินเพดาน" in w for w in warnings
            ):
                # hard-blocked by the user's own rules — never queue for confirmation
                speak = prefix + "ทำคำสั่งนี้ไม่ได้ครับ ขัดกับกฎที่คุณตั้งไว้: " + " และ ".join(warnings)
                return JSONResponse({
                    "ok": True, "command": cmd, "executed": False, "blocked": True,
                    "speak": speak, "module": MODULE_NAME,
                })

            require_confirm = rules.get("require_confirmation", True)
            if require_confirm:
                _PENDING[skey] = {"cmd": cmd, "created_at": time.time()}
                target = cmd.get("symbol") or "-"
                qty = cmd.get("qty")
                price = cmd.get("price")
                action_th = {"BUY": "ซื้อ", "SELL": "ขาย", "CANCEL": "ยกเลิกคำสั่ง"}[cmd["action"]]
                speak = f"{prefix}{action_th} {target} จำนวน {qty or '-'} ที่ราคา {price or 'ตลาด'} ยืนยันไหมครับ"
                if warnings:
                    speak += " หมายเหตุ: " + " และ ".join(warnings)
                return JSONResponse({
                    "ok": True, "command": cmd, "executed": False, "awaiting_confirmation": True,
                    "speak": speak, "module": MODULE_NAME,
                })

            # require_confirmation is off — execute immediately (not recommended)
            result = _execute_broker_command(cmd, broker_name, api_key_raw, account_label)
            return JSONResponse({
                "ok": True, "command": cmd, "executed": True,
                "broker_result": result, "speak": prefix + result.get("speak", ""),
                "module": MODULE_NAME,
            })

        # read-only actions (PORTFOLIO / ORDERS / QUOTE / VOLUME / ASK) — no
        # confirmation needed, but still try to answer from the broker if
        # credentials are configured.
        result = _execute_broker_command(cmd, broker_name, api_key_raw, account_label)
        return JSONResponse({
            "ok": True, "command": cmd, "executed": True,
            "broker_result": result, "speak": prefix + result.get("speak", ""),
            "module": MODULE_NAME,
        })

    async def list_customers(request: Request, scope: str = ""):
        skey = _scope_key(request, scope)
        customers_all = _load_customers()
        cust_scope = customers_all.get("items", {}).get(skey, {"customers": {}, "active": None})
        customers = cust_scope.get("customers") or {}
        out = []
        for cid, c in customers.items():
            api_key = str((c or {}).get("api_key") or "")
            out.append({
                "id": cid,
                "name": c.get("name") or cid,
                "broker_name": c.get("broker_name") or "",
                "account_label": c.get("account_label") or "",
                "api_configured": bool(api_key),
                "api_masked": _mask(api_key),
                "aliases": c.get("aliases") or {},
                "rules": c.get("rules") or _default_rules(),
            })
        return JSONResponse({"ok": True, "customers": out, "active": cust_scope.get("active")})

    async def save_customer(request: Request):
        payload = await request.json()
        scope = str(payload.get("scope") or "")
        skey = _scope_key(request, scope)
        customers_all = _load_customers()
        cust_scope = customers_all.setdefault("items", {}).setdefault(
            skey, {"customers": {}, "active": None}
        )
        customers = cust_scope.setdefault("customers", {})

        name = str(payload.get("name") or "").strip()[:80]
        if not name:
            return JSONResponse({"ok": False, "error": "ต้องใส่ชื่อลูกค้า"}, status_code=400)

        cid = str(payload.get("customer_id") or "").strip()
        if not cid or cid not in customers:
            cid = _new_customer_id(name, customers)

        old = customers.get(cid, {}) if isinstance(customers.get(cid), dict) else {}
        new_key = str(payload.get("api_key") or "").strip()
        aliases = payload.get("aliases") if isinstance(payload.get("aliases"), dict) else old.get("aliases", {})
        rules_in = payload.get("rules") if isinstance(payload.get("rules"), dict) else None
        merged_rules = old.get("rules") or _default_rules()
        if rules_in:
            merged_rules = {**_default_rules(), **{k: v for k, v in rules_in.items() if k in _default_rules()}}

        customers[cid] = {
            "name": name,
            "broker_name": str(payload.get("broker_name") or old.get("broker_name") or "").strip()[:120],
            "account_label": str(payload.get("account_label") or old.get("account_label") or "").strip()[:120],
            "api_key": new_key if new_key else str(old.get("api_key") or ""),
            "aliases": {str(k)[:80]: str(v)[:120] for k, v in list((aliases or {}).items())[:100]},
            "rules": merged_rules,
            "updated_at": int(time.time()),
        }
        if not cust_scope.get("active"):
            cust_scope["active"] = cid
        _save_customers(customers_all)
        c = customers[cid]
        return JSONResponse({
            "ok": True, "customer_id": cid, "active": cust_scope.get("active"),
            "api_configured": bool(c["api_key"]), "api_masked": _mask(c["api_key"]),
        })

    async def switch_customer(request: Request):
        payload = await request.json()
        scope = str(payload.get("scope") or "")
        cid = str(payload.get("customer_id") or "").strip()
        skey = _scope_key(request, scope)
        customers_all = _load_customers()
        cust_scope = customers_all.setdefault("items", {}).setdefault(
            skey, {"customers": {}, "active": None}
        )
        if cid not in (cust_scope.get("customers") or {}):
            return JSONResponse({"ok": False, "error": "ไม่พบลูกค้ารายนี้"}, status_code=404)
        if cust_scope.get("active") != cid:
            _PENDING.pop(skey, None)  # don't let a stale pending trade leak across customers
        cust_scope["active"] = cid
        _save_customers(customers_all)
        return JSONResponse({"ok": True, "active": cid})

    async def delete_customer(request: Request):
        payload = await request.json()
        scope = str(payload.get("scope") or "")
        cid = str(payload.get("customer_id") or "").strip()
        skey = _scope_key(request, scope)
        customers_all = _load_customers()
        cust_scope = customers_all.setdefault("items", {}).setdefault(
            skey, {"customers": {}, "active": None}
        )
        customers = cust_scope.setdefault("customers", {})
        customers.pop(cid, None)
        if cust_scope.get("active") == cid:
            cust_scope["active"] = next(iter(customers), None)
            _PENDING.pop(skey, None)
        _save_customers(customers_all)
        return JSONResponse({"ok": True})

    async def get_rules(request: Request, scope: str = ""):
        rules_all = _load_rules()
        rules = rules_all.get("items", {}).get(_scope_key(request, scope)) or _default_rules()
        return JSONResponse({"ok": True, "rules": rules})

    async def save_rules(request: Request):
        payload = await request.json()
        scope = str(payload.get("scope") or "")
        rules_all = _load_rules()
        items = rules_all.setdefault("items", {})
        merged = _default_rules()
        incoming = payload.get("rules") if isinstance(payload.get("rules"), dict) else {}
        merged.update({k: v for k, v in incoming.items() if k in merged})
        items[_scope_key(request, scope)] = merged
        _save_rules(rules_all)
        return JSONResponse({"ok": True, "rules": merged})

    app.add_api_route("/infini-voice-api/config", get_config, methods=["GET"], name="infini_voice_api_get_v1")
    app.add_api_route("/infini-voice-api/config", save_config, methods=["POST"], name="infini_voice_api_save_v1")
    app.add_api_route("/infini-voice-api/command", command, methods=["POST"], name="infini_voice_api_command_v1")
    app.add_api_route("/infini-voice-api/rules", get_rules, methods=["GET"], name="infini_voice_api_rules_get_v1")
    app.add_api_route("/infini-voice-api/rules", save_rules, methods=["POST"], name="infini_voice_api_rules_save_v1")
    app.add_api_route("/infini-voice-api/customers", list_customers, methods=["GET"], name="infini_voice_api_customers_list_v1")
    app.add_api_route("/infini-voice-api/customers", save_customer, methods=["POST"], name="infini_voice_api_customers_save_v1")
    app.add_api_route("/infini-voice-api/customers/switch", switch_customer, methods=["POST"], name="infini_voice_api_customers_switch_v1")
    app.add_api_route("/infini-voice-api/customers/delete", delete_customer, methods=["POST"], name="infini_voice_api_customers_delete_v1")
    app.add_middleware(_InjectMiddleware)
