from pathlib import Path
import json

p = Path("main.py")
s = p.read_text(encoding="utf-8")

MARK = "# === INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1 ==="

inject_html = r"""
<!-- INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1 -->
<style>
  /* ซ่อน UI สร้างแผ่นเก่าทั้งหมด */
  .plus-sheet-maker-v1,
  .plus-sheet-mini-v2,
  .sp-quick-bar{
    display:none !important;
    opacity:0 !important;
    pointer-events:none !important;
    visibility:hidden !important;
  }

  /* แผงเลือกแพทเทิร์น ใช้เฉพาะตอนกดค้าง + */
  .sheet-pattern-panel-v5{
    position:fixed;
    left:14px;
    right:14px;
    bottom:18px;
    z-index:999999;
    background:#0b0806;
    border:1px solid #8b4b1f;
    border-radius:26px;
    padding:16px;
    box-shadow:0 22px 70px rgba(0,0,0,.75);
    font-family:system-ui,sans-serif;
    display:none;
    color:#fff;
  }

  .sheet-pattern-panel-v5.open{
    display:block;
  }

  .sheet-pattern-panel-v5 .head{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:10px;
  }

  .sheet-pattern-panel-v5 .title{
    color:#ffad32;
    font-weight:900;
    font-size:19px;
  }

  .sheet-pattern-panel-v5 .close{
    border:1px solid #593018;
    background:#160d08;
    color:#ffad32;
    border-radius:999px;
    padding:7px 12px;
    font-weight:900;
  }

  .sheet-pattern-panel-v5 .hint{
    color:#c9b9aa;
    font-size:13px;
    margin-bottom:10px;
  }

  .sheet-pattern-panel-v5 .pattern-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
    margin:10px 0;
  }

  .sheet-pattern-panel-v5 .pattern-btn{
    border:1px solid #4b2a16;
    background:#130b06;
    color:#fff;
    border-radius:16px;
    padding:12px 8px;
    font-weight:800;
    font-size:14px;
  }

  .sheet-pattern-panel-v5 .pattern-btn.active{
    background:linear-gradient(135deg,#ff9f22,#ffbd4a);
    color:#111;
    border-color:#ffbd4a;
  }

  .sheet-pattern-panel-v5 input{
    width:100%;
    box-sizing:border-box;
    margin:7px 0;
    padding:12px;
    border-radius:16px;
    border:1px solid #4b2a16;
    background:#050505;
    color:#fff;
    font-size:16px;
  }

  .sheet-pattern-panel-v5 button.create{
    width:100%;
    border:0;
    border-radius:18px;
    padding:14px;
    margin-top:8px;
    background:linear-gradient(135deg,#ff9f22,#ffbd4a);
    color:#111;
    font-weight:900;
    font-size:17px;
  }

  .plus-holding-v5{
    outline:2px solid rgba(255,170,45,.95) !important;
    outline-offset:5px !important;
    box-shadow:0 0 30px rgba(255,160,35,.55) !important;
  }
</style>

<script>
(function(){
  if(window.__INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1__) return;
  window.__INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1__ = true;

  const patterns = [
    ["basic", "Basic"],
    ["product", "Product"],
    ["catalog", "Catalog"],
    ["vintage", "Vintage"],
    ["promo", "Promo"],
    ["gallery", "Gallery"],
    ["market", "Market"]
  ];

  let selectedPattern = "basic";

  function visible(el){
    if(!el) return false;
    const st = window.getComputedStyle(el);
    if(st.display === "none" || st.visibility === "hidden") return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }

  function textOf(el){
    return (el.innerText || el.textContent || "").trim();
  }

  function looksLikePlus(el){
    const txt = textOf(el);
    const aria = (el.getAttribute("aria-label") || "").toLowerCase();
    const title = (el.getAttribute("title") || "").toLowerCase();
    const cls = (el.className || "").toString().toLowerCase();
    const href = (el.getAttribute("href") || "").toLowerCase();

    if(txt === "+" || txt === "＋") return true;
    if(txt === "เพิ่ม") return true;
    if(aria.includes("add") || aria.includes("plus") || aria.includes("เพิ่ม")) return true;
    if(title.includes("add") || title.includes("plus") || title.includes("เพิ่ม")) return true;
    if(cls.includes("plus") || cls.includes("add")) return true;
    if(href.includes("add") || href.includes("upload") || href.includes("new")) return true;
    return false;
  }

  function looksLikeCameraOverlay(el){
    const txt = textOf(el);
    const aria = (el.getAttribute("aria-label") || "").toLowerCase();
    const title = (el.getAttribute("title") || "").toLowerCase();
    const cls = (el.className || "").toString().toLowerCase();

    if(txt === "📷" || txt.includes("📷")) return true;
    if(txt === "📸" || txt.includes("📸")) return true;
    if(aria.includes("camera") || aria.includes("upload") || aria.includes("photo") || aria.includes("image")) return true;
    if(title.includes("camera") || title.includes("upload") || title.includes("photo") || title.includes("image")) return true;
    if(cls.includes("camera") || cls.includes("upload") || cls.includes("photo") || cls.includes("image")) return true;

    return false;
  }

  function hideCameraOverlays(){
    const els = Array.from(document.querySelectorAll("a, button, div, span"));
    els.forEach(function(el){
      if(!visible(el)) return;
      if(!looksLikeCameraOverlay(el)) return;

      const r = el.getBoundingClientRect();

      /* ซ่อนเฉพาะไอคอนเล็ก ๆ ที่ลอยบนการ์ด ไม่ไปยุ่งรูปใหญ่ */
      if(r.width <= 90 && r.height <= 90){
        el.style.setProperty("display", "none", "important");
        el.style.setProperty("visibility", "hidden", "important");
        el.style.setProperty("opacity", "0", "important");
        el.style.setProperty("pointer-events", "none", "important");
      }
    });
  }

  function ensurePanel(){
    let panel = document.getElementById("sheet_pattern_panel_v5");
    if(panel) return panel;

    panel = document.createElement("div");
    panel.id = "sheet_pattern_panel_v5";
    panel.className = "sheet-pattern-panel-v5";

    let btns = "";
    for(const item of patterns){
      btns += '<button type="button" class="pattern-btn" data-pattern="' + item[0] + '">' + item[1] + '</button>';
    }

    panel.innerHTML =
      '<div class="head">' +
        '<div class="title">สร้างแผ่น</div>' +
        '<button class="close" type="button">ปิด</button>' +
      '</div>' +
      '<div class="hint">กดค้างปุ่ม + เพื่อเลือกแพทเทิร์นแผ่น</div>' +
      '<form method="post" action="/sheet-pattern-builder/create">' +
        '<input type="hidden" name="title" id="spv5_title">' +
        '<input type="hidden" name="source_url" id="spv5_source">' +
        '<input type="hidden" name="pattern" id="spv5_pattern" value="basic">' +
        '<div class="pattern-grid">' + btns + '</div>' +
        '<input name="note" placeholder="โน้ต เช่น ราคา / ไซซ์ / ฟีลที่ต้องการ">' +
        '<button class="create" type="submit">สร้างแผ่น</button>' +
      '</form>';

    document.body.appendChild(panel);

    panel.querySelector(".close").addEventListener("click", function(){
      panel.classList.remove("open");
    });

    panel.querySelectorAll(".pattern-btn").forEach(function(btn){
      btn.addEventListener("click", function(){
        selectedPattern = btn.dataset.pattern || "basic";
        document.getElementById("spv5_pattern").value = selectedPattern;

        panel.querySelectorAll(".pattern-btn").forEach(function(b){
          b.classList.remove("active");
        });
        btn.classList.add("active");
      });
    });

    const first = panel.querySelector('.pattern-btn[data-pattern="basic"]');
    if(first) first.classList.add("active");

    return panel;
  }

  function openPanel(index){
    const panel = ensurePanel();
    document.getElementById("spv5_title").value = "แผ่นจากช่องบวก #" + (index + 1);
    document.getElementById("spv5_source").value = location.pathname + location.search + "#plus-slot-" + (index + 1);
    document.getElementById("spv5_pattern").value = selectedPattern;
    panel.classList.add("open");
  }

  function bindLongPress(el, index){
    if(el.dataset.plusLongpressV5 === "1") return;
    el.dataset.plusLongpressV5 = "1";

    let timer = null;
    let longPressed = false;

    function start(){
      longPressed = false;
      el.classList.add("plus-holding-v5");
      timer = setTimeout(function(){
        longPressed = true;
        el.classList.remove("plus-holding-v5");
        try{ if(navigator.vibrate) navigator.vibrate(35); }catch(e){}
        openPanel(index);
      }, 650);
    }

    function clear(){
      el.classList.remove("plus-holding-v5");
      if(timer){
        clearTimeout(timer);
        timer = null;
      }
    }

    el.addEventListener("touchstart", start, {passive:true});
    el.addEventListener("touchend", function(ev){
      clear();
      if(longPressed){
        ev.preventDefault();
        ev.stopPropagation();
        longPressed = false;
      }
    }, {passive:false});
    el.addEventListener("touchcancel", clear, {passive:false});

    el.addEventListener("mousedown", start);
    el.addEventListener("mouseup", function(ev){
      clear();
      if(longPressed){
        ev.preventDefault();
        ev.stopPropagation();
        longPressed = false;
      }
    });
    el.addEventListener("mouseleave", clear);
  }

  function bindPlusLongPress(){
    const candidates = Array.from(document.querySelectorAll("a, button, div, span"))
      .filter(el => visible(el))
      .filter(el => looksLikePlus(el))
      .filter(el => !el.closest(".sheet-pattern-panel-v5"))
      .slice(0, 120);

    candidates.forEach((el, idx) => bindLongPress(el, idx));
  }

  function run(){
    hideCameraOverlays();
    bindPlusLongPress();
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", run);
  }else{
    run();
  }

  setTimeout(run, 500);
  setTimeout(run, 1200);
  setTimeout(run, 2500);
})();
</script>
"""

block = f'''

# === INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1 ===
# ซ่อนปุ่ม/ไอคอนที่บังรูปบนการ์ด และใช้กดค้างปุ่ม + เพื่อสร้างแผ่นแทน
from fastapi import Request as _HCOReq
from fastapi.responses import Response as _HCOResp

_HIDE_CARD_OVERLAY_HTML_V1 = {json.dumps(inject_html, ensure_ascii=False)}

@app.middleware("http")
async def infini_hide_card_overlay_buttons(request: _HCOReq, call_next):
    response = await call_next(request)

    try:
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        text = body.decode("utf-8", errors="ignore")

        if "INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1" not in text:
            if "</body>" in text:
                text = text.replace("</body>", _HIDE_CARD_OVERLAY_HTML_V1 + "\\n</body>")
            else:
                text += _HIDE_CARD_OVERLAY_HTML_V1

        headers = dict(response.headers)
        headers.pop("content-length", None)

        return _HCOResp(
            content=text,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html"
        )

    except Exception:
        return response

# === END INFINI_HIDE_CARD_OVERLAY_BUTTONS_V1 ===
'''

if MARK in s:
    print("มี HIDE CARD OVERLAY แล้ว ไม่เขียนซ้ำ")
else:
    s += block
    p.write_text(s, encoding="utf-8")
    print("เพิ่ม HIDE CARD OVERLAY แล้ว")

