from fastapi import File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
from threading import Lock
import json
import mimetypes
import re
import shutil
import time
import uuid

from user_scope_7000 import scoped_data_file, scoped_upload_dir, scoped_upload_url


class DetailTextIn(BaseModel):
    detail: str = ""


class ZoneIn(BaseModel):
    zone: str = ""


class ChatIn(BaseModel):
    text: str = ""


class RegisterIn(BaseModel):
    full_no: str
    media_url: str = ""
    media_type: str = ""


def install_detail_swipe_7000(app):
    base = Path(__file__).resolve().parent
    data_dir = base / "data"
    upload_dir = base / "uploads"
    legacy_db_file = data_dir / "detail_swipe_7000.json"
    legacy_remote_state_file = data_dir / "remote_show_state.json"

    def db_file():
        return scoped_data_file(base, "detail_swipe_7000.json", legacy_db_file)

    def remote_state_file():
        return scoped_data_file(base, "remote_show_state.json", legacy_remote_state_file)
    lock = Lock()

    data_dir.mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)

    full_no_re = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
    group_no_re = re.compile(r"^(\d+)\.(\d+)$")

    def now():
        return int(time.time())

    def page_id():
        return "detail_" + uuid.uuid4().hex[:12]

    def clean_full_no(value: str):
        value = (value or "").strip()
        match = full_no_re.fullmatch(value)
        if not match:
            raise HTTPException(400, "เลขหน้าต้องเป็นรูปแบบ 1.1.1")
        return value, f"{match.group(1)}.{match.group(2)}", int(match.group(3))

    def clean_group_no(value: str):
        value = (value or "").strip()
        if not group_no_re.fullmatch(value):
            raise HTTPException(400, "เลขกลุ่มต้องเป็นรูปแบบ 1.1")
        return value

    def empty_db():
        return {"version": 1, "groups": {}}

    def load_db_unlocked():
        if not db_file().exists():
            return empty_db()
        try:
            data = json.loads(db_file().read_text(encoding="utf-8"))
        except Exception:
            broken = db_file().with_name(
                f"{db_file().stem}.broken_{now()}{db_file().suffix}"
            )
            try:
                shutil.copy2(db_file(), broken)
            except Exception:
                pass
            return empty_db()
        if not isinstance(data, dict):
            data = empty_db()
        data.setdefault("version", 1)
        if not isinstance(data.get("groups"), dict):
            data["groups"] = {}
        return data

    def save_db_unlocked(data):
        tmp = db_file().with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(db_file())

    def sync_parent_thumbnail(full_no, media_url, media_type):
        """
        ให้รูปของหน้าแรกในชุด เช่น 7.1.1 กลับไปเป็นภาพหน้าปก
        ของช่อง no.7.1 ในหน้า Subpage โดยอัตโนมัติ
        """
        match = full_no_re.fullmatch((full_no or "").strip())
        if not match or int(match.group(3)) != 1:
            return False
        if not remote_state_file().exists():
            return False

        room_index = int(match.group(1)) - 1
        item_index = int(match.group(2)) - 1

        try:
            state = json.loads(remote_state_file().read_text(encoding="utf-8"))
        except Exception as exc:
            raise HTTPException(
                500,
                f"อ่านข้อมูล Subpage เพื่อซิงก์รูปไม่สำเร็จ: {exc}",
            )

        pages = state.get("pages")
        if not isinstance(pages, list) or not (0 <= room_index < len(pages)):
            raise HTTPException(404, "ไม่พบห้องแม่ของรูปนี้")

        parent_page = pages[room_index]
        items = parent_page.get("items")
        if not isinstance(items, list) or not (0 <= item_index < len(items)):
            raise HTTPException(404, "ไม่พบช่องย่อยแม่ของรูปนี้")

        parent_item = items[item_index]
        parent_item["media_url"] = media_url or ""
        parent_item["media_type"] = (
            "video" if media_type == "video" else "image"
        ) if media_url else ""
        parent_item["updated_at"] = now()
        parent_page["updated_at"] = now()

        tmp = remote_state_file().with_suffix(".detail_sync.tmp")
        tmp.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(remote_state_file())
        return True

    def normalize_page(page, group_no, index):
        page.setdefault("id", page_id())
        page["no"] = f"{group_no}.{index}"
        page.setdefault("media_url", "")
        page.setdefault("media_type", "")
        page.setdefault("detail", "")
        page.setdefault("zone", "")
        page.setdefault("messages", [])
        if not isinstance(page["messages"], list):
            page["messages"] = []
        page.setdefault("created_at", now())
        page.setdefault("updated_at", now())
        return page

    def ensure_group_unlocked(data, group_no):
        groups = data["groups"]
        group = groups.setdefault(
            group_no,
            {
                "group_no": group_no,
                "pages": [],
                "created_at": now(),
                "updated_at": now(),
            },
        )
        if not isinstance(group.get("pages"), list):
            group["pages"] = []
        for index, page in enumerate(group["pages"], start=1):
            normalize_page(page, group_no, index)
        group["updated_at"] = now()
        return group

    def ensure_page_unlocked(
        data,
        full_no,
        media_url="",
        media_type="",
        create_missing=True,
    ):
        full_no, group_no, index = clean_full_no(full_no)
        group = ensure_group_unlocked(data, group_no)

        if create_missing:
            while len(group["pages"]) < index:
                next_index = len(group["pages"]) + 1
                group["pages"].append(
                    normalize_page({}, group_no, next_index)
                )

        if index < 1 or index > len(group["pages"]):
            raise HTTPException(404, "ยังไม่มีหน้านี้")

        page = normalize_page(group["pages"][index - 1], group_no, index)

        if media_url and not page.get("media_url"):
            page["media_url"] = media_url
            page["media_type"] = (
                "video" if media_type == "video" else "image"
            )
            page["updated_at"] = now()

        return group, page, index - 1

    def public_group(group, active_index=0):
        return {
            "group_no": group["group_no"],
            "active_index": max(0, min(active_index, len(group["pages"]) - 1)),
            "pages": [
                {
                    "id": page["id"],
                    "no": page["no"],
                    "media_url": page.get("media_url", ""),
                    "media_type": page.get("media_type", ""),
                    "detail": page.get("detail", ""),
                    "zone": page.get("zone", ""),
                    "messages": page.get("messages", []),
                }
                for page in group["pages"]
            ],
        }

    html = r'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>INFINI DETAIL PAGE</title>
<style>
:root{
  --bg:#050302;
  --panel:#160904;
  --panel2:#250e03;
  --orange:#ff9200;
  --orange2:#ffbd28;
  --line:rgba(255,145,0,.42);
  --text:#fff7ef;
  --muted:#d8b892;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;min-height:100%;background:radial-gradient(circle at top,#251004,#050302 48%,#000);color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
body{padding-bottom:32px}
button,input,textarea{font:inherit}
.top{
  position:sticky;top:0;z-index:30;
  display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:10px;
  padding:12px 14px;background:rgba(5,3,2,.9);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line)
}
.back,.smallBtn{
  border:1px solid var(--line);border-radius:16px;background:#0c0502;color:#ffd39a;
  padding:10px 14px;font-weight:900
}
.title{text-align:center;font-weight:1000;color:#ff9f23;letter-spacing:.7px}
.counter{font-size:12px;color:var(--muted);white-space:nowrap}
.viewport{overflow:hidden}
.track{
  display:flex;overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;
  scrollbar-width:none;overscroll-behavior-x:contain
}
.track::-webkit-scrollbar{display:none}
.slide{flex:0 0 100%;scroll-snap-align:start;padding:14px}
.page{
  max-width:760px;margin:auto;border:1px solid var(--line);border-radius:28px;
  background:linear-gradient(180deg,rgba(36,14,3,.92),rgba(9,4,2,.98));overflow:hidden
}
.hero{
  position:relative;margin:14px;border:1px solid var(--line);border-radius:24px;
  min-height:62vh;overflow:hidden;background:#080402;display:grid;place-items:center
}
.hero img,.hero video{width:100%;height:100%;max-height:72vh;object-fit:contain;display:block;background:#000}
.emptyHero{display:grid;place-items:center;min-height:62vh;width:100%;color:rgba(255,164,35,.45);font-size:72px;font-weight:300}
.uploadHit{position:absolute;inset:0;border:0;background:transparent;color:transparent}
.noBadge{
  position:absolute;left:12px;bottom:12px;z-index:5;padding:8px 12px;border:1px solid rgba(255,190,90,.55);
  border-radius:999px;background:rgba(0,0,0,.74);color:#ffd28c;font-weight:1000
}
.section{margin:0 14px 14px;padding:14px;border:1px solid var(--line);border-radius:22px;background:rgba(0,0,0,.34)}
.sectionTitle{font-size:18px;font-weight:1000;margin:0}
.sectionHeadRow{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 10px}
.zoneSelect{
  width:min(52%,260px);min-height:42px;border:1px solid rgba(255,145,0,.48);
  border-radius:14px;background:#090402;color:#ffd39a;padding:9px 11px;
  font-weight:900;outline:none
}
.detailBox{
  width:100%;min-height:82px;max-height:150px;resize:vertical;border:1px solid rgba(255,145,0,.35);
  border-radius:16px;background:#090402;color:#fff7ef;padding:12px;outline:none;line-height:1.45
}
.saveState{min-height:18px;margin-top:6px;color:var(--muted);font-size:12px}
.messages{display:grid;gap:8px;max-height:240px;overflow:auto;margin-bottom:10px}
.message{padding:9px 11px;border-radius:14px;background:#0e0603;border:1px solid rgba(255,145,0,.22);word-break:break-word}
.message small{display:block;color:var(--muted);margin-top:3px}
.chatRow{display:grid;grid-template-columns:1fr auto;gap:8px}
.chatInput{width:100%;border:1px solid rgba(255,145,0,.35);border-radius:15px;background:#090402;color:#fff;padding:11px;outline:none}
.sendBtn{border:0;border-radius:15px;background:linear-gradient(135deg,var(--orange2),var(--orange));color:#1b0800;padding:0 18px;font-weight:1000}
.addWrap{max-width:760px;margin:0 auto;padding:0 14px 20px}
.addBtn{
  width:100%;min-height:70px;border:1px solid #ffc04a;border-radius:24px;
  background:linear-gradient(180deg,var(--orange2),var(--orange));color:#1b0800;
  font-size:19px;font-weight:1000;box-shadow:0 14px 32px rgba(255,135,0,.18)
}
.hint{text-align:center;color:var(--muted);font-size:12px;margin:9px 0 0}
.toast{
  position:fixed;top:72px;left:50%;transform:translateX(-50%);z-index:80;display:none;
  max-width:calc(100% - 28px);padding:10px 14px;border:1px solid var(--line);border-radius:999px;
  background:#160904;color:#ffd398;text-align:center;font-weight:900
}
.toast.show{display:block}
@media(min-width:800px){.hero{min-height:520px}.emptyHero{min-height:520px}}

/* DETAIL MINI EDITOR V1 */
.edDots{
 position:absolute;right:14px;top:14px;z-index:50;
 width:44px;height:44px;border:1px solid #ff8a00;
 border-radius:14px;background:#080808dd;color:#fff;
 font-size:28px;font-weight:900
}
.edPanel[hidden]{display:none!important}
.edPanel{
 margin:14px 0;padding:14px;border:1px solid #ff8a00;
 border-radius:20px;background:#0b0704;color:#fff
}
.edHead{
 display:flex;justify-content:space-between;
 align-items:center;margin-bottom:12px
}
.edHead b{color:#ff8a00;font-size:19px}
.edClose{
 width:36px;height:36px;border:1px solid #6d3b18;
 border-radius:50%;background:#120a05;color:#fff;font-size:20px
}
.edGrid{
 display:grid;grid-template-columns:1fr 1fr;gap:10px
}
.edField{
 display:flex;flex-direction:column;gap:6px;padding:10px;
 border:1px solid #5d3217;border-radius:14px;background:#120a05
}
.edField.full{grid-column:1/-1}
.edField select,.edField input{width:100%}
.edField select{
 height:40px;border:1px solid #70401e;border-radius:10px;
 background:#080503;color:#fff
}
.edField input[type=color]{
 height:40px;border:0;background:transparent
}
.edActions{
 display:grid;grid-template-columns:1fr 1fr;
 gap:9px;margin-top:12px
}
.edBtn{
 min-height:46px;border:1px solid #70401e;
 border-radius:13px;background:#120a05;color:#fff;
 font-weight:800
}
.edBtn.upload{grid-column:1/-1}
.edBtn.save{
 background:#ff9200;color:#1d0d00;border-color:#ff9200
}
.hero{
 border-style:solid!important;
 border-color:var(--ed-color,#ff8a00)!important;
 border-width:var(--ed-width,2px)!important;
 overflow:hidden
}
.hero img,.hero video{
 transform:scale(var(--ed-scale,1));
 transform-origin:center;
 transition:.2s
}
.slide.edOn,
.slide.edOn textarea,
.slide.edOn input,
.slide.edOn select,
.slide.edOn button{
 font-family:var(--ed-font,system-ui,sans-serif)
}
.slide.edOn .section,
.slide.edOn [data-detail]{
 font-size:var(--ed-size,18px)
}
@media(max-width:520px){
 .edGrid{grid-template-columns:1fr}
 .edField.full{grid-column:auto}
}

</style>
</head>
<body>
<div class="toast" id="toast"></div>
<header class="top">
  <button class="back" id="backBtn">← กลับ</button>
  <div class="title" id="title">INFINI PAGE</div>
  <div class="counter" id="counter"></div>
</header>
<div class="viewport"><div class="track" id="track"></div></div>
<div class="addWrap">
  <button class="addBtn" id="addBtn">＋ เพิ่มหน้าถัดไป</button>
  <div class="hint">มีหลายหน้าแล้วปัดซ้าย–ขวาได้</div>
</div>
<input id="mediaInput" type="file" accept="image/*,video/*" hidden>
<script>
const fullNo = decodeURIComponent(location.pathname.split('/').filter(Boolean).pop() || '');
let group = null;
let activeIndex = 0;
let detailTimer = null;
const track = document.getElementById('track');
const mediaInput = document.getElementById('mediaInput');
const $ = id => document.getElementById(id);

function toast(message){
  const box=$('toast'); box.textContent=message; box.classList.add('show');
  setTimeout(()=>box.classList.remove('show'),1500);
}
async function api(url, options={}){
  const response=await fetch(url, options);
  if(!response.ok) throw new Error(await response.text());
  return await response.json();
}
function esc(value){
  return String(value||'').replace(/[&<>"']/g, ch=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  })[ch]);
}

// DETAIL MINI EDITOR V1
const EDK='infini_detail_editor:'+location.pathname;
const EDD={
 color:'#ff8a00',
 width:2,
 font:'system-ui,sans-serif',
 size:18,
 scale:100
};

let EDS=(()=>{
 try{
  return JSON.parse(localStorage.getItem(EDK)||'{}');
 }catch(e){
  return {};
 }
})();

function edState(i){
 return Object.assign({},EDD,EDS[i]||{});
}

function edPanel(i,x){
 return (x||document).querySelector(`[data-ed-panel="${i}"]`);
}

function edRead(i,x){
 let q=edPanel(i,x);
 if(!q)return edState(i);

 return {
  color:q.querySelector('[data-ed-color]').value,
  width:+q.querySelector('[data-ed-width]').value,
  font:q.querySelector('[data-ed-font]').value,
  size:+q.querySelector('[data-ed-size]').value,
  scale:+q.querySelector('[data-ed-scale]').value
 };
}

function edPaint(i,x,v){
 if(!x)return;

 v=v||edState(i);
 x.classList.add('edOn');

 x.style.setProperty('--ed-color',v.color);
 x.style.setProperty('--ed-width',v.width+'px');
 x.style.setProperty('--ed-font',v.font);
 x.style.setProperty('--ed-size',v.size+'px');
 x.style.setProperty('--ed-scale',v.scale/100);

 let q=edPanel(i,x);
 if(!q)return;

 q.querySelector('[data-ed-color]').value=v.color;
 q.querySelector('[data-ed-width]').value=v.width;
 q.querySelector('[data-ed-font]').value=v.font;
 q.querySelector('[data-ed-size]').value=v.size;
 q.querySelector('[data-ed-scale]').value=v.scale;
}

function edSave(i,x){
 EDS[i]=edRead(i,x);
 localStorage.setItem(EDK,JSON.stringify(EDS));
 edPaint(i,x);
 toast('บันทึกรูปแบบแล้ว');
}

function edReset(i,x){
 delete EDS[i];
 localStorage.setItem(EDK,JSON.stringify(EDS));
 edPaint(i,x,EDD);
 toast('คืนค่าเดิมแล้ว');
}

function mediaMarkup(page){
  if(page.media_url && page.media_type==='video'){
    return `<video src="${esc(page.media_url)}" controls playsinline></video>`;
  }
  if(page.media_url){
    return `<img src="${esc(page.media_url)}" alt="${esc(page.no)}">`;
  }
  return '<div class="emptyHero">＋</div>';
}
function messagesMarkup(page){
  if(!page.messages || !page.messages.length){
    return '<div class="message">ยังไม่มีข้อความ</div>';
  }
  return page.messages.map(msg=>
    `<div class="message">${esc(msg.text)}<small>เพื่อน</small></div>`
  ).join('');
}
function render(){
  track.innerHTML='';
  group.pages.forEach((page,index)=>{
    const slide=document.createElement('section');
    slide.className='slide';
    slide.dataset.index=String(index);
    slide.innerHTML=`
      <article class="page">
        <div class="hero">
${mediaMarkup(page)}
<button class="uploadHit" data-upload="${index}" aria-label="อัปโหลดรูปหรือวิดีโอ"></button>
<button type="button" class="edDots" data-ed-open="${index}" aria-label="แก้ไข">⋮</button>
<div class="noBadge">no.${esc(page.no)}</div>
</div>

<div class="edPanel" data-ed-panel="${index}" hidden>
 <div class="edHead">
  <b>ปรับแต่งหน้านี้</b>
  <button type="button" class="edClose" data-ed-close>×</button>
 </div>

 <div class="edGrid">
  <button type="button" class="edBtn upload" data-ed-upload="${index}">
   อัปโหลด / เปลี่ยนรูป
  </button>

  <label class="edField">
   <span>สีกรอบ</span>
   <input type="color" value="#ff8a00"
          data-ed-color data-ed-input="${index}">
  </label>

  <label class="edField">
   <span>ความหนากรอบ</span>
   <input type="range" min="0" max="12" value="2"
          data-ed-width data-ed-input="${index}">
  </label>

  <label class="edField full">
   <span>ฟอนต์</span>
   <select data-ed-font data-ed-input="${index}">
    <option value="system-ui,sans-serif">โมเดิร์น</option>
    <option value="Georgia,serif">คลาสสิก</option>
    <option value="Impact,sans-serif">สตรีท / หนา</option>
    <option value="monospace">เทค / โมโน</option>
   </select>
  </label>

  <label class="edField">
   <span>ขนาดตัวหนังสือ</span>
   <input type="range" min="14" max="34" value="18"
          data-ed-size data-ed-input="${index}">
  </label>

  <label class="edField">
   <span>ขยายรูป</span>
   <input type="range" min="100" max="180" step="5" value="100"
          data-ed-scale data-ed-input="${index}">
  </label>
 </div>

 <div class="edActions">
  <button type="button" class="edBtn"
          data-ed-reset="${index}">คืนค่า</button>
  <button type="button" class="edBtn save"
          data-ed-save="${index}">บันทึก</button>
 </div>
</div>
        <section class="section">
          <div class="sectionHeadRow">
            <h2 class="sectionTitle">รายละเอียด</h2>
            <select class="zoneSelect" data-zone="${index}" aria-label="เลือกโซน">
              <option value="" ${!page.zone ? 'selected' : ''}>เลือกโซน</option>
              <option value="1" ${page.zone==='1' ? 'selected' : ''}>ZONE 1 · ส่วนตัว</option>
              <option value="2" ${page.zone==='2' ? 'selected' : ''}>ZONE 2 · ออฟฟิศ</option>
              <option value="3" ${page.zone==='3' ? 'selected' : ''}>ZONE 3 · ร้านค้า</option>
              <option value="4" ${page.zone==='4' ? 'selected' : ''}>ZONE 4 · ชุมชน</option>
            </select>
          </div>
          <textarea class="detailBox" data-detail="${index}" placeholder="กรอกรายละเอียดสั้น ๆ ของหน้านี้">${esc(page.detail||'')}</textarea>
          <div class="saveState" data-save-state="${index}"></div>
        </section>
        <section class="section">
          <h2 class="sectionTitle">แชทเพื่อน</h2>
          <div class="messages" data-messages="${index}">${messagesMarkup(page)}</div>
          <div class="chatRow">
            <input class="chatInput" data-chat="${index}" placeholder="พิมพ์ข้อความ...">
            <button class="sendBtn" data-send="${index}">ส่ง</button>
          </div>
        </section>
      </article>`;
    track.appendChild(slide);
      edPaint(index,slide);
  });
  bindEvents();
  requestAnimationFrame(()=>goTo(activeIndex,false));
  updateTop();
}
function bindEvents(){
 document.querySelectorAll('[data-ed-open]').forEach(b=>{
  b.onclick=e=>{
   e.preventDefault();
   e.stopPropagation();

   let i=+b.dataset.edOpen;
   let x=b.closest('article');
   let q=edPanel(i,x);
   let opening=q.hidden;

   document.querySelectorAll('.edPanel').forEach(z=>z.hidden=true);
   q.hidden=!opening;
  };
 });

 document.querySelectorAll('[data-ed-close]').forEach(b=>{
  b.onclick=e=>{
   e.stopPropagation();
   b.closest('.edPanel').hidden=true;
  };
 });

 document.querySelectorAll('[data-ed-upload]').forEach(b=>{
  b.onclick=e=>{
   e.preventDefault();
   e.stopPropagation();

   document.querySelector(
    `[data-upload="${b.dataset.edUpload}"]`
   )?.click();
  };
 });

 document.querySelectorAll('[data-ed-input]').forEach(c=>{
  let update=e=>{
   e.stopPropagation();

   let i=+c.dataset.edInput;
   let x=c.closest('article');

   edPaint(i,x,edRead(i,x));
  };

  c.oninput=update;
  c.onchange=update;
 });

 document.querySelectorAll('[data-ed-save]').forEach(b=>{
  b.onclick=e=>{
   e.preventDefault();
   e.stopPropagation();

   let i=+b.dataset.edSave;
   let x=b.closest('article');

   edSave(i,x);
   b.closest('.edPanel').hidden=true;
  };
 });

 document.querySelectorAll('[data-ed-reset]').forEach(b=>{
  b.onclick=e=>{
   e.preventDefault();
   e.stopPropagation();

   let i=+b.dataset.edReset;
   let x=b.closest('article');

   edReset(i,x);
  };
 });

  document.querySelectorAll('[data-upload]').forEach(button=>{
    button.addEventListener('click',()=>{
      activeIndex=Number(button.dataset.upload||0);
      mediaInput.value=''; mediaInput.click();
    });
  });
  document.querySelectorAll('[data-detail]').forEach(box=>{
    box.addEventListener('input',()=>{
      const index=Number(box.dataset.detail||0);
      clearTimeout(detailTimer);
      const state=document.querySelector(`[data-save-state="${index}"]`);
      if(state) state.textContent='กำลังบันทึก...';
      detailTimer=setTimeout(()=>saveDetail(index,box.value),500);
    });
  });
  document.querySelectorAll('[data-zone]').forEach(select=>{
    select.addEventListener('change',()=>{
      saveZone(Number(select.dataset.zone||0), select.value);
    });
  });
  document.querySelectorAll('[data-send]').forEach(button=>{
    button.addEventListener('click',()=>sendChat(Number(button.dataset.send||0)));
  });
  document.querySelectorAll('[data-chat]').forEach(input=>{
    input.addEventListener('keydown',event=>{
      if(event.key==='Enter'){ event.preventDefault(); sendChat(Number(input.dataset.chat||0)); }
    });
  });
}
function updateTop(){
  const page=group.pages[activeIndex] || group.pages[0];
  if(!page) return;
  $('title').textContent=`INFINI PAGE ${page.no}`;
  $('counter').textContent=`${activeIndex+1} / ${group.pages.length}`;
}
function goTo(index,smooth=true){
  activeIndex=Math.max(0,Math.min(index,group.pages.length-1));
  const slide=track.children[activeIndex];
  if(slide) slide.scrollIntoView({behavior:smooth?'smooth':'auto',inline:'start',block:'nearest'});
  updateTop();
}
let scrollTimer=null;
track.addEventListener('scroll',()=>{
  clearTimeout(scrollTimer);
  scrollTimer=setTimeout(()=>{
    const width=track.clientWidth || 1;
    activeIndex=Math.max(0,Math.min(Math.round(track.scrollLeft/width),group.pages.length-1));
    updateTop();
  },80);
});
async function saveDetail(index,detail){
  const page=group.pages[index]; if(!page) return;
  try{
    group=await api(`/api/detail-page/${encodeURIComponent(page.no)}/detail`,{
      method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({detail})
    });
    group.pages[index].detail=detail;
    const state=document.querySelector(`[data-save-state="${index}"]`);
    if(state){state.textContent='บันทึกแล้ว';setTimeout(()=>state.textContent='',900);}
  }catch(error){toast('บันทึกรายละเอียดไม่สำเร็จ');}
}
async function saveZone(index,zone){
  const page=group.pages[index]; if(!page) return;
  const state=document.querySelector(`[data-save-state="${index}"]`);
  if(state) state.textContent='กำลังบันทึกโซน...';
  try{
    group=await api(`/api/detail-page/${encodeURIComponent(page.no)}/zone`,{
      method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({zone})
    });
    group.pages[index].zone=zone;
    if(state){state.textContent='บันทึกโซนแล้ว';setTimeout(()=>state.textContent='',900);}
  }catch(error){
    if(state) state.textContent='';
    toast('บันทึกโซนไม่สำเร็จ');
  }
}
async function sendChat(index){
  const page=group.pages[index];
  const input=document.querySelector(`[data-chat="${index}"]`);
  if(!page || !input) return;
  const text=input.value.trim(); if(!text) return;
  try{
    group=await api(`/api/detail-page/${encodeURIComponent(page.no)}/chat`,{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})
    });
    activeIndex=index; render(); goTo(index,false);
  }catch(error){toast('ส่งข้อความไม่สำเร็จ');}
}
mediaInput.addEventListener('change',async()=>{
  const file=mediaInput.files && mediaInput.files[0];
  const page=group.pages[activeIndex];
  if(!file || !page) return;
  const form=new FormData(); form.append('file',file); toast('กำลังอัปโหลด...');
  try{
    group=await api(`/api/detail-page/${encodeURIComponent(page.no)}/upload`,{method:'POST',body:form});
    render(); goTo(activeIndex,false); toast('อัปโหลดแล้ว');
  }catch(error){toast('อัปโหลดไม่สำเร็จ');}
});
$('addBtn').addEventListener('click',async()=>{
  try{
    const result=await api(`/api/detail-group/${encodeURIComponent(group.group_no)}/add`,{method:'POST'});
    group=result.group; activeIndex=group.pages.length-1; render();
    setTimeout(()=>goTo(activeIndex,true),80); toast(`สร้าง no.${result.created_no} แล้ว`);
  }catch(error){toast('เพิ่มหน้าไม่สำเร็จ');}
});
$('backBtn').addEventListener('click',()=>{
  if(history.length>1) history.back(); else location.href='/';
});
async function load(){
  const query=location.search || '';
  group=await api(`/api/detail-page/${encodeURIComponent(fullNo)}${query}`);
  activeIndex=group.active_index||0; render();
}
load().catch(error=>{console.error(error);toast('เปิดหน้าไม่สำเร็จ');});
</script>
</body>
</html>'''

    injection = r'''<script id="infini-detail-swipe-inject-v1">
(() => {
  const NUMBER = /(?:^|\D)(\d+\.\d+(?:\.\d+)?)(?:\D|$)/;
  let press = null;

  function normalizedNumber(value){
    const match = String(value || '').match(NUMBER);
    if(!match) return '';

    const parts = match[1].split('.');

    // ช่อง 14.5 จะเปิดหน้าแรกของชุด คือ 14.5.1
    return parts.length === 2
      ? match[1] + '.1'
      : match[1];
  }

  function findNumber(node){
    let current = node;

    for(
      let depth = 0;
      current && current !== document.body && depth < 8;
      depth++, current = current.parentElement
    ){
      const direct =
        current.getAttribute?.('data-sub-no') ||
        current.getAttribute?.('data-no') ||
        current.getAttribute?.('data-number') ||
        '';

      const directNo = normalizedNumber(direct);
      if(directNo){
        return {number: directNo, card: current};
      }

      const text = String(
        current.innerText ||
        current.textContent ||
        ''
      ).trim();

      const textNo = normalizedNumber(text);
      if(textNo){
        return {number: textNo, card: current};
      }
    }

    return null;
  }

  function mediaFrom(card){
    const media = card && card.querySelector
      ? card.querySelector('img,video')
      : null;

    if(!media){
      return {url:'', type:''};
    }

    return {
      url:
        media.currentSrc ||
        media.getAttribute('src') ||
        media.src ||
        '',
      type:
        media.tagName === 'VIDEO'
          ? 'video'
          : 'image'
    };
  }

  document.addEventListener(
    'pointerdown',
    event => {
      press = {
        id: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        time: Date.now()
      };
    },
    true
  );

  document.addEventListener(
    'pointerup',
    event => {
      const started = press;
      press = null;

      if(
        !started ||
        started.id !== event.pointerId
      ){
        return;
      }

      if(window.__infiniActionMenuOpen){
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        return;
      }

      const elapsed =
        Date.now() - started.time;

      const movedX =
        Math.abs(event.clientX - started.x);

      const movedY =
        Math.abs(event.clientY - started.y);

      // กดค้างยังใช้ระบบอัปโหลดเดิม ไม่เปลี่ยน
      if(
        elapsed >= 560 ||
        movedX > 12 ||
        movedY > 12
      ){
        return;
      }

      if(
        event.target.closest(
          'button,input,textarea,select,label,a'
        )
      ){
        return;
      }

      const found = findNumber(event.target);
      if(!found){
        return;
      }

      const media = mediaFrom(found.card);

      // หยุดหน้าดูเต็มแบบเก่า แล้วเปิดหน้ารายละเอียดใหม่แทน
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      const query = new URLSearchParams();

      if(media.url){
        query.set('media_url', media.url);
      }

      if(media.type){
        query.set('media_type', media.type);
      }

      location.href =
        '/detail-page/' +
        encodeURIComponent(found.number) +
        (query.toString()
          ? '?' + query.toString()
          : '');
    },
    true
  );
})();
</script>'''

    @app.middleware("http")
    async def inject_detail_click(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if not (
            path.startswith("/subpages/")
            or path.startswith("/subpage/")
        ):
            return response

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return HTMLResponse(
                body,
                status_code=response.status_code,
                headers={
                    key: value
                    for key, value in response.headers.items()
                    if key.lower() not in {"content-length", "content-encoding"}
                },
                background=response.background,
            )

        if "infini-detail-swipe-inject-v1" not in text:
            if "</body>" in text:
                text = text.replace("</body>", injection + "</body>", 1)
            else:
                text += injection

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in {"content-length", "content-encoding"}
        }
        return HTMLResponse(
            text,
            status_code=response.status_code,
            headers=headers,
            background=response.background,
        )

    @app.get("/detail-page/{full_no}", response_class=HTMLResponse)
    def detail_page(
        full_no: str,
        media_url: str = "",
        media_type: str = "",
    ):
        with lock:
            data = load_db_unlocked()
            ensure_page_unlocked(
                data,
                full_no,
                media_url=media_url,
                media_type=media_type,
                create_missing=True,
            )
            save_db_unlocked(data)
        return HTMLResponse(html)

    @app.get("/api/detail-page/{full_no}")
    def detail_data(
        full_no: str,
        media_url: str = "",
        media_type: str = "",
    ):
        with lock:
            data = load_db_unlocked()
            group, _, active_index = ensure_page_unlocked(
                data,
                full_no,
                media_url=media_url,
                media_type=media_type,
                create_missing=True,
            )
            save_db_unlocked(data)
            return JSONResponse(public_group(group, active_index))

    @app.post("/api/detail-page/register")
    def register_page(body: RegisterIn):
        with lock:
            data = load_db_unlocked()
            group, _, active_index = ensure_page_unlocked(
                data,
                body.full_no,
                media_url=body.media_url,
                media_type=body.media_type,
                create_missing=True,
            )
            save_db_unlocked(data)
            return JSONResponse(public_group(group, active_index))

    @app.post("/api/detail-group/{group_no}/add")
    def add_detail_page(group_no: str):
        group_no = clean_group_no(group_no)
        with lock:
            data = load_db_unlocked()
            group = ensure_group_unlocked(data, group_no)
            if len(group["pages"]) >= 50:
                raise HTTPException(400, "เพิ่มได้สูงสุด 50 หน้าในชุดนี้")
            index = len(group["pages"]) + 1
            page = normalize_page({}, group_no, index)
            group["pages"].append(page)
            group["updated_at"] = now()
            save_db_unlocked(data)
            return JSONResponse(
                {
                    "ok": True,
                    "created_no": page["no"],
                    "group": public_group(group, index - 1),
                }
            )

    @app.patch("/api/detail-page/{full_no}/detail")
    def save_detail(full_no: str, body: DetailTextIn):
        with lock:
            data = load_db_unlocked()
            group, page, active_index = ensure_page_unlocked(
                data, full_no, create_missing=False
            )
            page["detail"] = (body.detail or "")[:5000]
            page["updated_at"] = now()
            save_db_unlocked(data)
            return JSONResponse(public_group(group, active_index))

    @app.patch("/api/detail-page/{full_no}/zone")
    def save_zone(full_no: str, body: ZoneIn):
        zone = (body.zone or "").strip()
        if zone not in {"", "1", "2", "3", "4"}:
            raise HTTPException(400, "โซนไม่ถูกต้อง")
        with lock:
            data = load_db_unlocked()
            group, page, active_index = ensure_page_unlocked(
                data, full_no, create_missing=False
            )
            page["zone"] = zone
            page["updated_at"] = now()
            save_db_unlocked(data)
            return JSONResponse(public_group(group, active_index))

    @app.post("/api/detail-page/{full_no}/chat")
    def send_chat(full_no: str, body: ChatIn):
        text = (body.text or "").strip()
        if not text:
            raise HTTPException(400, "กรุณาพิมพ์ข้อความ")
        with lock:
            data = load_db_unlocked()
            group, page, active_index = ensure_page_unlocked(
                data, full_no, create_missing=False
            )
            page["messages"].append(
                {
                    "id": "msg_" + uuid.uuid4().hex[:10],
                    "text": text[:1000],
                    "created_at": now(),
                }
            )
            page["messages"] = page["messages"][-200:]
            page["updated_at"] = now()
            save_db_unlocked(data)
            return JSONResponse(public_group(group, active_index))

    @app.post("/api/detail-page/{full_no}/upload")
    def upload_detail_media(
        full_no: str,
        file: UploadFile = File(...),
    ):
        original = Path(file.filename or "upload.bin")
        extension = original.suffix.lower()
        allowed = {
            ".png", ".jpg", ".jpeg", ".webp", ".gif",
            ".mp4", ".webm", ".mov", ".m4v",
        }
        if extension not in allowed:
            raise HTTPException(400, "รองรับเฉพาะรูปหรือวิดีโอ")

        name = f"detail_{now()}_{uuid.uuid4().hex[:10]}{extension}"
        destination = scoped_upload_dir(base) / name
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        content_type = (
            file.content_type
            or mimetypes.guess_type(name)[0]
            or ""
        ).lower()
        media_type = "video" if content_type.startswith("video/") else "image"

        with lock:
            data = load_db_unlocked()
            group, page, active_index = ensure_page_unlocked(
                data, full_no, create_missing=False
            )
            page["media_url"] = scoped_upload_url(name)
            page["media_type"] = media_type
            page["updated_at"] = now()
            save_db_unlocked(data)

            # หน้าแรกของชุด เช่น 7.1.1 ต้องเป็นภาพของช่อง no.7.1
            # ในหน้ากริด Subpage ด้วย ไม่แยกเก็บคนละฐานข้อมูลอีกต่อไป
            sync_parent_thumbnail(
                full_no,
                page["media_url"],
                page["media_type"],
            )

            return JSONResponse(public_group(group, active_index))
