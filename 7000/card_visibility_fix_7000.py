from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


MARKER = "INFINI_CARD_VISIBILITY_FIX_STANDALONE_V1"

INJECT = r"""
<!-- INFINI_CARD_VISIBILITY_FIX_STANDALONE_V1 -->
<style>
  /* ลดฟิล์มดำบนรูปให้ใกล้เคียง FRIEND / CHAT */
  .infini-picture-card.has-infini-picture::before{
    background:
      linear-gradient(
        105deg,
        rgba(0,0,0,.48) 0%,
        rgba(0,0,0,.34) 58%,
        rgba(0,0,0,.24) 100%
      ) !important;
  }

  .infini-picture-card.has-infini-picture{
    background-position:center !important;
    background-size:cover !important;
    background-repeat:no-repeat !important;
  }

  /* ชั้นใหญ่ด้านในที่บังรูป */
  .infini-card-unblock{
    background-color:rgba(0,0,0,.14) !important;
    background-image:none !important;
    box-shadow:none !important;
  }

  .infini-card-unblock::before,
  .infini-card-unblock::after{
    background-color:transparent !important;
    background-image:none !important;
    box-shadow:none !important;
  }

  /* คงตัวหนังสือให้อ่านชัด */
  .infini-picture-card.has-infini-picture h1,
  .infini-picture-card.has-infini-picture h2,
  .infini-picture-card.has-infini-picture h3,
  .infini-picture-card.has-infini-picture p,
  .infini-picture-card.has-infini-picture span{
    text-shadow:
      0 2px 8px rgba(0,0,0,.98),
      0 0 3px rgba(0,0,0,.95) !important;
  }
</style>

<script>
(function(){
  if(window.__INFINI_CARD_VISIBILITY_FIX_STANDALONE_V1__){
    return;
  }

  window.__INFINI_CARD_VISIBILITY_FIX_STANDALONE_V1__ = true;

  function shouldSkip(element){
    if(!element || !element.closest){
      return true;
    }

    if(
      element.closest(
        ".infini-card-upload," +
        ".infini-card-file," +
        "#ifc-upload," +
        "#ifc-file"
      )
    ){
      return true;
    }

    return [
      "BUTTON",
      "INPUT",
      "IMG",
      "VIDEO",
      "A"
    ].includes(element.tagName);
  }

  function unblock(card){
    const cardRect =
      card.getBoundingClientRect();

    if(
      cardRect.width < 100 ||
      cardRect.height < 80
    ){
      return;
    }

    Array.from(
      card.querySelectorAll("*")
    ).forEach(function(element){
      if(shouldSkip(element)){
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
        rect.width / cardRect.width;

      const heightRatio =
        rect.height / cardRect.height;

      /*
        เลือกเฉพาะชั้นใหญ่ที่ปิดพื้นที่รูป
        ไม่แตะข้อความและปุ่มเล็ก
      */
      if(
        widthRatio >= 0.68 &&
        heightRatio >= 0.42
      ){
        element.classList.add(
          "infini-card-unblock"
        );
      }
    });
  }

  function apply(){
    const cards =
      document.querySelectorAll(
        ".infini-picture-card.has-infini-picture"
      );

    cards.forEach(unblock);

    return cards.length;
  }

  function start(){
    apply();

    let count = 0;

    const timer = setInterval(
      function(){
        count += 1;
        apply();

        if(count >= 18){
          clearInterval(timer);
        }
      },
      300
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


class CardVisibilityFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        content_type = (
            response.headers
            .get("content-type", "")
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
        headers.pop("content-length", None)
        headers.pop("content-encoding", None)

        return Response(
            html,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html",
        )


def install_card_visibility_fix_7000(app):
    marker = (
        "_infini_card_visibility_fix_installed"
    )

    if getattr(
        app.state,
        marker,
        False,
    ):
        return

    app.add_middleware(
        CardVisibilityFixMiddleware
    )

    setattr(
        app.state,
        marker,
        True,
    )
