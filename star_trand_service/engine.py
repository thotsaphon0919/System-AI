from __future__ import annotations
from typing import Any
import json, re, urllib.request, urllib.error
from storage import get_config, get_memory, update_memory

STYLE_AGENTS = [
    "Scalping", "Day Trading", "Swing", "Trend Following",
    "Momentum/Breakout", "Mean Reversion", "Position", "Event-News",
]

HEAD_KEYWORDS = {
    "news": ["ข่าว", "news", "event", "เหตุการณ์"],
    "portfolio": ["พอร์ต", "portfolio", "position", "ถืออะไร", "ต้นทุน"],
    "risk": ["risk", "เสี่ยง", "ความเสี่ยง", "กฎ", "rule", "เกิน", "กระจุก"],
    "technical": ["กราฟ", "technical", "แนวรับ", "แนวต้าน", "breakout", "volume", "วอลุ่ม", "momentum", "trend", "เทรนด์"],
    "sector": ["กลุ่ม", "sector", "leader", "follower", "ตัวนำ", "ตัวตาม", "ธีม", "theme"],
    "market": ["ตลาด", "market", "set", "index", "ดัชนี"],
    "trade": ["แผนเทรด", "trade plan", "จุดเข้า", "จุดออก", "stop", "ไม้", "ซื้อ", "ขาย", "buy", "sell"],
}


def _contains(text: str, kws: list[str]) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in kws)


def route_heads(text: str) -> list[str]:
    heads = [name for name, kws in HEAD_KEYWORDS.items() if _contains(text, kws)]
    if not heads:
        heads = ["market", "technical"]
    # Trade always consumes analysis; keep it last.
    if "trade" in heads:
        for h in ("market", "technical", "risk"):
            if h not in heads: heads.insert(0, h)
    order = ["market", "news", "technical", "sector", "portfolio", "risk", "trade"]
    return [h for h in order if h in heads]


def choose_styles(text: str) -> list[str]:
    low = text.lower()
    if re.search(r"(ทั้ง\s*8|8\s*ตัว|แปดตัว|ประชุมทั้งหมด|all\s*8)", low):
        return STYLE_AGENTS[:]
    selected = []
    mapping = {
        "Scalping": ["scalp", "scalping", "สั้นมาก"],
        "Day Trading": ["day", "intraday", "เดย์", "ในวัน"],
        "Swing": ["swing", "สวิง"],
        "Trend Following": ["trend following", "ตามเทรนด์"],
        "Momentum/Breakout": ["momentum", "breakout", "โมเมนตัม", "เบรก"],
        "Mean Reversion": ["mean reversion", "กลับค่าเฉลี่ย", "เด้งกลับ"],
        "Position": ["position", "ถือยาว", "รอบใหญ่"],
        "Event-News": ["event", "news", "ข่าว", "เหตุการณ์"],
    }
    for name, kws in mapping.items():
        if _contains(low, kws): selected.append(name)
    return selected or ["Swing", "Momentum/Breakout", "Trend Following"]


def _llm_call(messages: list[dict[str, str]]) -> str:
    cfg = get_config()
    api_key = str(cfg.get("api_key") or "").strip()
    base_url = str(cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = str(cfg.get("model") or "gpt-5-mini").strip()
    if not api_key:
        return ""
    body = json.dumps({"model": model, "messages": messages, "temperature": 0.2}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(base_url + "/chat/completions", data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            obj = json.loads(r.read().decode("utf-8"))
        return str(obj["choices"][0]["message"]["content"]).strip()
    except Exception as exc:
        return f"[AI_ERROR] {exc}"


def _head_prompt(head: str, text: str, context: dict[str, Any], memory: dict[str, Any], market_data: dict[str, Any] | None) -> str:
    roles = {
        "market": "Market Head: สรุปภาพตลาด/ธีม/แรงนำจากข้อมูลที่มี ห้ามเดาตัวเลข",
        "news": "News Head: แยกข่าว/เหตุการณ์ที่เกี่ยวข้องและผลกระทบ ห้ามสร้างข่าว",
        "technical": "Technical Head: อ่านราคา/volume/structure/แนวรับแนวต้านจากข้อมูลที่ส่งมาเท่านั้น",
        "sector": "Sector Head: หา sector/theme, leader และ follower ตามหลักยืนยันตลาดก่อน ไม่ไล่ตัวแรกทันที",
        "portfolio": "Portfolio Head: วิเคราะห์พอร์ตเฉพาะบัญชี/context นี้ ห้ามปนบัญชี",
        "risk": "Risk Head: ตรวจ Trade Rules, concentration, invalid assumptions และสิ่งที่ต้องระวัง",
        "trade": "Trade Head: ทำแผนตัดสินใจจากผล Technical/Risk/Account เท่านั้น ไม่ส่งคำสั่งซื้อขายและไม่อ้างว่าซื้อขายแล้ว",
    }
    return f"""คุณคือ {roles[head]}\nคำถามผู้ใช้: {text}\nPage/Account context: {json.dumps(context, ensure_ascii=False)}\nMemory: {json.dumps(memory, ensure_ascii=False)}\nLive/Input data: {json.dumps(market_data or {}, ensure_ascii=False)}\nถ้าข้อมูลสดที่จำเป็นไม่มี ให้บอกชัดว่า 'ต้องมีข้อมูลสด/API' และบอกว่าต้องการข้อมูลอะไร ห้ามแต่งข้อมูลขึ้นเอง ตอบกระชับเป็นภาษาไทย"""


def _style_prompt(style: str, text: str, context: dict[str, Any], market_data: dict[str, Any] | None) -> str:
    return f"""คุณคือ Trading Style AI: {style}. วิเคราะห์คำถามจากมุมของสไตล์นี้เท่านั้น\nคำถาม: {text}\nContext: {json.dumps(context, ensure_ascii=False)}\nData: {json.dumps(market_data or {}, ensure_ascii=False)}\nห้ามเดาราคา/ข่าว/volume ถ้าไม่มีข้อมูลจริง ให้ระบุข้อมูลที่ขาด ตอบสั้น 3-6 บรรทัด"""


def execute(text: str, memory_key: str, context: dict[str, Any], parsed_command: dict[str, Any] | None = None, market_data: dict[str, Any] | None = None) -> dict[str, Any]:
    memory = get_memory(memory_key)
    heads = route_heads(text)
    styles = choose_styles(text) if "sector" in heads or _contains(text, ["8 ตัว", "แปดตัว", "style", "สไตล์"]) else []

    # Do not execute real orders. Convert action into decision-support intent.
    action = str((parsed_command or {}).get("action") or "ASK").upper()
    manual_trade_only = action in {"BUY", "SELL", "CANCEL"}

    results: dict[str, str] = {}
    llm_available = bool(str(get_config().get("api_key") or "").strip())
    for head in heads:
        out = _llm_call([
            {"role": "system", "content": "STAR TRAND Mission Control. ใช้ข้อมูลจริงเท่านั้น ไม่รับประกันกำไร ไม่ส่งคำสั่งซื้อขายจริง"},
            {"role": "user", "content": _head_prompt(head, text, context, memory, market_data)},
        ]) if llm_available else ""
        results[head] = out or "พร้อมทำงาน แต่ยังไม่ได้ตั้ง AI API สำหรับ STAR TRAND"

    style_results: dict[str, str] = {}
    for style in styles:
        out = _llm_call([
            {"role": "system", "content": "STAR TRAND Style Agent. วิเคราะห์เฉพาะข้อมูลที่ได้รับ"},
            {"role": "user", "content": _style_prompt(style, text, context, market_data)},
        ]) if llm_available else ""
        style_results[style] = out or "พร้อมทำงาน แต่ยังไม่ได้ตั้ง AI API สำหรับ STAR TRAND"

    if llm_available:
        summary_prompt = f"""คุณคือ STAR TRAND Assistant ที่คุยกับ Captain คนเดียว\nคำถาม: {text}\nHeads: {json.dumps(results, ensure_ascii=False)}\nStyles: {json.dumps(style_results, ensure_ascii=False)}\nManual trade only: {manual_trade_only}\nสรุปคำตอบเพื่อช่วยตัดสินใจ 3-8 บรรทัด กระชับ ชี้ข้อมูลที่ยังขาด ห้ามสั่งซื้อขายจริง ห้ามรับประกันผลกำไร"""
        answer = _llm_call([{"role":"system","content":"ตอบภาษาไทย กระชับและซื่อสัตย์ต่อข้อมูล"},{"role":"user","content":summary_prompt}])
    else:
        answer = "STAR TRAND รับคำสั่งแล้ว แต่ยังไม่ได้ตั้ง AI API จึงทำได้เฉพาะ routing/context ตอนนี้"

    if manual_trade_only:
        answer += "\nการซื้อ/ขายจริงให้ Captain ทำมือเอง ระบบนี้ไม่ส่งออเดอร์ไปโบรก"
    if not market_data:
        answer += "\nถ้าคำถามต้องใช้ราคาหรือข้อมูลตลาดสด ต้องต่อ Market/Broker Data API แบบอ่านอย่างเดียวก่อน"

    update_memory(memory_key, {"history_append": {"text": text, "heads": heads, "styles": styles, "manual_trade_only": manual_trade_only}})
    return {
        "ok": True,
        "assistant_text": answer.strip(),
        "speak_text": answer.strip(),
        "mission": {"heads": heads, "styles": styles, "manual_trade_only": manual_trade_only},
        "head_results": results,
        "style_results": style_results,
        "memory_key": memory_key,
        "llm_configured": llm_available,
        "market_data_present": bool(market_data),
    }
