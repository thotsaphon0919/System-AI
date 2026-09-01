from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


MARKER = "INFINI_FORCE_FLAT_CREATIVE_V3"

INJECT = r"""
<!-- INFINI_FORCE_FLAT_CREATIVE_V3 -->
<style>
  /* เหลือรูปและข้อความบน CREATIVE ROOM โดยตรง */
  .ifc3-creative{
    position:relative !important;
    overflow:hidden !important;
    min-height:300px !important;
    background-position:center !important;
    background-size:cover !important;
    background-repeat:no-repeat !important;
  }

  .ifc3-creative::before{
    content:"" !important;
    position:absolute !important;
    inset:0 !important;
    z-index:0 !important;
    pointer-events:none !important;
    background:
      linear-gradient(
        100deg,
        rgba(0,0,0,.66) 0%,
        rgba(0,0,0,.42) 58%,
        rgba(0,0,0,.22) 100%
      ) !important;
  }

  .ifc3-creative > *{
    position:relative !important;
    z-index:2 !important;
  }

  /* ลบกรอบดำชั้นในทั้งหมด แต่ไม่แตะปุ่มอัปโหลด */
  .ifc3-clear,
  .ifc3-clear::before,
  .ifc3-clear::after{
    background:none !important;
    background-color:transparent !important;
    background-image:none !important;
    border:none !important;
    outline:none !important;
    box-shadow:none !important;
    backdrop-filter:none !important;
    -webkit-backdrop-filter:none !important;
  }

  .ifc3-creative h1,
  .ifc3-creative h2,
  .ifc3-creative h3,
  .ifc3-creative p,
  .ifc3-creative span{
    text-shadow:
      0 3px 10px rgba(0,0,0,.98),
      0 0 4px rgba(0,0,0,.96) !important;
  }

  /* ช่อง ZONE 1–4 กลับเป็นช่องดำธรรมดา */
  .ifc3-zone{
    background:#070707 !important;
    background-image:none !important;
  }

  .ifc3-zone::before,
  .ifc3-zone::after{
    display:none !important;
    background:none !important;
  }

  .ifc3-zone .infini-card-upload,
  .ifc3-zone button[data-card-key],
  .ifc3-zone [aria-label*="อัปโหลดรูป"]{
    display:none !important;
    visibility:hidden !important;
    pointer-events:none !important;
  }
</style>

<script>
(function(){
  if(window.__INFINI_FORCE_FLAT_CREATIVE_V3__){
    return;
  }

  window.__INFINI_FORCE_FLAT_CREATIVE_V3__ = true;

  function clean(value){
    return String(value || "")
      .replace(/\s+/g," ")
      .trim()
      .toUpperCase();
  }

  function exactLeaf(text){
    const wanted = clean(text);

    return Array.from(
      document.querySelectorAll("body *")
    ).find(function(element){
      return (
        element.children.length === 0 &&
        clean(element.textContent) === wanted
      );
    }) || null;
  }

  function findCreativeOuter(){
    const byData =
      document.querySelector(
        '[data-infini-picture-key="creative"]'
      );

    if(byData){
      return byData;
    }

    const label = exactLeaf("CREATIVE ROOM");

    if(!label){
      return null;
    }

    const byClass =
      label.closest(
        ".infini-picture-card"
      );

    if(byClass){
      return byClass;
    }

    let node = label.parentElement;
    let best = null;

    while(node && node !== document.body){
      const rect =
        node.getBoundingClientRect();

      if(
        rect.width >= 250 &&
        rect.height >= 180 &&
        rect.height <= 800
      ){
        best = node;

        if(
          node.querySelector(
            ".infini-card-upload," +
            "button[data-card-key='creative']"
          )
        ){
          return node;
        }
      }

      node = node.parentElement;
    }

    return best;
  }

  function flattenCreative(){
    const outer = findCreativeOuter();

    if(!outer){
      return false;
    }

    outer.classList.add(
      "ifc3-creative"
    );

    const label = exactLeaf(
      "CREATIVE ROOM"
    );

    if(label && outer.contains(label)){
      let node = label.parentElement;

      while(
        node &&
        node !== outer
      ){
        if(
          node.tagName !== "BUTTON" &&
          node.tagName !== "A"
        ){
          node.classList.add(
            "ifc3-clear"
          );
        }

        node = node.parentElement;
      }
    }

    /*
      จับชั้นใหญ่ภายในที่ยังคลุมรูปอยู่
      แต่เว้นปุ่มอัปโหลดและปุ่มเข้าใช้งาน
    */
    const outerRect =
      outer.getBoundingClientRect();

    Array.from(
      outer.querySelectorAll("*")
    ).forEach(function(element){
      if(
        element.tagName === "BUTTON" ||
        element.tagName === "A" ||
        element.tagName === "INPUT" ||
        element.closest(
          ".infini-card-upload," +
          "[data-card-key='creative']"
        )
      ){
        return;
      }

      const rect =
        element.getBoundingClientRect();

      if(
        rect.width <= 0 ||
        rect.height <= 0
      ){
        return;
      }

      const widthRatio =
        rect.width /
        Math.max(outerRect.width,1);

      const heightRatio =
        rect.height /
        Math.max(outerRect.height,1);

      if(
        widthRatio >= .68 &&
        heightRatio >= .32
      ){
        element.classList.add(
          "ifc3-clear"
        );
      }
    });

    return true;
  }

  function findZoneCard(number){
    const byData =
      document.querySelector(
        '[data-infini-picture-key="zone' +
        number +
        '"]'
      );

    if(byData){
      return byData;
    }

    const label = exactLeaf(
      "ZONE " + number
    );

    if(!label){
      return null;
    }

    const direct =
      label.closest(
        ".infini-picture-card," +
        ".zone-card,.zoneCard,.zone," +
        ".card,.tile,a,button"
      );

    if(direct){
      return direct;
    }

    let node = label.parentElement;

    while(node && node !== document.body){
      const rect =
        node.getBoundingClientRect();

      if(
        rect.width >= 120 &&
        rect.height >= 100 &&
        rect.height <= 500
      ){
        return node;
      }

      node = node.parentElement;
    }

    return null;
  }

  function makeZonesPlain(){
    [1,2,3,4].forEach(function(number){
      const card =
        findZoneCard(number);

      if(!card){
        return;
      }

      card.classList.add(
        "ifc3-zone"
      );

      card.classList.remove(
        "has-infini-picture"
      );

      card.style.setProperty(
        "background",
        "#070707",
        "important"
      );

      card.style.setProperty(
        "background-image",
        "none",
        "important"
      );

      Array.from(
        card.querySelectorAll(
          ".infini-card-upload," +
          "button[data-card-key]," +
          "[aria-label*='อัปโหลดรูป']"
        )
      ).forEach(function(button){
        button.remove();
      });
    });
  }

  let applying = false;

  function apply(){
    if(applying){
      return;
    }

    applying = true;

    try{
      flattenCreative();
      makeZonesPlain();
    }finally{
      applying = false;
    }
  }

  function start(){
    apply();

    let count = 0;

    const timer = setInterval(
      function(){
        count += 1;
        apply();

        if(count >= 30){
          clearInterval(timer);
        }
      },
      250
    );

    let queued = false;

    const observer =
      new MutationObserver(function(){
        if(queued){
          return;
        }

        queued = true;

        setTimeout(function(){
          queued = false;
          apply();
        },80);
      });

    observer.observe(
      document.body,
      {
        childList:true,
        subtree:true
      }
    );
  }

  if(document.readyState === "loading"){
    document.addEventListener(
      "DOMContentLoaded",
      start
    );
  }else{
    start();
  }
})();
</script>
"""


class ForceFlatCreativeMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request,
        call_next,
    ):
        response = await call_next(request)

        content_type = (
            response.headers
            .get("content-type","")
            .lower()
        )

        if "text/html" not in content_type:
            return response

        path = request.url.path

        allowed = (
            path == "/id-home"
            or path.startswith("/id-home/")
            or path == "/id"
            or path.startswith("/id/")
            or path == "/member/id"
            or path.startswith("/member/id/")
        )

        if not allowed:
            return response

        iterator = getattr(
            response,
            "body_iterator",
            None,
        )

        if iterator is None:
            return response

        chunks = []

        async for chunk in iterator:
            chunks.append(chunk)

        raw = b"".join(chunks)

        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            return Response(
                raw,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="text/html",
            )

        if MARKER not in html:
            if "</body>" in html:
                html = html.replace(
                    "</body>",
                    INJECT + "\n</body>",
                    1,
                )
            else:
                html += INJECT

        headers = dict(response.headers)
        headers.pop("content-length",None)
        headers.pop("content-encoding",None)

        return Response(
            html,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html",
        )


def install_force_flat_creative_7000(app):
    marker = (
        "_infini_force_flat_creative_v3"
    )

    if getattr(
        app.state,
        marker,
        False,
    ):
        return

    app.add_middleware(
        ForceFlatCreativeMiddleware
    )

    setattr(
        app.state,
        marker,
        True,
    )
