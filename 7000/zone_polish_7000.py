from pathlib import Path
import mimetypes
import shutil
import time
import uuid

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


MARKER = "INFINI_ZONE_POLISH_V2"
BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data" / "zone_polish_7000"
COVER_DIR = DATA_DIR / "zone_hub_cover"


def _ensure_dirs():
    COVER_DIR.mkdir(parents=True, exist_ok=True)


def _safe_ext(filename: str, content_type: str = "") -> str:
    ext = Path(filename or "").suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mov"}
    if ext in allowed:
        return ext
    guessed = mimetypes.guess_extension(content_type or "") or ""
    return guessed if guessed in allowed else ".jpg"


def _media_kind(path: Path) -> str:
    return "video" if path.suffix.lower() in {".mp4", ".webm", ".mov"} else "image"


def _current_cover(cover_dir: Path):
    cover_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (p for p in cover_dir.iterdir() if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


_INJECT = r'''
<!-- INFINI_ZONE_POLISH_V2 -->
<style id="infiniZonePolishV2">
/* ===== หน้าศูนย์เลือกโซน ===== */
body.infini-zone-hub-v1 .wrap{
  width:min(100%,820px) !important;
  max-width:820px !important;
  padding:20px 16px 112px !important;
}
body.infini-zone-hub-v1 .topbar{margin-bottom:18px !important}
body.infini-zone-hub-v1 .panel.hero{
  position:relative !important;
  min-height:230px !important;
  padding:30px 250px 28px 28px !important;
  display:flex !important;
  flex-direction:column !important;
  justify-content:center !important;
  overflow:hidden !important;
  border:1px solid rgba(255,132,25,.42) !important;
  border-radius:26px !important;
  background:#070402 !important;
  isolation:isolate !important;
}
body.infini-zone-hub-v1 .panel.hero::before{
  content:"";
  position:absolute;
  inset:0;
  z-index:-1;
  background:linear-gradient(90deg,rgba(0,0,0,.97) 0%,rgba(0,0,0,.82) 52%,rgba(0,0,0,.18) 100%) !important;
  pointer-events:none;
}
body.infini-zone-hub-v1 .panel.hero .zh-cover{
  position:absolute;
  inset:0;
  z-index:-2;
  width:100%;
  height:100%;
  object-fit:cover;
  object-position:center;
  display:block;
}
body.infini-zone-hub-v1 .panel.hero h1{
  position:relative;
  z-index:2;
  margin:0 0 12px !important;
  color:#ff8124 !important;
  font-size:clamp(38px,7vw,58px) !important;
  line-height:.94 !important;
  letter-spacing:-1.4px !important;
  white-space:pre-line !important;
  text-shadow:0 3px 20px #000 !important;
}
body.infini-zone-hub-v1 .panel.hero p{
  position:relative;
  z-index:2;
  max-width:470px !important;
  margin:0 !important;
  color:#eee !important;
  font-size:clamp(15px,3vw,19px) !important;
  line-height:1.52 !important;
  text-shadow:0 2px 14px #000 !important;
}
.zh-more{
  position:absolute;
  top:14px;
  right:14px;
  z-index:8;
  width:46px;
  height:46px;
  display:grid;
  place-items:center;
  padding:0;
  border:1px solid rgba(255,137,37,.7);
  border-radius:999px;
  background:rgba(4,3,2,.78);
  color:#ff9a3b;
  font-size:27px;
  line-height:1;
  font-weight:1000;
  box-shadow:0 7px 24px rgba(0,0,0,.42);
}
.zh-more:active{transform:scale(.93)}
body.infini-zone-hub-v1 .panel:not(.hero){
  padding:20px !important;
  border-radius:27px !important;
}
body.infini-zone-hub-v1 .section-title{
  margin:0 0 18px !important;
  text-align:center !important;
  font-size:clamp(25px,5vw,34px) !important;
}
body.infini-zone-hub-v1 .grid{
  display:grid !important;
  grid-template-columns:repeat(2,minmax(0,1fr)) !important;
  gap:16px !important;
}
body.infini-zone-hub-v1 .zone-card{
  min-width:0 !important;
  min-height:430px !important;
  height:auto !important;
  padding:16px !important;
  display:flex !important;
  flex-direction:column !important;
  border:1px solid rgba(255,128,28,.43) !important;
  border-radius:24px !important;
  background:radial-gradient(circle at 50% 38%,#211005 0,#080402 44%,#020202 76%) !important;
  box-shadow:0 0 20px rgba(255,104,0,.08) !important;
  overflow:hidden !important;
}
body.infini-zone-hub-v1 .zone-top{
  display:grid !important;
  grid-template-columns:56px minmax(0,1fr) !important;
  align-items:start !important;
  gap:12px !important;
}
body.infini-zone-hub-v1 .zone-no{
  width:56px !important;
  height:56px !important;
  min-width:56px !important;
  border-radius:15px !important;
  font-size:26px !important;
}
body.infini-zone-hub-v1 .zone-head{min-width:0 !important;padding-top:1px !important}
body.infini-zone-hub-v1 .zone-en{
  font-size:12px !important;
  line-height:1.2 !important;
  white-space:nowrap !important;
  overflow:hidden !important;
  text-overflow:ellipsis !important;
}
body.infini-zone-hub-v1 .zone-name{
  margin-top:5px !important;
  color:#ff8a31 !important;
  font-size:clamp(18px,3.5vw,25px) !important;
  line-height:1.16 !important;
  font-weight:950 !important;
  display:-webkit-box !important;
  -webkit-line-clamp:2 !important;
  -webkit-box-orient:vertical !important;
  overflow:hidden !important;
}
body.infini-zone-hub-v1 .zone-logo{
  flex:0 0 132px !important;
  height:132px !important;
  min-height:132px !important;
}
body.infini-zone-hub-v1 .zone-logo svg{
  width:112px !important;
  height:112px !important;
}
body.infini-zone-hub-v1 .zone-desc{
  flex:1 1 auto !important;
  min-height:112px !important;
  margin-top:2px !important;
  color:#d3d3d3 !important;
  font-size:clamp(13px,2.7vw,16px) !important;
  line-height:1.5 !important;
  overflow:hidden !important;
  display:-webkit-box !important;
  -webkit-line-clamp:5 !important;
  -webkit-box-orient:vertical !important;
}
body.infini-zone-hub-v1 .zone-enter{
  flex:0 0 48px !important;
  min-height:48px !important;
  margin-top:14px !important;
  padding:0 14px !important;
  font-size:13px !important;
}
body.infini-zone-hub-v1 .infini-zone-enter{display:none !important}

/* ===== รูปหัวข้อของหน้าโซน: เปลี่ยนผ่านปุ่มสามจุด ===== */
body.infini-zone-detail-v1 .hero{position:relative !important}
body.infini-zone-detail-v1 .az-stats{
  grid-template-columns:repeat(3,minmax(0,1fr)) !important;
}
body.infini-zone-detail-v1 .az-hero-upload{
  position:absolute !important;
  top:12px !important;
  right:12px !important;
  z-index:30 !important;
  width:46px !important;
  height:46px !important;
  min-width:46px !important;
  min-height:46px !important;
  padding:0 !important;
  display:grid !important;
  place-items:center !important;
  border:1px solid rgba(255,134,31,.72) !important;
  border-radius:999px !important;
  background:rgba(5,3,2,.78) !important;
  color:#ff9a3b !important;
  box-shadow:0 7px 24px rgba(0,0,0,.42) !important;
  overflow:hidden !important;
}
body.infini-zone-detail-v1 .az-hero-upload b{
  display:none !important;
}
body.infini-zone-detail-v1 .az-hero-upload span{
  width:100% !important;
  height:100% !important;
  display:grid !important;
  place-items:center !important;
  font-size:0 !important;
  line-height:1 !important;
}
body.infini-zone-detail-v1 .az-hero-upload span::before{
  content:"⋮";
  color:#ff9a3b;
  font-size:28px;
  font-weight:1000;
  line-height:1;
}
body.infini-zone-detail-v1 .az-upload-panel{display:none !important}

.infini-zone-toast{
  position:fixed;
  top:13px;
  left:50%;
  transform:translateX(-50%);
  z-index:999999;
  max-width:calc(100% - 28px);
  padding:10px 14px;
  border:1px solid rgba(255,139,42,.58);
  border-radius:999px;
  background:#160a04;
  color:#fff2e3;
  font:800 13px system-ui,-apple-system,"Segoe UI",sans-serif;
  box-shadow:0 10px 30px rgba(0,0,0,.45);
}

@media(max-width:560px){
  body.infini-zone-hub-v1 .wrap{padding:14px 12px 108px !important}
  body.infini-zone-hub-v1 .panel.hero{
    min-height:210px !important;
    padding:24px 92px 22px 20px !important;
    border-radius:23px !important;
  }
  body.infini-zone-hub-v1 .panel.hero::before{
    background:linear-gradient(90deg,rgba(0,0,0,.96) 0%,rgba(0,0,0,.78) 65%,rgba(0,0,0,.2) 100%) !important;
  }
  body.infini-zone-hub-v1 .panel.hero h1{font-size:clamp(34px,10vw,48px) !important}
  body.infini-zone-hub-v1 .panel.hero p{
    max-width:390px !important;
    font-size:14px !important;
    display:-webkit-box !important;
    -webkit-line-clamp:3 !important;
    -webkit-box-orient:vertical !important;
    overflow:hidden !important;
  }
  body.infini-zone-hub-v1 .panel:not(.hero){padding:15px !important}
  body.infini-zone-hub-v1 .grid{gap:12px !important}
  body.infini-zone-hub-v1 .zone-card{
    min-height:390px !important;
    padding:13px !important;
    border-radius:21px !important;
  }
  body.infini-zone-hub-v1 .zone-top{
    grid-template-columns:48px minmax(0,1fr) !important;
    gap:9px !important;
  }
  body.infini-zone-hub-v1 .zone-no{
    width:48px !important;
    height:48px !important;
    min-width:48px !important;
    font-size:22px !important;
  }
  body.infini-zone-hub-v1 .zone-en{font-size:10px !important}
  body.infini-zone-hub-v1 .zone-name{font-size:clamp(16px,4.6vw,21px) !important}
  body.infini-zone-hub-v1 .zone-logo{
    flex-basis:112px !important;
    height:112px !important;
    min-height:112px !important;
  }
  body.infini-zone-hub-v1 .zone-logo svg{width:94px !important;height:94px !important}
  body.infini-zone-hub-v1 .zone-desc{
    min-height:108px !important;
    font-size:13px !important;
    -webkit-line-clamp:5 !important;
  }
  body.infini-zone-hub-v1 .zone-enter{
    min-height:45px !important;
    flex-basis:45px !important;
    padding:0 10px !important;
    font-size:11.5px !important;
  }
  body.infini-zone-hub-v1 .zone-enter b{font-size:24px !important}
}
</style>
<script id="infiniZonePolishScriptV2">
(function(){
  if(window.__INFINI_ZONE_POLISH_V2__) return;
  window.__INFINI_ZONE_POLISH_V2__=true;

  const path=location.pathname.replace(/\/+$/,"") || "/";

  function toast(message){
    let el=document.querySelector('.infini-zone-toast');
    if(!el){el=document.createElement('div');el.className='infini-zone-toast';document.body.appendChild(el)}
    el.textContent=message;el.hidden=false;
    clearTimeout(el._timer);el._timer=setTimeout(()=>{el.hidden=true},1500);
  }

  function chooseFile(accept,handler){
    const input=document.createElement('input');
    input.type='file';input.accept=accept;input.hidden=true;
    document.body.appendChild(input);
    input.addEventListener('change',async()=>{
      const file=input.files&&input.files[0];
      try{if(file)await handler(file)}finally{input.remove()}
    },{once:true});
    input.click();
  }

  async function installHub(){
    document.body.classList.add('infini-zone-hub-v1');
    const hero=document.querySelector('.panel.hero');
    if(!hero)return;

    async function applyCover(){
      try{
        const data=await fetch('/api/zone-hub-cover?t='+Date.now(),{cache:'no-store'}).then(r=>r.json());
        hero.querySelectorAll(':scope > .zh-cover').forEach(x=>x.remove());
        if(!data.url)return;
        let media;
        if(data.type==='video'){
          media=document.createElement('video');media.autoplay=true;media.loop=true;media.muted=true;media.playsInline=true;
        }else media=document.createElement('img');
        media.className='zh-cover';media.src=data.url+'?t='+Date.now();
        hero.insertBefore(media,hero.firstChild);
      }catch(err){console.error(err)}
    }

    if(!hero.querySelector('.zh-more')){
      const button=document.createElement('button');
      button.type='button';button.className='zh-more';button.textContent='⋮';
      button.setAttribute('aria-label','เปลี่ยนรูป CREATIVE ROOM');
      button.addEventListener('click',e=>{
        e.preventDefault();e.stopPropagation();
        chooseFile('image/*,video/*',async file=>{
          const fd=new FormData();fd.append('file',file);
          toast('กำลังอัปโหลด...');
          const res=await fetch('/api/zone-hub-cover/upload',{method:'POST',body:fd});
          if(!res.ok){toast('อัปโหลดไม่สำเร็จ');return}
          await applyCover();toast('เปลี่ยนรูปด้านบนแล้ว');
        });
      });
      hero.appendChild(button);
    }
    await applyCover();
  }

  function zoneKeyFromPath(){
    const m=path.match(/^\/zone\/(private|office|shop)$/);
    return m?m[1]:'';
  }

  function installZoneDetail(){
    const zone=zoneKeyFromPath();
    if(!zone)return;
    document.body.classList.add('infini-zone-detail-v1');

    function moveButton(){
      const hero=document.querySelector('.hero');
      const button=document.querySelector('.az-hero-upload');
      if(!hero||!button)return false;
      if(button.parentElement!==hero)hero.appendChild(button);
      button.setAttribute('aria-label','เปลี่ยนรูปหัวข้อ');
      if(button.dataset.polishBound!=='1'){
        button.dataset.polishBound='1';
        button.addEventListener('click',e=>{
          e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
          chooseFile('image/*',async file=>{
            const fd=new FormData();fd.append('file',file);
            toast('กำลังอัปโหลด...');
            const res=await fetch('/zone-auto/'+zone+'/header-upload',{method:'POST',body:fd,redirect:'follow'});
            if(!res.ok){toast('อัปโหลดไม่สำเร็จ');return}
            toast('เปลี่ยนรูปหัวข้อแล้ว');setTimeout(()=>location.reload(),350);
          });
        },true);
      }
      return true;
    }

    if(!moveButton()){
      const observer=new MutationObserver(()=>{if(moveButton())observer.disconnect()});
      observer.observe(document.documentElement,{childList:true,subtree:true});
      setTimeout(()=>{moveButton();observer.disconnect()},1800);
    }
  }

  if(path==='/zone-hub')installHub();
  else installZoneDetail();
})();
</script>
'''


class _ZonePolishMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path.rstrip("/") or "/"
        if path not in {"/zone-hub", "/zone/private", "/zone/office", "/zone/shop"}:
            return response

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            return response

        body_iterator = getattr(response, "body_iterator", None)
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

        # Apply the page class on the server so layout CSS works even before JavaScript runs.
        page_class = "infini-zone-hub-v1" if path == "/zone-hub" else "infini-zone-detail-v1"
        if page_class not in html:
            if "<body class=\"" in html:
                html = html.replace("<body class=\"", f"<body class=\"{page_class} ", 1)
            elif "<body>" in html:
                html = html.replace("<body>", f"<body class=\"{page_class}\">", 1)

        if MARKER not in html:
            if "</body>" in html:
                html = html.replace("</body>", _INJECT + "\n</body>", 1)
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


def install_zone_polish_7000(app):
    marker = "_infini_zone_polish_v2_installed"
    if getattr(app.state, marker, False):
        return

    _ensure_dirs()

    def _uid(request):
        try:
            from id_entry_7000 import _current_user_id
            return _current_user_id(request)
        except Exception:
            return None

    def _safe_uid(uid: str) -> str:
        import re as _re
        return _re.sub(r"[^A-Za-z0-9_-]+", "_", str(uid or ""))[:100] or "guest"

    def _user_cover_dir(uid: str) -> Path:
        # CRITICAL FIX: previously ALL users shared one single COVER_DIR —
        # uploading a zone hub cover as any user replaced it for every
        # other user on the server. Each user now gets their own folder.
        p = COVER_DIR / _safe_uid(uid)
        p.mkdir(parents=True, exist_ok=True)
        return p

    from fastapi import Request

    @app.get("/api/zone-hub-cover")
    def get_zone_hub_cover(request: Request):
        uid = _uid(request)
        if not uid:
            return JSONResponse({"url": "", "type": ""}, status_code=401)
        cover = _current_cover(_user_cover_dir(uid))
        if not cover:
            return JSONResponse({"url": "", "type": ""})
        return JSONResponse({
            "url": f"/zone-hub-cover/{cover.name}",
            "type": _media_kind(cover),
        })

    @app.post("/api/zone-hub-cover/upload")
    async def upload_zone_hub_cover(request: Request, file: UploadFile = File(...)):
        uid = _uid(request)
        if not uid:
            raise HTTPException(401, "กรุณาเข้าสู่ระบบ")
        user_dir = _user_cover_dir(uid)
        raw = await file.read()
        if not raw:
            raise HTTPException(400, "empty file")
        if len(raw) > 25 * 1024 * 1024:
            raise HTTPException(413, "file too large")

        ext = _safe_ext(file.filename or "", file.content_type or "")
        stored_bytes, stored_ext = raw, ext
        try:
            from image_optimize_7000 import is_optimizable_image, optimize_image_bytes
            if is_optimizable_image(file.filename or f"x{ext}"):
                stored_bytes, stored_ext, _changed = optimize_image_bytes(raw, file.filename or f"x{ext}")
        except Exception:
            pass

        for old in user_dir.iterdir():
            if old.is_file():
                try:
                    old.unlink()
                except Exception:
                    pass

        name = f"cover_{int(time.time())}_{uuid.uuid4().hex[:8]}{stored_ext}"
        target = user_dir / name
        target.write_bytes(stored_bytes)
        return JSONResponse({
            "ok": True,
            "url": f"/zone-hub-cover/{name}",
            "type": _media_kind(target),
        })

    @app.get("/zone-hub-cover/{name}")
    def zone_hub_cover_file(request: Request, name: str):
        uid = _uid(request)
        if not uid:
            raise HTTPException(404, "file not found")
        safe_name = Path(name).name
        target = _user_cover_dir(uid) / safe_name
        if not target.exists() or not target.is_file():
            raise HTTPException(404, "file not found")
        return FileResponse(target, headers={"Cache-Control": "no-store, max-age=0"})

    app.add_middleware(_ZonePolishMiddleware)
    setattr(app.state, marker, True)
