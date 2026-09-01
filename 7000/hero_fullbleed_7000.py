"""
INFINI hero full-bleed override.

Problem: ".hero" (the big image/banner block at the top of most pages —
zone pages, Point Tower, etc.) is defined with its own
`border:1px solid ...; border-radius:...px; padding:20-28px` in roughly
15 separate places scattered across main.py — each page template style-
copy-pasted its own near-identical version over time. Editing all 15
individually is risky (easy to miss one, easy to break an f-string).

Fix: inject ONE small <style> block, site-wide, late enough in the
cascade (appended just before </head>, or as a fallback appended to
</body> if a page has no </head> in this response) that overrides all of
them with !important — image goes edge-to-edge, no border, no padding.
The original per-page CSS is left completely untouched; this only rides
on top of it at render time, so it's trivially reversible by removing
this one file.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

MARKER = "INFINI_HERO_FULLBLEED_V1"

STYLE = """
<style id="infini-hero-fullbleed">
.hero{
  border:none!important;
  border-radius:0!important;
  padding:0!important;
  box-shadow:none!important;
}
.hero img,
.hero video{
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  display:block!important;
  margin:0!important;
}
/* Text/content that used to rely on .hero's own padding gets its own
   inset instead, so titles etc. don't end up flush against the edge. */
.hero h1,.hero .sub,.hero>div:not([style*="background"]){
  padding-left:20px!important;
  padding-right:20px!important;
}
</style>
"""


class _HeroFullBleedInject(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype.lower() or response.headers.get("content-encoding"):
            return response
        try:
            chunks = [chunk async for chunk in response.body_iterator]
            body = b"".join(chunks)
            text = body.decode("utf-8")
        except Exception:
            return response

        if MARKER not in text:
            tag = f"<!-- {MARKER} -->" + STYLE
            if "</head>" in text:
                text = text.replace("</head>", tag + "</head>", 1)
            elif "<body" in text:
                # No </head> in this fragment — inject right after <body ...>
                idx = text.find(">", text.find("<body")) + 1
                text = text[:idx] + tag + text[idx:]
            else:
                text = tag + text

        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(content=text, status_code=response.status_code,
                         headers=headers, media_type="text/html")


def install_hero_fullbleed_7000(app):
    if getattr(app.state, "infini_hero_fullbleed_v1", False):
        return
    app.state.infini_hero_fullbleed_v1 = True
    app.add_middleware(_HeroFullBleedInject)
