"""
INFINI global tools hub + floating gear "door".

Problem this fixes: the gear/settings icon exists in many different
places across the site, but each one only opens whatever that specific
page happened to wire up (some open a real menu, some open nothing,
some point at features that were later replaced). There's no single,
reliable, everywhere-the-same "door" into the full toolset.

Fix, in two parts:
  1. /infini-tools — one page listing every major feature as a single
     complete, always-up-to-date toolset.
  2. A site-wide floating gear button (fixed bottom-right, injected into
     every HTML response) that always opens that same page. It doesn't
     touch or remove any existing per-page gear button — it's additive,
     so nothing that already worked stops working. It just guarantees
     every page has at least one gear that reliably works and leads
     somewhere complete.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

MARKER = "INFINI_GLOBAL_GEAR_V1"

TOOLS_PAGE = r'''<!doctype html><html lang="th"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>เครื่องมือทั้งหมด</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:#050100;color:#fff;font-family:system-ui,-apple-system,sans-serif}
.top{position:sticky;top:0;z-index:10;height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:rgba(0,0,0,.92);border-bottom:1px solid rgba(255,138,31,.3)}
.top b{color:#ff9a2f;letter-spacing:.06em;font-size:14px}
.top a{color:#ffc17d;text-decoration:none;font-size:13px;font-weight:800}
.wrap{max-width:640px;margin:auto;padding:18px 16px 60px}
.groupTitle{color:#ff9a2f;font-size:11px;font-weight:1000;letter-spacing:.12em;margin:22px 4px 10px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.tile{display:block;border:1px solid rgba(255,255,255,.13);border-radius:18px;padding:16px 14px;background:#0b0b0d;text-decoration:none;color:#fff}
.tile .ic{font-size:22px;color:#ff9a2f;display:block;margin-bottom:8px}
.tile b{display:block;font-size:14px}
.tile span{display:block;color:#999;font-size:11px;margin-top:4px}
@media(max-width:420px){.grid{grid-template-columns:1fr}}
</style>
<body>
<div class="top"><b>⚙ เครื่องมือทั้งหมด</b><a href="/id">กลับ ID</a></div>
<div class="wrap">

<div class="groupTitle">คอนเทนต์ของฉัน</div>
<div class="grid">
  <a class="tile" href="/id"><span class="ic">◈</span><b>INFINI ID</b><span>หน้าหลักและโปรไฟล์</span></a>
  <a class="tile" href="/creative-rooms"><span class="ic">▦</span><b>Creative Rooms</b><span>เพิ่มห้องได้ต่อเนื่อง</span></a>
  <a class="tile" href="/poster"><span class="ic">▢</span><b>โปสเตอร์</b><span>Mini App + เผยแพร่สาธารณะ</span></a>
  <a class="tile" href="/friend-chat"><span class="ic">◌</span><b>แชทเพื่อน</b><span>คุยกับเพื่อน</span></a>
</div>

<div class="groupTitle">AI &amp; เสียง</div>
<div class="grid">
  <a class="tile" href="/image-generator"><span class="ic">✦</span><b>สร้างภาพ AI</b><span>เลือกตัวละครได้</span></a>
  <a class="tile" href="/ai-chat"><span class="ic">✦</span><b>AI Chat</b><span>คุยและจัดการร้าน</span></a>
  <a class="tile" href="/shop-scene-builder"><span class="ic">▦</span><b>จัดร้าน V4</b><span>ฉากและสินค้า</span></a>
</div>

<div class="groupTitle">โซนส่วนตัว</div>
<div class="grid">
  <a class="tile" href="/zone/private"><span class="ic">①</span><b>Zone 1</b><span>Private</span></a>
  <a class="tile" href="/zone/office"><span class="ic">②</span><b>Zone 2</b><span>Office</span></a>
  <a class="tile" href="/zone/shop"><span class="ic">③</span><b>Zone 3</b><span>Shop</span></a>
  <a class="tile" href="/zone/portfolio"><span class="ic">④</span><b>Zone 4</b><span>Showcase</span></a>
</div>

<div class="groupTitle">อื่นๆ</div>
<div class="grid">
  <a class="tile" href="/8046/tower"><span class="ic">▲</span><b>Point Tower</b><span>กิจกรรม/รางวัล</span></a>
  <a class="tile" href="/8032/commerce"><span class="ic">$</span><b>Commerce Suite</b><span>ระบบขายของ</span></a>
  <a class="tile" href="/logout"><span class="ic">⏻</span><b>ออกจากระบบ</b><span>Logout</span></a>
</div>

</div>
</body></html>'''

GEAR_HTML = """
<a id="infini-global-gear" href="/infini-tools" aria-label="เครื่องมือทั้งหมด"
   style="position:fixed;right:16px;bottom:86px;z-index:9998;width:52px;height:52px;
          border-radius:999px;background:linear-gradient(135deg,#ff9d2f,#ff7411);
          color:#180800;display:flex;align-items:center;justify-content:center;
          font-size:24px;font-weight:900;text-decoration:none;
          box-shadow:0 8px 24px rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.25)">⚙</a>
"""


class _GlobalGearInject(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype.lower() or response.headers.get("content-encoding"):
            return response
        # Don't add a second floating gear ON the tools page itself.
        if request.url.path == "/infini-tools":
            return response
        try:
            chunks = [chunk async for chunk in response.body_iterator]
            body = b"".join(chunks)
            text = body.decode("utf-8")
        except Exception:
            return response

        if MARKER not in text:
            tag = f"<!-- {MARKER} -->" + GEAR_HTML
            text = text.replace("</body>", tag + "</body>", 1) if "</body>" in text else text + tag

        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(content=text, status_code=response.status_code,
                         headers=headers, media_type="text/html")


def install_global_gear_7000(app):
    if getattr(app.state, "infini_global_gear_v1", False):
        return
    app.state.infini_global_gear_v1 = True

    @app.get("/infini-tools", response_class=HTMLResponse)
    async def infini_tools_page():
        return HTMLResponse(TOOLS_PAGE)

    app.add_middleware(_GlobalGearInject)
