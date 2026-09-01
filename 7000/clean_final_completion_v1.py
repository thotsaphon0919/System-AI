from pathlib import Path
from datetime import datetime, timezone
import json, os, re, secrets, html
from urllib.parse import quote
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from itsdangerous import URLSafeSerializer

BASE=Path(__file__).resolve().parent
DATA=BASE/"data"; DATA.mkdir(parents=True,exist_ok=True)
CHAT=DATA/"infini_friend_chat.json"
POSTERS=DATA/"infini_poster_miniapps.json"

def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def secret():
    # Same shared secret location used everywhere else (id_entry_7000.py,
    # user_scope_7000.py, infini_clean_ui_7000.py, etc.):
    # <project_root>/8032/data/infini_session_secret.txt. The original
    # version of this function checked BASE.parent/"data" and BASE/"data"
    # instead, neither of which exists on Render — that mismatch meant
    # uid() always returned None here, so every request looked logged
    # out even with a valid session cookie.
    infini_8032_root = Path(os.getenv("INFINI_8032_ROOT", str(BASE.parent / "8032")))
    for p in [
        infini_8032_root / "data" / "infini_session_secret.txt",
        BASE.parent / "8032" / "data" / "infini_session_secret.txt",
        BASE.parent / "data" / "infini_session_secret.txt",
        BASE / "data" / "infini_session_secret.txt",
    ]:
        try:
            s = p.read_text(encoding="utf-8").strip()
            if s:
                return s
        except Exception:
            pass
    return os.getenv("INFINI_SESSION_SECRET", "").strip()
def uid(req):
    try:
        return str(URLSafeSerializer(secret(),salt="infini-session").loads(req.cookies.get("infini_session","")).get("user_id") or "").strip() or None
    except:return None
def skey(v):return re.sub(r"[^A-Za-z0-9_.:-]+","_",str(v or ""))[:120] or "default"

FRIEND=r'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Friend Chat</title>
<style>*{box-sizing:border-box}body{margin:0;background:#030303;color:#fff;font-family:system-ui}.w{max-width:760px;margin:auto;padding:16px}.c{border:1px solid #4b2d1a;border-radius:22px;padding:14px;margin:12px 0;background:#080706}.r{display:flex;gap:8px}input,textarea{width:100%;background:#030303;color:#fff;border:1px solid #4b2d1a;border-radius:14px;padding:12px;font:inherit}button,a{border:0;border-radius:14px;padding:12px;background:#ff941f;color:#160800;font-weight:900;text-decoration:none}.msgs{min-height:260px;max-height:55vh;overflow:auto;display:flex;flex-direction:column;gap:8px;margin:12px 0}.m{max-width:82%;background:#181818;padding:10px;border-radius:15px}.me{align-self:flex-end;background:#3b210e}.z{font-size:10px;color:#999;margin-top:4px}</style>
<body><main class="w"><div class="r"><b style="flex:1">∞ FRIEND CHAT</b><a href="/id">กลับ ID</a></div><section class="c"><div class="r"><input id="peer" placeholder="รหัส ID / username"><button id="open">เปิดแชท</button></div></section><section class="c"><b id="who">เลือกเพื่อนก่อน</b><div class="msgs" id="msgs"></div><textarea id="text" placeholder="ข้อความ"></textarea><div class="r" style="margin-top:8px"><input id="ctx" placeholder="Page context"><button id="send">ส่ง</button></div></section></main>
<script>const $=x=>document.getElementById(x);let peer='';async function load(){if(!peer)return;const d=await fetch('/api/friend-chat/thread?peer='+encodeURIComponent(peer)).then(r=>r.json());$('msgs').innerHTML='';(d.messages||[]).forEach(x=>{const m=document.createElement('div');m.className='m '+(x.mine?'me':'');m.textContent=x.text;const z=document.createElement('div');z.className='z';z.textContent=(x.context||'')+' '+(x.time||'');m.appendChild(z);$('msgs').appendChild(m)});$('msgs').scrollTop=$('msgs').scrollHeight}$('open').onclick=()=>{peer=$('peer').value.trim();$('who').textContent=peer?'คุยกับ '+peer:'เลือกเพื่อนก่อน';load()};$('send').onclick=async()=>{if(!peer||!$('text').value.trim())return;const d=await fetch('/api/friend-chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({peer:peer,text:$('text').value,context:$('ctx').value})}).then(r=>r.json());if(d.ok){$('text').value='';load()}};setInterval(()=>{if(peer)load()},4000)</script></body></html>'''

POSTER=r'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Poster Mini App</title>
<style>*{box-sizing:border-box}body{margin:0;background:#030303;color:#fff;font-family:system-ui}.w{max-width:760px;margin:auto;padding:16px 16px 100px}.hero{position:relative;aspect-ratio:4/5;border:1px solid #5a341d;border-radius:25px;overflow:hidden;background:#090909}.hero img,.hero video{width:100%;height:100%;object-fit:cover}.copy{position:absolute;left:6%;right:6%;bottom:6%;background:#000a;padding:14px;border-radius:16px}.copy h1{margin:0}.c{border:1px solid #392619;border-radius:20px;padding:14px;margin-top:12px}.g{display:grid;grid-template-columns:1fr 1fr;gap:8px}label{display:block;color:#baa99b;font-size:12px;margin-top:9px}input,textarea,select{width:100%;background:#030303;color:#fff;border:1px solid #4b2d1a;border-radius:13px;padding:11px;font:inherit}button,a{border:1px solid #754116;border-radius:14px;padding:12px;background:#080808;color:#ffc17d;font-weight:900;text-decoration:none}.primary{background:#ff941f;color:#160800}.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.status{font-size:12px;color:#aaa;margin-top:8px;word-break:break-all}@media(max-width:520px){.g,.actions{grid-template-columns:1fr}}</style>
<body><main class="w"><div style="display:flex;justify-content:space-between;align-items:center"><b>∞ POSTER / MINI APP</b><a id="back" href="/id">กลับ</a></div><section class="hero" id="pv"><div class="copy"><h1 id="pt">MINI APP</h1><p id="px">แผ่นนี้เผยแพร่เป็น Mini App ได้</p></div></section><section class="c"><div class="g"><div><label>แผ่น / Page ID</label><input id="sheet"></div><div><label>สถานะ</label><select id="vis"><option value="draft">Draft</option><option value="public">Public</option><option value="private">Private</option></select></div></div><label>หัวข้อ</label><input id="title"><label>ข้อความ</label><textarea id="text"></textarea><label>URL รูป/วิดีโอจากคลังเดิม</label><input id="media"><div class="g"><div><label>เชื่อมแผ่น</label><select id="lt"><option value="">ไม่เชื่อม</option><option value="A">A · ID เดียวกัน</option><option value="B">B · ต่าง ID</option></select></div><div><label>รหัส ID ปลายทาง (B)</label><input id="tid"></div></div><label>ตำแหน่งแผ่นปลายทาง</label><input id="ts"><div class="actions"><button id="save">บันทึก</button><button class="primary" id="pub">บันทึก + Public</button></div><div class="status" id="st"></div></section></main>
<script>const $=x=>document.getElementById(x),q=new URLSearchParams(location.search);$('sheet').value=q.get('sheet')||q.get('target')||'default';$('back').href=q.get('from')||'/id';function pv(){pt.textContent=$('title').value||'MINI APP';px.textContent=$('text').value||'แผ่นนี้เผยแพร่เป็น Mini App ได้';const o=$('pv').querySelector('.media');if(o)o.remove();const u=$('media').value.trim();if(u){const e=document.createElement(/\.(mp4|webm|mov)(\?|$)/i.test(u)?'video':'img');e.className='media';e.src=u;if(e.tagName==='VIDEO'){e.autoplay=true;e.loop=true;e.muted=true;e.playsInline=true}$('pv').insertBefore(e,$('pv').firstChild)}}['title','text','media'].forEach(k=>$(k).addEventListener('input',pv));async function load(){const d=await fetch('/api/poster-miniapp?sheet='+encodeURIComponent($('sheet').value)).then(r=>r.json());if(d.item){const x=d.item;$('title').value=x.title||'';$('text').value=x.text||'';$('media').value=x.media||'';$('vis').value=x.visibility||'draft';$('lt').value=x.link_type||'';$('tid').value=x.target_id||'';$('ts').value=x.target_sheet||''}pv();$('st').textContent=d.public_url?'Public URL: '+d.public_url:''}async function save(pub){const b={sheet:$('sheet').value,title:$('title').value,text:$('text').value,media:$('media').value,visibility:pub?'public':$('vis').value,link_type:$('lt').value,target_id:$('tid').value,target_sheet:$('ts').value};const d=await fetch('/api/poster-miniapp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());if(d.ok){$('vis').value=b.visibility;$('st').textContent='บันทึกแล้ว · Public URL: '+d.public_url}else alert(d.error||'บันทึกไม่สำเร็จ')}$('save').onclick=()=>save(false);$('pub').onclick=()=>save(true);$('sheet').onchange=load;load()</script></body></html>'''

PUBLIC=r'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>INFINI Mini App</title><style>*{box-sizing:border-box}body{margin:0;background:#000;color:#fff;font-family:system-ui}.a{max-width:760px;margin:auto}.h{position:relative;aspect-ratio:4/5;background:#090909;overflow:hidden}.h img,.h video{width:100%;height:100%;object-fit:cover}.c{position:absolute;left:6%;right:6%;bottom:6%;background:#000a;padding:15px;border-radius:18px}h1{margin:0}.go{display:block;margin:14px;padding:15px;border-radius:17px;background:#ff941f;color:#160800;text-align:center;text-decoration:none;font-weight:900}.i{padding:14px;color:#999;font-size:12px}</style><body><main class="a"><section class="h">__M__<div class="c"><h1>__T__</h1><p>__X__</p></div></section>__G__<div class="i">INFINI MINI APP · Public sheet</div></main></body></html>'''

def install_clean_final_completion_v1(app):
    if getattr(app.state,"_clean_final_completion_v1",False):return
    app.state._clean_final_completion_v1=True

    @app.get("/friend-chat",response_class=HTMLResponse)
    async def friend_page(request:Request):
        return HTMLResponse(FRIEND) if uid(request) else HTMLResponse("login required",status_code=401)

    @app.get("/api/friend-chat/thread")
    async def thread(request:Request,peer:str):
        me=uid(request)
        if not me:return JSONResponse({"ok":False},status_code=401)
        out=[]
        for x in load(CHAT,{"messages":[]}).get("messages",[]):
            if {x.get("from"),x.get("to")}=={me,peer}:
                y=dict(x);y["mine"]=x.get("from")==me;out.append(y)
        return {"ok":True,"messages":out[-300:]}

    @app.post("/api/friend-chat/send")
    async def send(request:Request):
        me=uid(request);p=await request.json()
        if not me:return JSONResponse({"ok":False},status_code=401)
        peer=str(p.get("peer") or "").strip();text=str(p.get("text") or "").strip()
        if not peer or not text:return JSONResponse({"ok":False,"error":"ต้องมีผู้รับและข้อความ"},status_code=400)
        d=load(CHAT,{"messages":[]});d.setdefault("messages",[]).append({"id":secrets.token_hex(8),"from":me,"to":peer,"text":text[:5000],"context":str(p.get("context") or "")[:500],"time":datetime.now(timezone.utc).isoformat()});d["messages"]=d["messages"][-10000:];save(CHAT,d);return {"ok":True}

    @app.get("/poster",response_class=HTMLResponse)
    async def poster(request:Request):
        return HTMLResponse(POSTER) if uid(request) else HTMLResponse("login required",status_code=401)

    @app.get("/api/poster-miniapp")
    async def pget(request:Request,sheet:str="default"):
        me=uid(request)
        if not me:return JSONResponse({"ok":False},status_code=401)
        item=load(POSTERS,{}).get(me+"::"+sheet)
        return {"ok":True,"item":item,"public_url":"/p/"+quote(me,safe="")+"/"+quote(skey(sheet),safe="")}

    @app.post("/api/poster-miniapp")
    async def psave(request:Request):
        me=uid(request);p=await request.json()
        if not me:return JSONResponse({"ok":False},status_code=401)
        sheet=str(p.get("sheet") or "default").strip();lt=str(p.get("link_type") or "").upper()
        if lt not in {"","A","B"}:return JSONResponse({"ok":False,"error":"เชื่อมแผ่นใช้ A หรือ B"},status_code=400)
        if lt=="B" and not str(p.get("target_id") or "").strip():return JSONResponse({"ok":False,"error":"B ต้องมีรหัส ID"},status_code=400)
        if lt and not str(p.get("target_sheet") or "").strip():return JSONResponse({"ok":False,"error":"ต้องมีตำแหน่งแผ่น"},status_code=400)
        item={"owner":me,"sheet":sheet,"title":str(p.get("title") or "")[:300],"text":str(p.get("text") or "")[:3000],"media":str(p.get("media") or "")[:2000],"visibility":str(p.get("visibility") or "draft"),"link_type":lt,"target_id":str(p.get("target_id") or "")[:200],"target_sheet":str(p.get("target_sheet") or "")[:1000],"updated_at":datetime.now(timezone.utc).isoformat()}
        d=load(POSTERS,{});d[me+"::"+sheet]=item;save(POSTERS,d)
        return {"ok":True,"public_url":"/p/"+quote(me,safe="")+"/"+quote(skey(sheet),safe="")}

    @app.get("/p/{owner}/{sheet_key}",response_class=HTMLResponse)
    async def ppublic(owner:str,sheet_key:str):
        item=None
        for x in load(POSTERS,{}).values():
            if x.get("owner")==owner and skey(x.get("sheet"))==sheet_key:item=x;break
        if not item or item.get("visibility")!="public":return HTMLResponse("Mini App is not public",status_code=404)
        u=str(item.get("media") or "");m=""
        if u:
            m=(f'<video src="{html.escape(u)}" autoplay muted loop playsinline></video>' if re.search(r"\.(mp4|webm|mov)(\?|$)",u,re.I) else f'<img src="{html.escape(u)}" alt="">')
        lt=item.get("link_type");ts=str(item.get("target_sheet") or "").strip();g=""
        if lt=="A" and ts:
            href=ts if ts.startswith("/") else "/"+ts.lstrip("/")
            g=f'<a class="go" href="{html.escape(href)}">เข้าแผ่นต่อไป →</a>'
        elif lt=="B" and ts:
            href="/id-hub/member/"+quote(str(item.get("target_id") or ""),safe="")+"?target_sheet="+quote(ts,safe="")
            g=f'<a class="go" href="{html.escape(href)}">ไป ID / แผ่นปลายทาง →</a>'
        return HTMLResponse(PUBLIC.replace("__M__",m).replace("__T__",html.escape(str(item.get("title") or "MINI APP"))).replace("__X__",html.escape(str(item.get("text") or ""))).replace("__G__",g))

    @app.get("/api/clean-final/health")
    async def health():
        return {"ok":True,"friend_chat":True,"poster_miniapp":True,"public_url":True,"link_A_B":True}
