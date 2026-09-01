from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8")

MARK = "# === INFINI_PLUS_SLOT_COMPACT_CSS_PATCH_V1 ==="

if MARK in s:
    print("มี compact css patch แล้ว ไม่เขียนซ้ำ")
else:
    patch = r'''

# === INFINI_PLUS_SLOT_COMPACT_CSS_PATCH_V1 ===
# บีบ UI สร้างแผ่นในช่อง + ให้เล็กลง ไม่ให้รกหน้าการ์ด
from fastapi import Request as _PCSReq
from fastapi.responses import Response as _PCSResp

_PLUS_COMPACT_CSS_V1 = """
<!-- PLUS_SLOT_COMPACT_CSS_PATCH_V1 -->
<style>
  .sp-quick-bar{
    display:none !important;
  }

  .plus-sheet-maker-v1{
    position:absolute !important;
    right:8px !important;
    top:8px !important;
    z-index:50 !important;
    display:flex !important;
    align-items:center !important;
    gap:3px !important;
    width:auto !important;
    max-width:112px !important;
    margin:0 !important;
    padding:4px !important;
    border-radius:999px !important;
    background:rgba(10,8,5,.72) !important;
    color:#ffb343 !important;
    box-shadow:0 6px 18px rgba(0,0,0,.35) !important;
    border:1px solid rgba(255,160,35,.75) !important;
  }

  .plus-sheet-maker-v1 .label{
    display:none !important;
  }

  .plus-sheet-maker-v1 select{
    width:68px !important;
    max-width:68px !important;
    height:28px !important;
    padding:2px 4px !important;
    margin:0 !important;
    border-radius:999px !important;
    font-size:11px !important;
    background:#fff7e8 !important;
    color:#111 !important;
  }

  .plus-sheet-maker-v1 button{
    width:36px !important;
    height:28px !important;
    padding:2px !important;
    margin:0 !important;
    border-radius:999px !important;
    font-size:11px !important;
    background:#111 !important;
    color:#fff !important;
  }
</style>
"""

@app.middleware("http")
async def infini_plus_slot_compact_css_patch(request: _PCSReq, call_next):
    response = await call_next(request)

    try:
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        text = body.decode("utf-8", errors="ignore")

        if "PLUS_SLOT_COMPACT_CSS_PATCH_V1" not in text:
            if "</head>" in text:
                text = text.replace("</head>", _PLUS_COMPACT_CSS_V1 + "</head>")
            elif "</body>" in text:
                text = text.replace("</body>", _PLUS_COMPACT_CSS_V1 + "</body>")
            else:
                text += _PLUS_COMPACT_CSS_V1

        headers = dict(response.headers)
        headers.pop("content-length", None)

        return _PCSResp(
            content=text,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html"
        )

    except Exception:
        return response

# === END INFINI_PLUS_SLOT_COMPACT_CSS_PATCH_V1 ===
'''
    p.write_text(s + patch, encoding="utf-8")
    print("เพิ่ม compact css patch แล้ว")

