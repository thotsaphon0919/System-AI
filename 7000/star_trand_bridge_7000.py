from __future__ import annotations
from typing import Any
import hashlib, json, os, urllib.request
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

STAR_URL = os.getenv("INFINI_STAR_TRAND_URL", "http://127.0.0.1:7050").rstrip("/")
MARKER = "INFINI_STAR_TRAND_BRIDGE_V1"


def _user_key(request: Request) -> str:
    raw = request.cookies.get("infini_session") or request.cookies.get("session") or "local"
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16]


def _call_star(payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(STAR_URL + "/v1/command", data=body, method="POST", headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

SCRIPT = r'''
<script>
(()=>{
 if(window.__INFINI_STAR_TRAND_BRIDGE_V1)return; window.__INFINI_STAR_TRAND_BRIDGE_V1=true;
 function speak(text){
   if(!text || !('speechSynthesis' in window))return;
   try{speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(text); u.lang='th-TH'; speechSynthesis.speak(u)}catch(_e){}
 }
 window.addEventListener('infini-voice-command',ev=>{
   const c=(ev&&ev.detail)||{};
   if(!c.star_trand)return;
   const box=document.getElementById('ivx-result');
   if(box && c.assistant_text) box.textContent=c.assistant_text;
   if(c.speak_text) speak(c.speak_text);
 });
})();
</script>
'''

class _BridgeInject(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype.lower() or response.headers.get("content-encoding"):
            return response
        try:
            chunks=[chunk async for chunk in response.body_iterator]; body=b"".join(chunks); text=body.decode("utf-8")
        except Exception:
            return response
        # Runtime-only switch: existing Clean source file stays untouched.
        text = text.replace('jfetch("/infini-voice-api/command"', 'jfetch("/infini-trading-assistant/command"')
        if MARKER not in text:
            inject = f"<!-- {MARKER} -->" + SCRIPT
            text = text.replace("</body>", inject + "</body>", 1) if "</body>" in text else text + inject
        headers=dict(response.headers); headers.pop("content-length",None)
        return Response(content=text,status_code=response.status_code,headers=headers,media_type="text/html")


def install_star_trand_bridge_7000(app):
    if getattr(app.state, "infini_star_trand_bridge_v1", False): return
    app.state.infini_star_trand_bridge_v1=True

    async def unified_command(request: Request):
        p=await request.json(); scope=str(p.get("scope") or ""); text=str(p.get("text") or "").strip()
        if not text: return JSONResponse({"ok":False,"error":"empty command"},status_code=400)
        # Reuse the Clean parser/config in-process; this keeps one mic/text command brain.
        try:
            import subpage_voice_api_7000 as voice
            data=voice._load(); item=data.setdefault("items",{}).get(voice._scope_key(request,scope),{})
            aliases=item.get("aliases",{}) if isinstance(item,dict) else {}
            account_label=str(item.get("account_label") or "") if isinstance(item,dict) else ""
            parsed=voice._parse_command(text,account_label,aliases if isinstance(aliases,dict) else {})
        except Exception as exc:
            account_label=""; parsed={"raw":text,"action":"ASK","target":"CURRENT_SHEET","parser_error":str(exc)}
        payload={
            "text": text,
            "scope": scope,
            "user_key": _user_key(request),
            "account_label": account_label,
            "parsed_command": parsed,
            "context": {"origin_scope":scope,"return_target":scope,"account_label":account_label},
        }
        try:
            star=_call_star(payload)
            cmd=dict(parsed)
            cmd.update({"star_trand":True,"assistant_text":star.get("assistant_text",""),"speak_text":star.get("speak_text",""),"mission":star.get("mission",{})})
            return JSONResponse({"ok":True,"command":cmd,"star_trand":star,"shared_command":True,"broker_execution":False})
        except Exception as exc:
            cmd=dict(parsed); cmd.update({"star_trand":False,"assistant_text":"STAR TRAND ยังไม่ออนไลน์ แต่ Clean parser ยังรับคำสั่งได้","speak_text":"STAR TRAND ยังไม่ออนไลน์"})
            return JSONResponse({"ok":True,"command":cmd,"shared_command":True,"star_error":str(exc),"broker_execution":False})

    app.add_api_route("/infini-trading-assistant/command", unified_command, methods=["POST"], name="infini_trading_assistant_command_v1")
    app.add_middleware(_BridgeInject)
