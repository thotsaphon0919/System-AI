from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


_MARKER = "INFINI_ZONE_LINKS_V1"

_INJECT = r'''
<!-- INFINI_ZONE_LINKS_V1 -->
<style>
  [data-infini-zone-link="1"]{
    cursor:pointer !important;
    touch-action:manipulation !important;
    -webkit-tap-highlight-color:rgba(255,145,0,.18) !important;
  }

  [data-infini-zone-link="1"]:active{
    transform:scale(.975) !important;
    filter:brightness(1.15) !important;
  }

  .infini-zone-enter{
    display:inline-flex;
    align-items:center;
    margin-top:10px;
    padding:6px 10px;
    border:1px solid rgba(255,145,0,.45);
    border-radius:999px;
    color:#ffad46;
    background:rgba(255,145,0,.07);
    font-size:11px;
    font-weight:900;
  }
</style>

<script>
(function(){
  if(window.__INFINI_ZONE_LINKS_V1__) return;
  window.__INFINI_ZONE_LINKS_V1__ = true;

  const ZONES = {
    1: {
      url: "/zone/private",
      subtitle: "Private / ส่วนตัว",
      button: "เข้าโซนส่วนตัว"
    },
    2: {
      url: "/zone/office",
      subtitle: "Office / ออฟฟิต",
      button: "เข้าโซนออฟฟิต"
    },
    3: {
      url: "/zone/shop",
      subtitle: "Shop / ร้านค้า",
      button: "เข้าโซนร้านค้า"
    },
    4: {
      url: "/zone/portfolio",
      subtitle: "Creative / ครีเอทีฟ",
      button: "เข้าโซนครีเอทีฟ"
    }
  };

  function clean(value){
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toUpperCase();
  }

  function findLabel(number){
    const wanted = "ZONE " + number;

    return Array.from(
      document.querySelectorAll("body *")
    ).find(function(el){
      if(el.children.length !== 0) return false;
      return clean(el.textContent) === wanted;
    }) || null;
  }

  function findCard(label){
    if(!label) return null;

    const direct = label.closest(
      "a,button,[role='button'],.zone-card,.zoneCard,.zone,.card,.tile"
    );

    if(direct) return direct;

    let el = label.parentElement;

    while(el && el !== document.body){
      const rect = el.getBoundingClientRect();
      const text = clean(el.textContent);

      if(
        rect.width >= 100 &&
        rect.height >= 80 &&
        rect.height <= 420 &&
        text.length <= 220
      ){
        return el;
      }

      el = el.parentElement;
    }

    return label.parentElement;
  }

  function replaceSubtitle(card, number, value){
    const oldWords = {
      1: ["GALLERY", "PRIVATE", "ส่วนตัว"],
      2: ["SHOP", "OFFICE", "ออฟฟิต"],
      3: ["SERVICE", "SHOP", "ร้านค้า"],
      4: ["FRIEND / FAN", "FRIEND/FAN", "CREATIVE", "ครีเอทีฟ"]
    };

    const leaves = Array.from(
      card.querySelectorAll("*")
    ).filter(function(el){
      return el.children.length === 0;
    });

    const target = leaves.find(function(el){
      const text = clean(el.textContent);
      return oldWords[number].some(function(word){
        return text === clean(word);
      });
    });

    if(target){
      target.textContent = value;
    }
  }

  function connect(number){
    const config = ZONES[number];
    const label = findLabel(number);
    const card = findCard(label);

    if(!card) return false;

    if(card.dataset.infiniZoneLink === "1"){
      return true;
    }

    card.dataset.infiniZoneLink = "1";
    card.setAttribute("role", "link");
    card.setAttribute("tabindex", "0");
    card.setAttribute(
      "aria-label",
      config.button
    );

    if(card.tagName === "A"){
      card.setAttribute("href", config.url);
    }

    replaceSubtitle(
      card,
      number,
      config.subtitle
    );

    if(!card.querySelector(".infini-zone-enter")){
      const badge = document.createElement("div");
      badge.className = "infini-zone-enter";
      badge.textContent = config.button;
      card.appendChild(badge);
    }

    function openZone(event){
      if(
        event &&
        event.type === "keydown" &&
        event.key !== "Enter" &&
        event.key !== " "
      ){
        return;
      }

      if(event){
        event.preventDefault();
        event.stopPropagation();
      }

      location.href = config.url;
    }

    card.addEventListener(
      "click",
      openZone,
      true
    );

    card.addEventListener(
      "keydown",
      openZone,
      true
    );

    return true;
  }

  function install(){
    Object.keys(ZONES).forEach(function(number){
      connect(Number(number));
    });

    setTimeout(function(){
      Object.keys(ZONES).forEach(function(number){
        connect(Number(number));
      });
    }, 700);
  }

  if(document.readyState === "loading"){
    document.addEventListener(
      "DOMContentLoaded",
      install
    );
  }else{
    install();
  }
})();
</script>
'''


class _ZoneLinkMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        content_type = (
            response.headers.get("content-type", "")
            .lower()
        )

        if "text/html" not in content_type:
            return response

        path = request.url.path

        if not (
            path == "/id-home"
            or path.startswith("/id-home/")
            or path == "/id"
            or path.startswith("/id/")
            or path == "/member/id"
            or path.startswith("/member/id/")
        ):
            return response

        body_iterator = getattr(
            response,
            "body_iterator",
            None,
        )

        if body_iterator is None:
            return response

        chunks = []

        async for chunk in body_iterator:
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

        if _MARKER not in html:
            if "</body>" in html:
                html = html.replace(
                    "</body>",
                    _INJECT + "\n</body>",
                    1,
                )
            else:
                html += _INJECT

        headers = dict(response.headers)
        headers.pop("content-length", None)
        headers.pop("content-encoding", None)

        return Response(
            content=html,
            status_code=response.status_code,
            headers=headers,
            media_type="text/html",
        )


def install_zone_link_7000(app):
    marker = "_infini_zone_links_installed"

    if getattr(app.state, marker, False):
        return

    app.add_middleware(_ZoneLinkMiddleware)
    setattr(app.state, marker, True)
