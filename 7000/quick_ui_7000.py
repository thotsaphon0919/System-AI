from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

MARKER = "INFINI_QUICK_UI_V1"

STYLE = r"""
<style>
.inf-ai-tools{display:grid!important;grid-template-columns:1fr 1fr;gap:9px;width:100%}
.inf-ai-link{display:flex;align-items:center;justify-content:center;min-height:52px;padding:10px;border:1px solid rgba(255,145,0,.58);border-radius:15px;background:linear-gradient(135deg,rgba(255,174,30,.18),rgba(255,105,0,.08));color:#ffd29b;text-decoration:none;font-weight:950}
.inf-friend-request{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 14px;padding:14px;border:1px solid rgba(255,145,0,.42);border-radius:18px;background:linear-gradient(135deg,rgba(255,145,0,.12),rgba(8,4,2,.92))}
.inf-friend-request b{display:block;color:#ffad48}.inf-friend-request small{display:block;margin-top:3px;color:#b99d85}
.inf-friend-request a{padding:10px 13px;border:1px solid rgba(255,177,64,.55);border-radius:13px;background:#080402;color:#ffd29b;text-decoration:none;font-weight:900}
.inf-cr-nav{position:sticky;top:0;z-index:99990;display:flex;align-items:center;justify-content:space-between;gap:10px;margin:-24px -16px 16px;padding:12px 15px;border-bottom:1px solid rgba(255,145,0,.42);background:rgba(3,2,1,.94)}
.inf-cr-nav a{padding:10px 13px;border:1px solid rgba(255,145,0,.52);border-radius:14px;background:#080402;color:#ffd29b;text-decoration:none;font-weight:950}
.inf-cr-nav strong{color:#ff9d2d}
.inf-easy-up{position:absolute!important;top:10px!important;right:10px!important;z-index:9998!important;min-width:42px!important;height:42px!important;display:flex!important;align-items:center!important;justify-content:center!important;padding:0 11px!important;border:1px solid rgba(255,181,69,.72)!important;border-radius:999px!important;background:rgba(0,0,0,.84)!important;color:#ffd18a!important;font:950 14px system-ui!important;box-shadow:0 8px 22px rgba(0,0,0,.5)!important}
.inf-easy-up:active{transform:scale(.94)!important;background:#ff9a18!important;color:#170700!important}
.inf-toast{position:fixed;top:12px;left:50%;z-index:999999;transform:translateX(-50%);display:none;max-width:calc(100% - 28px);padding:10px 14px;border:1px solid rgba(255,145,0,.55);border-radius:999px;background:#170a03;color:#ffd398;text-align:center;font:850 13px system-ui}
</style>
"""

ID_SCRIPT = r"""
<script>
(function(){
 if(window.__INF_AI_ENTRY__)return;window.__INF_AI_ENTRY__=1;
 const clean=v=>String(v||"").replace(/\s+/g," ").trim();
 function run(){
  if(document.getElementById("infAiShop"))return true;
  const leaf=[...document.querySelectorAll("body *")].find(e=>!e.children.length&&clean(e.textContent)==="เพิ่มรูป");
  if(!leaf)return false;
  const btn=leaf.closest("button,a,label,[role='button']")||leaf;
  if(!btn.parentElement)return false;
  const wrap=document.createElement("div");wrap.className="inf-ai-tools";
  const ai=document.createElement("a");ai.id="infAiShop";ai.className="inf-ai-link";ai.href="/ai-layout-lab";ai.textContent="✦ AI จัดร้าน";
  btn.parentElement.insertBefore(wrap,btn);wrap.appendChild(btn);wrap.appendChild(ai);return true;
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>{let n=0,t=setInterval(()=>{n++;if(run()||n>20)clearInterval(t)},300)});
 else run();
})();
</script>
"""

FRIEND_SCRIPT = r"""
<script>
(function(){
 if(window.__INF_FRIEND_REQ__)return;window.__INF_FRIEND_REQ__=1;
 function run(){
  if(document.getElementById("infFriendRequest"))return;
  const cover=document.querySelector(".cover"),layout=document.querySelector(".layout"),a=cover||layout;
  if(!a||!a.parentElement)return;
  const bar=document.createElement("div");bar.id="infFriendRequest";bar.className="inf-friend-request";
  bar.innerHTML='<div><b>คำขอเป็นเพื่อน</b><small>รับหรือปฏิเสธคำขอจาก INFINI ID</small></div><a href="/friend-requests">เปิด</a>';
  cover?cover.insertAdjacentElement("afterend",bar):layout.parentElement.insertBefore(bar,layout);
 }
 document.readyState==="loading"?document.addEventListener("DOMContentLoaded",run):run();
})();
</script>
"""

CREATIVE_SCRIPT = r"""
<script>
(function(){
 if(window.__INF_CR_EASY__)return;window.__INF_CR_EASY__=1;
 let pages=[];
 function toast(m){let x=document.getElementById("infToast");if(!x){x=document.createElement("div");x.id="infToast";x.className="inf-toast";document.body.appendChild(x)}x.textContent=m;x.style.display="block";clearTimeout(x.t);x.t=setTimeout(()=>x.style.display="none",1500)}
 function stop(e){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()}
 function upload(url){const i=document.createElement("input");i.type="file";i.accept="image/*,video/*";i.hidden=true;document.body.appendChild(i);i.onchange=async()=>{const f=i.files&&i.files[0];if(!f){i.remove();return}const d=new FormData();d.append("file",f);toast("กำลังอัปโหลด...");try{const r=await fetch(url,{method:"POST",body:d});if(!r.ok)throw new Error(await r.text());toast("อัปโหลดแล้ว");setTimeout(()=>location.reload(),350)}catch(e){console.error(e);toast("อัปโหลดไม่สำเร็จ")}setTimeout(()=>i.remove(),500)};i.click()}
 function button(url,label,cls){const b=document.createElement("button");b.type="button";b.className="inf-easy-up "+cls;b.textContent=label;b.addEventListener("pointerdown",stop,true);b.addEventListener("click",e=>{stop(e);upload(url)},true);return b}
 function nav(){if(document.getElementById("infCrNav"))return;const app=document.querySelector(".app")||document.body,n=document.createElement("div");n.id="infCrNav";n.className="inf-cr-nav";n.innerHTML='<a href="/id-home">← กลับหน้า ID</a><strong>CREATIVE ROOM</strong>';app.insertBefore(n,app.firstChild)}
 function hero(){const h=document.getElementById("heroBox");if(!h)return false;const p=h.closest(".hero")||h.parentElement||h;if(p.querySelector(".inf-easy-up.hero"))return true;p.style.position="relative";p.appendChild(button("/api/simple/top/upload","⇧ รูป","hero"));return true}
 function cards(){const cs=[...document.querySelectorAll("#grid .card")];if(!cs.length||!pages.length)return 0;cs.forEach((c,k)=>{const p=pages[k];if(!p||!p.id||c.querySelector(".inf-easy-up.card"))return;c.style.position="relative";c.appendChild(button("/api/pages/"+encodeURIComponent(p.id)+"/upload","⇧","card"))});return cs.length}
 async function start(){nav();try{const r=await fetch("/api/state",{cache:"no-store"});if(r.ok)pages=(await r.json()).pages||[]}catch(e){}hero();cards();let n=0,t=setInterval(()=>{n++;hero();cards();if(n>25)clearInterval(t)},300)}
 document.readyState==="loading"?document.addEventListener("DOMContentLoaded",start):start();
})();
</script>
"""

class QuickUiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "text/html" not in response.headers.get("content-type","").lower():
            return response
        path = request.url.path
        if path == "/":
            inject = STYLE + CREATIVE_SCRIPT
        elif path == "/friend-chat":
            inject = STYLE + FRIEND_SCRIPT
        elif path == "/id-home" or path.startswith("/id-home/") or path == "/id" or path.startswith("/id/"):
            inject = STYLE + ID_SCRIPT
        else:
            return response
        iterator = getattr(response,"body_iterator",None)
        if iterator is None:
            return response
        chunks=[]
        async for chunk in iterator:
            chunks.append(chunk)
        raw=b"".join(chunks)
        try:
            html=raw.decode("utf-8")
        except UnicodeDecodeError:
            return Response(raw,status_code=response.status_code,headers=dict(response.headers),media_type="text/html")
        if MARKER not in html:
            inject="<!-- "+MARKER+" -->"+inject
            html=html.replace("</body>",inject+"\n</body>",1) if "</body>" in html else html+inject
        headers=dict(response.headers);headers.pop("content-length",None);headers.pop("content-encoding",None)
        return Response(html,status_code=response.status_code,headers=headers,media_type="text/html")

def install_quick_ui_7000(app):
    paths={getattr(r,"path",None) for r in app.routes}
    if "/friend-requests" not in paths:
        @app.get("/friend-requests",response_class=HTMLResponse)
        def friend_requests_placeholder():
            return HTMLResponse(r"""<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>คำขอเป็นเพื่อน</title><style>*{box-sizing:border-box}body{margin:0;min-height:100vh;padding:16px;background:radial-gradient(circle at top right,#321500,#080402 45%,#000);color:#fff;font-family:system-ui}.wrap{max-width:680px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}h1{margin:0;color:#ff9d2d;font-size:23px}.back{padding:10px 14px;border:1px solid rgba(255,145,0,.5);border-radius:14px;background:#080402;color:#ffd29b;text-decoration:none;font-weight:900}.panel{padding:22px;border:1px solid rgba(255,145,0,.38);border-radius:22px;background:rgba(12,6,3,.84)}.empty{min-height:230px;display:grid;place-items:center;color:#b99b80;text-align:center}.note{margin-top:14px;padding:12px;border:1px dashed rgba(255,145,0,.3);border-radius:14px;color:#a98e77;font-size:12px;line-height:1.5}</style></head><body><div class="wrap"><div class="top"><h1>คำขอเป็นเพื่อน</h1><a class="back" href="/friend-chat">กลับ</a></div><section class="panel"><div class="empty">ยังไม่มีคำขอเป็นเพื่อน</div></section><div class="note">วางทางเข้าไว้ก่อน ระบบรับเพื่อนข้ามบัญชีจริงจะทำงานเมื่อเชื่อมระบบสมาชิกของแต่ละ INFINI ID</div></div></body></html>""")
    marker="_infini_quick_ui_v1"
    if getattr(app.state,marker,False):
        return
    app.add_middleware(QuickUiMiddleware)
    setattr(app.state,marker,True)
