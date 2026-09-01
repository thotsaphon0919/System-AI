from pathlib import Path
import json

p = Path("main.py")
s = p.read_text(encoding="utf-8")

# ลบ modal pattern ตัวเก่า ถ้ามี
START = "# === INFINI_MODAL_SHEET_PATTERN_V1 ==="
END = "# === END INFINI_MODAL_SHEET_PATTERN_V1 ==="
while START in s and END in s:
    a = s.index(START)
    b = s.index(END, a) + len(END)
    s = s[:a] + "\n" + s[b:]

MARK = "# === INFINI_MODAL_SHEET_PATTERN_V2 ==="

inject_html = r"""
<!-- INFINI_MODAL_SHEET_PATTERN_V2 -->
<style>
  .infini-modal-pattern-v2{
    margin-top:14px;
    padding:14px;
    border:1px solid rgba(255,160,35,.55);
    border-radius:18px;
    background:rgba(255,160,35,.07);
    font-family:system-ui,sans-serif;
  }
  .infini-modal-pattern-v2 .title{
    color:#ffad32;
    font-weight:900;
    font-size:17px;
    margin-bottom:7px;
  }
  .infini-modal-pattern-v2 .hint{
    color:#cbb8a5;
    font-size:13px;
    margin-bottom:8px;
  }
  .infini-modal-pattern-v2 select,
  .infini-modal-pattern-v2 input{
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
  .infini-modal-pattern-v2 button{
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
  if(window.__INFINI_MODAL_SHEET_PATTERN_V2__) return;
  window.__INFINI_MODAL_SHEET_PATTERN_V2__ = true;

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
    return r.width > 240 && r.height > 200;
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
    if(modal.querySelector(".infini-modal-pattern-v2")) return;

    let opts = "";
    for(const item of patterns){
      opts += '<option value="' + item[0] + '">' + item[1] + '</option>';
    }

    const box = document.createElement("div");
    box.className = "infini-modal-pattern-v2";
    box.innerHTML =
      '<div class="title">เลือกแพทเทิร์นแผ่น</div>' +
      '<div class="hint">ใช้รูป/ข้อมูลในช่องนี้ สร้างเป็นแผ่นอีกแบบได้</div>' +
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
    addPatternBox();
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", run);
  }else{
    run();
  }

  setInterval(run, 500);

  const obs = new MutationObserver(run);
  obs.observe(document.body, {childList:true, subtree:true, attributes:true});
})();
</script>
"""

block = f'''

# === INFINI_MODAL_SHEET_PATTERN_V2 ===
# เพิ่มช่องเลือกแพทเทิร์นแผ่นเข้า popup อัปโหลด/แก้ไขเดิม
from fastapi import Request as _MSPV2Req
from fastapi.responses import Response as _MSPV2Resp

_MODAL_SHEET_PATTERN_HTML_V2 = {json.dumps(inject_html, ensure_ascii=False)}

@app.middleware("http")
async def infini_modal_sheet_pattern_v2(request: _MSPV2Req, call_next):
    response = await call_next(request)

    try:
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        text = body.decode("utf-8", errors="ignore")

        if "INFINI_MODAL_SHEET_PATTERN_V2" not in text:
            if "</body>" in text:
                text = text.replace("</body>", _MODAL_SHEET_PATTERN_HTML_V2 + "\\n</body>")
            else:
                text += _MODAL_SHEET_PATTERN_HTML_V2

        headers = dict(response.headers)
        headers.pop("content-length", None)

        return _MSPV2Resp(
            content=text,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html"
        )

    except Exception:
        return response

# === END INFINI_MODAL_SHEET_PATTERN_V2 ===
'''

if MARK in s:
    print("มี V2 แล้ว ไม่เขียนซ้ำ")
else:
    s += block
    p.write_text(s, encoding="utf-8")
    print("เพิ่ม INFINI_MODAL_SHEET_PATTERN_V2 แล้ว")

