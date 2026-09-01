from pathlib import Path
import json,secrets,hashlib,hmac,time,shutil
from fastapi import Form,Request,UploadFile
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
B=Path(__file__).parent;D=B/'data';U=B/'uploads/member_profiles';F=D/'members.json'
D.mkdir(exist_ok=True);U.mkdir(parents=True,exist_ok=True);S=b'infini-secret'
def load():
 try:return json.loads(F.read_text())
 except:return {}
def save(x):F.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def hp(p,s=None):
 s=s or secrets.token_hex(16);return s,hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),120000).hex()
def esc(x):
 import html;return html.escape(str(x or ''),quote=True)
def tok(e):
 z=str(int(time.time())+2592000);q=f'{e}|{z}';return q+'|'+hmac.new(S,q.encode(),hashlib.sha256).hexdigest()
def who(r):
 try:
  e,z,g=r.cookies.get('infini_member','').rsplit('|',2);q=f'{e}|{z}'
  if int(z)<time.time() or not hmac.compare_digest(g,hmac.new(S,q.encode(),hashlib.sha256).hexdigest()):return None
  return e,load().get(e)
 except:return None
CSS="""<style>*{box-sizing:border-box}body{margin:0;background:#06101e;color:#fff;font-family:system-ui}a{color:inherit;text-decoration:none}main{max-width:720px;margin:auto;min-height:100vh;background:#0d1b2e}header{padding:16px;display:flex;justify-content:space-between}.hero{height:55vh;background:#1a2d4a;display:grid;place-items:center;position:relative;overflow:hidden}.hero img{width:100%;height:100%;object-fit:cover}.info,form{padding:20px}input,textarea{width:100%;padding:13px;margin:7px 0 14px;border-radius:12px;border:1px solid #345;background:#091523;color:#fff}button,.btn{border:0;border-radius:13px;padding:13px 16px;background:linear-gradient(135de