from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


MARKER = "INFINI_CREATIVE_FLAT_CARD_V1"

INJECT = r"""
<!-- INFINI_CREATIVE_FLAT_CARD_V1 -->
<style>
  /* CREATIVE ROOM: ตัวหนังสือวางบนรูปโดยตรง */
  .infini-creative-flat{
    position:relative !important;
    overflow:hidden !important;
    min-height:300px !important;
    background-position:center !important;
    background-size:cover !important;
    background-repeat:no-repeat !important;
  }

  .infini-creative-flat::before{
    content:"" !important;
    position:absolute !important;
    inset:0 !important;
    z-index:0 !important;
    pointer-events:none !important;
    background:
      linear-gradient(
        100deg,
        rgba(0,0,0,.72) 0%,
        rgba(0,0,0,.45) 58%,
        rgba(0,0,0,.23) 100%
      ) !important;
  }

  .infini-creative-flat > *{
    position:relative !important;
    z-index:2 !important;
  }

  .infini-creative-flat-inner,
  .infini-creative-flat-inner::before,
  .infini-creative-flat-inner::after{
    background-color:transparent !important;
    background-image:none !important;
    border-color:transparent !important;
    box-shadow:none !important;
  }

  .infini-creative-flat-inner{
    border:0 !important;
    border-radius:0 !important;
  }

  .infini-creative-flat h1,
  .infini-creative-flat h2,
  .infini-creative-flat h3,
  .infini-creative-flat p,
  .infini-creative-flat span{
    text-shadow:
      0 3px 10px rgba(0,0,0,.98),
      0 0 4px rgba(0,0,0,.95) !important;
  }

  /* ZONE 1–4: กลับเป็นช่องเล็กธรรมดา ไม่ใช้รูป */
  .infini-zone-plain{
    background-image:none !important;
    background-color:#070707 !important;
  }

  .infini-zone-plain::before{
    display:none !important;
  }

  .infini-zone-plain .infini-card-upload{
    display:none !important;
  }
</style>

<script>
(function(){
  if(window.__INFINI_CREATIVE_FLAT_CARD_V1__){
    return;
  }

  window.__INFINI_CREATIVE_FLAT_CARD_V1__ = true;

  function clean(value){
    return String(value || "")
      .replace(/\s+/g," ")
      .trim()
      .toUpperCase();
  }

  function findCreativeCard(){
    return (
      document.querySelector(
        '[data-infini-picture-key="creative"]'
      )
      ||
      Array.from(
        document.querySelectorAll(
          ".infini-picture-card"
        )
      ).find(function(card){
        return clean(card.textContent)
          .includes("CREATIVE ROOM");
      })
      ||
      null
    );
  }

  function flattenCreative(){
    const card = findCreativeCard();

    if(!card){
      return false;
    }

    card.classList.add(
      "infini-creative-flat"
    );

    const label =
      Array.from(
        card.querySelectorAll("*")
      ).find(function(element){
        return (
          element.children.length === 0 &&
          clean(element.textContent) ===
            "CREATIVE ROOM"
        );
      });

    if(!label){
      return true;
    }

    const cardRect =
      card.getBoundingClientRect();

    let node = label.parentElement;

    while(
      node &&
      node !== card
    ){
      const rect =
        node.getBoundingClientRect();

      const widthRatio =
        cardRect.width
          ? rect.width / cardRect.width
          : 0;

      const heightRatio =
        cardRect.height
          ? rect.height / cardRect.height
          : 0;

      if(
        widthRatio >= .65 &&
        heightRatio >= .32
      ){
        node.classList.add(
          "infini-creative-flat-inner"
        );
      }

      node = node.parentElement;
    }

    return true;
  }

  function makeZonesPlain(){
    ["zone1","zone2","zone3","zone4"]
      .forEach(function(key){
        const card =
          document.querySelector(
            '[data-infini-picture-key="' +
            key +
            '"]'
          );

        if(!card){
          return;
        }

        card.classList.add(
          "infini-zone-plain"
        );

        card.classList.remove(
          "has-infini-picture"
        );

        card.style.setProperty(
          "background-image",
          "none",
          "important"
        );

        const upload =
          card.querySelector(
            ".infini-card-upload"
          );

        if(upload){
          upload.style.setProperty(
            "display",
            "none",
            "important"
          );
        }
      });
  }

  function apply(){
    flattenCreative();
    makeZonesPlain();
  }

  function start(){
    apply();

    let count = 0;

    const timer = setInterval(
      function(){
        count += 1;
        apply();

        if(count >= 20){
          clearInterval(timer);
        }
      },
      300
    );

    const observer =
      new MutationObserver(function(){
        apply();
      });

    observer.observe(
      document.body,
      {
        childList:true,
        subtree:true,
        attributes:true,
        attributeFilter:[
          "class",
          "style"
        ]
      }
    );

    setTimeout(function(){
      observer.disconnect();
    },10000);
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


class CreativeFlatCardMiddleware(
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
        headers.pop(
            "content-length",
            None,
        )
        headers.pop(
            "content-encoding",
            None,
        )

        return Response(
            html,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html",
        )


def install_creative_flat_card_7000(app):
    marker = (
        "_infini_creative_flat_card_installed"
    )

    if getattr(
        app.state,
        marker,
        False,
    ):
        return

    app.add_middleware(
        CreativeFlatCardMiddleware
    )

    setattr(
        app.state,
        marker,
        True,
    )
