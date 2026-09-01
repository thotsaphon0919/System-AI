from pathlib import Path
import json

p = Path("main.py")
s = p.read_text(encoding="utf-8")

MARK = "# === INFINI_PLUS_LONGPRESS_SHEET_PATTERN_V1 ==="

inject_html = r'''
<!-- PLUS_LONGPRESS_SHEET_PATTERN_V1 -->
<style>
  /* ซ่อน UI เก่าที่รก */
  .plus-sheet-maker-v1,
  .plus-sheet-mini-v2,
  .sp-quick-bar{
    display:none !important;
    opacity:0 !important;
    pointer-events:none !important;
  }

  .plus-longpress-ready-v1{
    touch-action: manipulation;
  }

  .plus-longpress-ready-v1.plus-holding-v1{
    outline:2px solid rgba(255,170,45,.95) !important;
    outline-offset:4px !important;
    box-shadow:0 0 28px rgba(255,160,35,.55) !important;
  }

  .sheet-pattern-panel-v3{
    position:fixed;
    left:14px;
    right:14px;
    bottom:18px;
    z-index:999999;
    background:#0b0806;
    border:1px solid #8b4b1f;
    border-radius:24px;
    padding:14px;
    box-shadow:0 20px 60px rgba(0,0,0,.7);
    font-family:system-ui,sans-serif;
    display:none;
    color:#fff;
  }

  .sheet-pattern-panel-v3.open{
    display:block;
  }

  .sheet-pattern-panel-v3 .head{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:10px;
    margin-bottom:10px;
  }

  .sheet-pattern-panel-v3 .title{
    color:#ffad32;
    font-weight:900;
    font-size:18px;
  }

  .sheet-pattern-panel-v3 .close{
    border:1px solid #593018;
    background:#160d08;
    color:#ffad32;
    border-radius:999px;
    padding:6px 10px;
    font-weight:900;
  }

  .sheet-pattern-panel-v3 select,
  .sheet-pattern-panel-v3 input{
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

  .sheet-pattern-panel-v3 button.create{
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

  .sheet-pattern-panel-v3 .hint{
    color:#c9b9aa;
    font-size:13px;
    margin:4px 0 8px;
  }
</style>

<script>
(function(){
  if(window.__PLUS_LONGPRESS_SHEET_PATTERN_V1__) return;
  window.__PLUS_LONGPRESS_SHEET_PATTERN_V1__ = true;

  const patterns = [
    ["basic", "Basic Sheet"],
    ["product", "Product Sheet"],
    ["catalog", "Catalog Grid"],
    ["vintage", "Vintage Sheet"],
    ["promo", "Promo Sheet"],
    ["gallery", "Gallery Sheet"],
    ["market", "Market Sheet"]
  ];

  function visible(el){
    if(!el) return false;
    const st = window.getComputedStyle(el);
    if(st.display === "none" || st.visibility === "hidden" || st.opacity === "0") return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }

  function looksLikePlus(el){
    const txt = (el.innerText || el.textContent || "").trim();
    const aria = (el.getAttribute("aria-label") || "").toLowerCase();
    const title = (el.getAttribute("title") || "").toLowerCase();
    const cls = (el.className || "").toString().toLowerCase();
    const href = (el.getAttribute("href") || "").toLowerCase();

    if(txt === "+" || txt === "＋") return true;
    if(txt.includes("＋")) return true;
    if(txt === "เพิ่ม") return true;
    if(aria.includes("add") || aria.includes("plus") || aria.includes("เพิ่ม")) return true;
    if(title.includes("add") || title.includes("plus") || title.includes("เพิ่ม")) return true;
    if(cls.includes("plus") || cls.includes("add")) return true;
    if(href.includes("add") || href.includes("upload") || href.includes("new")) return true;

    return false;
  }

  function ensurePanel(){
    let panel = document.getElementById("sheet_pattern_panel_v3");
    if(panel) return panel;

    panel = document.createElement("div");
    panel.id = "sheet_pattern_panel_v3";
    panel.className = "sheet-pattern-panel-v3";

    let opts = "";
    for(const item of patterns){
      opts += '<option value="' + item[0] + '">' + item[1] + '</option>';
    }

    panel.innerHTML =
      '<div class="head">' +
        '<div class="title">เลือกแพทเทิร์นแผ่น</div>' +
        '<button class="close" type="button">ปิด</button>' +
      '</div>' +
      '<div class="hint">เปิดจากการกดค้างปุ่ม +</div>' +
      '<form method="post" action="/sheet-pattern-builder/create">' +
        '<input type="hidden" name="title" id="spv3_title">' +
        '<input type="hidden" name="source_url" id="spv3_source">' +
        '<select name="pattern">' + opts + '</select>' +
        '<input name="note" placeholder="โน้ต เช่น ราคา / ไซซ์ / ฟีลที่ต้องการ">' +
        '<button class="create" type="submit">สร้างแผ่น</button>' +
      '</form>';

    document.body.appendChild(panel);

    panel.querySelector(".close").addEventListener("click", function(){
      panel.classList.remove("open");
    });

    return panel;
  }

  function openPanel(index){
    const panel = ensurePanel();
    document.getElementById("spv3_title").value = "แผ่นจากช่องบวก #" + (index + 1);
    document.getElementById("spv3_source").value = location.pathname + location.search + "#plus-slot-" + (index + 1);
    panel.classList.add("open");
  }

  function bindLongPress(el, index){
    if(el.dataset.plusLongpressReady === "1") return;
    el.dataset.plusLongpressReady = "1";
    el.classList.add("plus-longpress-ready-v1");

    let timer = null;
    let fired = false;

    function start(ev){
      fired = false;
      el.classList.add("plus-holding-v1");

      timer = setTimeout(function(){
        fired = true;
        el.classList.remove("plus-holding-v1");

        try{
          if(navigator.vibrate) navigator.vibrate(35);
        }catch(e){}

        openPanel(index);
      }, 550);
    }

    function end(ev){
      el.classList.remove("plus-holding-v1");
      if(timer){
        clearTimeout(timer);
        timer = null;
      }

      if(fired){
        ev.preventDefault();
        ev.stopPropagation();
        fired = false;
      }
    }

    el.addEventListener("touchstart", start, {passive:true});
    el.addEventListener("touchend", end, {passive:false});
    el.addEventListener("touchcancel", end, {passive:false});

    el.addEventListener("mousedown", start);
    el.addEventListener("mouseup", end);
    el.addEventListener("mouseleave", end);

    el.addEventListener("click", function(ev){
      if(fired){
        ev.preventDefault();
        ev.stopPropagation();
        fired = false;
      }
    }, true);
  }

  function inject(){
    const candidates = Array.from(document.querySelectorAll("a, button, div, span"))
      .filter(el => visible(el))
      .filter(el => looksLikePlus(el))
      .filter(el => !el.closest(".sheet-pattern-panel-v3"))
      .slice(0, 100);

    candidates.forEach((el, idx) => bindLongPress(el, idx));
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", inject);
  }else{
    inject();
  }

  setTimeout(inject, 800);
  setTimeout(inject, 1800);
})();
</script>
'''

block = f'''

# === INFINI_PLUS_LONGPRESS_SHEET_PATTERN_V1 ===
# กดค้างที่ปุ่ม + เพื่อเลือกแพทเทิร์นแผ่น โดยไม่แสดงตัวหนังสือรกบนการ์ด
from fastapi import Request as _PLPReq
from fastapi.responses import Response as _PLPResp

_PLUS_LONGPRESS_HTML_V1 = {json.dumps(inject_html, ensure_ascii=False)}

@app.middleware("http")
async def infini_plus_longpress_sheet_pattern(request: _PLPReq, call_next):
    response = await call_next(request)

    try:
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        text = body.decode("utf-8", errors="ignore")

        if "PLUS_LONGPRESS_SHEET_PATTERN_V1" not in text:
            if "</body>" in text:
                text = text.replace("</body>", _PLUS_LONGPRESS_HTML_V1 + "\\n</body>")
            else:
                text += _PLUS_LONGPRESS_HTML_V1

        headers = dict(response.headers)
        headers.pop("content-length", None)

        return _PLPResp(
            content=text,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html"
        )

    except Exception:
        return response

# === END INFINI_PLUS_LONGPRESS_SHEET_PATTERN_V1 ===
'''

if MARK in s:
    print("มี longpress patch แล้ว ไม่เขียนซ้ำ")
else:
    s += block
    p.write_text(s, encoding="utf-8")
    print("เพิ่ม longpress patch แล้ว")

