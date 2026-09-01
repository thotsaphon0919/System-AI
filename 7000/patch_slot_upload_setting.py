from pathlib import Path
import json

p = Path("main.py")
s = p.read_text(encoding="utf-8")

# ลบบล็อกทดลองเก่าที่ทำให้รก / กดค้าง / ซ่อนกล้อง
blocks = [
    ("# === INFINI_PLUS_SLOT_SHEET_PATTERN_V1 ===", "# === END INFINI_PLUS_SLOT_SHEET_PATTERN_V1 ==="),
    ("# === INFINI_PLUS_SLOT_COMPACT_CSS_PATCH_V1 ===", "# === END INFINI_PLUS_SLOT_COMPACT_CSS_PATCH_V1 ==="),
    ("# === INFINI_PLUS_LONGPRESS_SHEET_PATTERN_V1 ===", "# === END INFINI_PLUS_LONGPRESS_SHEET_PATTERN_V1 ==="),
    ("# === INFINI_PLUS_LONGPRESS_ONLY_PATTERN_V1 ===", "# === END INFINI_PLUS_LONGPRESS_ONLY_PATTERN_V1 ==="),
    ("# === INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1 ===", "# === END INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1 ==="),
    ("# === INFINI_MODAL_SHEET_PATTERN_V1 ===", "# === END INFINI_MODAL_SHEET_PATTERN_V1 ==="),
    ("# === INFINI_MODAL_SHEET_PATTERN_V2 ===", "# === END INFINI_MODAL_SHEET_PATTERN_V2 ==="),
]

removed = 0
for start, end in blocks:
    while start in s and end in s:
        a = s.index(start)
        b = s.index(end, a) + len(end)
        s = s[:a] + "\n" + s[b:]
        removed += 1

MARK = "# === INFINI_SLOT_UPLOAD_SETTING_V1 ==="

inject_html = r"""
<!-- INFINI_SLOT_UPLOAD_SETTING_V1 -->
<style>
  /* เอา UI ทดลองเก่าทั้งหมดออกจากหน้าการ์ด */
  .plus-sheet-maker-v1,
  .plus-sheet-mini-v2,
  .sp-quick-bar{
    display:none !important;
    visibility:hidden !important;
    opacity:0 !important;
    pointer-events:none !important;
  }

  .infini-slot-click-ready-v1{
    cursor:pointer;
  }

  .infini-slot-click-ready-v1:active{
    outline:2px solid rgba(255,170,45,.85);
    outline-offset:4px;
  }

  .infini-modal-pattern-v3{
    margin-top:14px;
    padding:14px;
    border:1px solid rgba(255,160,35,.55);
    border-radius:18px;
    background:rgba(255,160,35,.07);
    font-family:system-ui,sans-serif;
  }

  .infini-modal-pattern-v3 .title{
    color:#ffad32;
    font-weight:900;
    font-size:17px;
    margin-bottom:7px;
  }

  .infini-modal-pattern-v3 .hint{
    color:#cbb8a5;
    font-size:13px;
    margin-bottom:8px;
  }

  .infini-modal-pattern-v3 select,
  .infini-modal-pattern-v3 input{
    width:100%;
    box-sizing:border-box;
    margin:6px 0;
    padding:12px;
    border-radius:14px;
    border:1px solid #6b3b1d;
    background:#090504;
    color:#fff;
    font-size:15px;
  }

  .infini-modal-pattern-v3 button{
    width:100%;
    border:0;
    border-radius:16px;
    padding:13px;
    margin-top:8px;
    background:linear-gradient(135deg,#ff9f22,#ffbd4a);
    color:#111;
    font-weight:900;
    font-size:16px;
  }
</style>

<script>
(function(){
  if(window.__INFINI_SLOT_UPLOAD_SETTING_V1__) return;
  window.__INFINI_SLOT_UPLOAD_SETTING_V1__ = true;

  const patterns = [
    ["basic", "Basic Sheet"],
    ["product", "Product Sheet"],
    ["catalog", "Catalog Grid"],
    ["vintage", "Vintage Sheet"],
    ["promo", "Promo Sheet"],
    ["gallery", "Gallery Sheet"],
    ["market", "Market Sheet"]
  ];

  function textOf(el){
    return (el.innerText || el.textContent || "").trim();
  }

  function visible(el){
    if(!el) return false;
    const st = getComputedStyle(el);
    if(st.display === "none" || st.visibility === "hidden") return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }

  function isInteractive(el){
    if(!el) return false;
    const tag = (el.tagName || "").toLowerCase();
    return ["input","textarea","select","button","a","label"].includes(tag);
  }

  function looksLikeCamera(el){
    const txt = textOf(el);
    const aria = (el.getAttribute("aria-label") || "").toLowerCase();
    const title = (el.getAttribute("title") || "").toLowerCase();
    const cls = (el.className || "").toString().toLowerCase();

    if(txt.includes("📷") || txt.includes("📸")) return true;
    if(aria.includes("camera") || aria.includes("upload") || aria.includes("photo") || aria.includes("image")) return true;
    if(title.includes("camera") || title.includes("upload") || title.includes("photo") || title.includes("image")) return true;
    if(cls.includes("camera") || cls.includes("upload") || cls.includes("photo") || cls.includes("image")) return true;

    return false;
  }

  function looksLikeSlot(el){
    const txt = textOf(el);
    const r = el.getBoundingClientRect();

    if(r.width < 120 || r.height < 120) return false;

    const hasPlus = txt.includes("+") || txt.includes("＋");
    const hasSub = txt.includes("ย่อย");
    const hasCamera = Array.from(el.querySelectorAll("a,button,div,span")).some(looksLikeCamera);

    return (hasPlus && hasSub) || (hasPlus && hasCamera);
  }

  function findCameraInside(slot){
    const items = Array.from(slot.querySelectorAll("a,button,div,span"))
      .filter(visible)
      .filter(looksLikeCamera);

    if(items.length) return items[0];
    return null;
  }

  function bindSlots(){
    const candidates = Array.from(document.querySelectorAll("div, article, section, a"))
      .filter(visible)
      .filter(looksLikeSlot)
      .slice(0, 80);

    candidates.forEach(function(slot, idx){
      if(slot.dataset.slotUploadSettingReady === "1") return;
      slot.dataset.slotUploadSettingReady = "1";
      slot.classList.add("infini-slot-click-ready-v1");

      slot.addEventListener("click", function(ev){
        if(isInteractive(ev.target) && !looksLikeCamera(ev.target)) return;

        const cam = findCameraInside(slot);
        if(cam && cam !== ev.target){
          ev.preventDefault();
          ev.stopPropagation();
          cam.click();
        }
      }, true);
    });
  }

  function scoreModal(el){
    const t = textOf(el);
    let score = 0;
    if(t.includes("ชื่อแผ่น")) score += 5;
    if(t.includes("รายละเอียด")) score += 3;
    if(t.includes("ลิงก์")) score += 2;
    if(t.includes("อัปโหลดรูป/วิดีโอ")) score += 5;
    if(t.includes("บันทึก")) score += 3;
    if(t.includes("เปิดลิงก์")) score += 2;
    if(t.includes("ปิด")) score += 1;
    return score;
  }

  function findUploadModal(){
    const all = Array.from(document.querySelectorAll("form, dialog, section, article, div"));
    let best = null;
    let bestScore = 0;

    for(const el of all){
      if(!visible(el)) continue;
      const r = el.getBoundingClientRect();
      if(r.width < 260 || r.height < 260) continue;

      const score = scoreModal(el);
      if(score > bestScore){
        best = el;
        bestScore = score;
      }
    }

    if(bestScore >= 8) return best;
    return null;
  }

  function getTitleFromModal(modal){
    const inputs = Array.from(modal.querySelectorAll("input, textarea"));

    for(const input of inputs){
      const ph = input.getAttribute("placeholder") || "";
      const name = input.getAttribute("name") || "";
      if(ph.includes("ชื่อ") || name.includes("title") || name.includes("name")){
        if(input.value && input.value.trim()) return input.value.trim();
      }
    }

    const h = modal.querySelector("h1,h2,h3");
    if(h && textOf(h)) return textOf(h);

    return "แผ่นจากช่องอัปโหลด";
  }

  function addPatternBox(){
    const modal = findUploadModal();
    if(!modal) return;
    if(modal.querySelector(".infini-modal-pattern-v3")) return;

    let opts = "";
    for(const item of patterns){
      opts += '<option value="' + item[0] + '">' + item[1] + '</option>';
    }

    const box = document.createElement("div");
    box.className = "infini-modal-pattern-v3";
    box.innerHTML =
      '<div class="title">เลือกแพทเทิร์นแผ่น</div>' +
      '<div class="hint">อัปโหลด/ตั้งค่าช่องนี้ก่อน แล้วเลือกแพทเทิร์นเพื่อสร้างแผ่นได้</div>' +
      '<select class="pattern">' + opts + '</select>' +
      '<input class="note" placeholder="โน้ต เช่น ราคา / ไซซ์ / ฟีลที่ต้องการ">' +
      '<button type="button" class="create">สร้างแผ่นจากช่องนี้</button>';

    box.querySelector(".create").addEventListener("click", function(ev){
      ev.preventDefault();
      ev.stopPropagation();

      const title = getTitleFromModal(modal);
      const pattern = box.querySelector(".pattern").value || "basic";
      const note = box.querySelector(".note").value || "";

      const form = document.createElement("form");
      form.method = "post";
      form.action = "/sheet-pattern-builder/create";

      function hidden(name, value){
        const i = document.createElement("input");
        i.type = "hidden";
        i.name = name;
        i.value = value;
        form.appendChild(i);
      }

      hidden("title", title);
      hidden("source_url", location.pathname + location.search);
      hidden("pattern", pattern);
      hidden("note", note);

      document.body.appendChild(form);
      form.submit();
    });

    modal.appendChild(box);
  }

  function run(){
    bindSlots();
    addPatternBox();
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", run);
  }else{
    run();
  }

  setInterval(run, 700);

  const obs = new MutationObserver(run);
  obs.observe(document.body, {childList:true, subtree:true, attributes:true});
})();
</script>
"""

block = f'''

# === INFINI_SLOT_UPLOAD_SETTING_V1 ===
# กดช่อง + ให้เข้า popup อัปโหลด/ตั้งค่าเดิม และเพิ่มแพทเทิร์นแผ่นใน popup นั้น
from fastapi import Request as _SUSReq
from fastapi.responses import Response as _SUSResp

_SLOT_UPLOAD_SETTING_HTML_V1 = {json.dumps(inject_html, ensure_ascii=False)}

@app.middleware("http")
async def infini_slot_upload_setting_v1(request: _SUSReq, call_next):
    response = await call_next(request)

    try:
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        text = body.decode("utf-8", errors="ignore")

        if "INFINI_SLOT_UPLOAD_SETTING_V1" not in text:
            if "</body>" in text:
                text = text.replace("</body>", _SLOT_UPLOAD_SETTING_HTML_V1 + "\\n</body>")
            else:
                text += _SLOT_UPLOAD_SETTING_HTML_V1

        headers = dict(response.headers)
        headers.pop("content-length", None)

        return _SUSResp(
            content=text,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html"
        )

    except Exception:
        return response

# === END INFINI_SLOT_UPLOAD_SETTING_V1 ===
'''

if MARK in s:
    print("มี INFINI_SLOT_UPLOAD_SETTING_V1 แล้ว ไม่เขียนซ้ำ")
else:
    s += block
    p.write_text(s, encoding="utf-8")
    print("ลบบล็อกเก่า:", removed)
    print("เพิ่ม INFINI_SLOT_UPLOAD_SETTING_V1 แล้ว")

