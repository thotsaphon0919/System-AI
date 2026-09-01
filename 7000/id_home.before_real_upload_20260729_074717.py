from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ID_HOME_HTML = r'''
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>INFINI ID HOME</title>

<style>
*{box-sizing:border-box}
html,body{
  margin:0;
  width:100%;
  height:100%;
  background:#050100;
  color:#fff;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
body{overflow:hidden}

.swipe-wrap{
  width:100vw;
  height:100vh;
  display:flex;
  overflow-x:hidden;
  overflow-y:hidden;
  scroll-behavior:smooth;
}

.page{
  min-width:100vw;
  height:100vh;
  overflow-y:auto;
  background:radial-gradient(circle at top,#1c0900,#050100 48%,#000);
}

.topbar{
  position:sticky;
  top:0;
  z-index:50;
  height:58px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 14px;
  background:rgba(0,0,0,.86);
  border-bottom:1px solid rgba(255,132,0,.35);
  backdrop-filter:blur(10px);
}

.brand{
  color:#ff8a1c;
  font-weight:900;
  letter-spacing:.12em;
  font-size:14px;
}

.hint{
  color:#aaa;
  font-size:12px;
}

.btn{
  border:1px solid rgba(255,132,0,.6);
  background:rgba(0,0,0,.72);
  color:#ffc17d;
  border-radius:999px;
  padding:9px 13px;
  font-size:13px;
  font-weight:900;
}

.btn.orange{
  background:#ff9a1f;
  color:#050505;
  border:0;
}

input[type=file]{display:none}

.hero{
  height:46vh;
  min-height:46vh;
  position:relative;
  overflow:hidden;
  background:#111;
  border-bottom:1px solid rgba(255,132,0,.3);
}

.hero img,.hero video{
  width:100%;
  height:46vh;
  object-fit:cover;
  display:block;
}

.hero-empty{
  height:46vh;
  display:flex;
  align-items:center;
  justify-content:center;
  text-align:center;
  color:#777;
  background:radial-gradient(circle at center,#1b1b1b,#050505);
}

.upload-float{
  position:absolute;
  right:16px;
  bottom:16px;
  z-index:5;
}

.section{padding:14px}

.card{
  border:1px solid rgba(255,132,0,.28);
  background:rgba(8,8,8,.88);
  border-radius:24px;
  padding:16px;
  margin-bottom:14px;
}

.card-title{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  margin-bottom:12px;
}

.card-title h2{
  margin:0;
  color:#ff9a2c;
  font-size:20px;
}

.grid2{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
}

.label{
  display:block;
  color:#aaa;
  font-size:12px;
  margin:8px 0 6px;
}

.input{
  width:100%;
  border:1px solid rgba(255,255,255,.12);
  background:#080808;
  color:white;
  border-radius:15px;
  padding:12px;
  font-size:14px;
  outline:none;
}

textarea.input{
  min-height:86px;
  resize:vertical;
}

.chat-grid{
  display:grid;
  grid-template-columns:1fr;
  gap:14px;
}

.chat-box{
  min-height:170px;
  border-radius:20px;
  border:1px solid rgba(255,255,255,.1);
  background:#070707;
  overflow:hidden;
}

.chat-head{
  height:44px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 12px;
  background:rgba(255,132,0,.08);
  border-bottom:1px solid rgba(255,255,255,.08);
}

.chat-body{
  padding:12px;
  color:#aaa;
  font-size:13px;
  line-height:1.5;
}

.chat-row{
  display:flex;
  gap:8px;
  padding:10px;
  border-top:1px solid rgba(255,255,255,.08);
}

.chat-row input{flex:1}

.creative-card{
  min-height:190px;
  display:flex;
  flex-direction:column;
  justify-content:flex-end;
  border-radius:24px;
  padding:18px;
  border:1px solid rgba(255,132,0,.45);
  background:
    linear-gradient(to top,rgba(0,0,0,.9),rgba(0,0,0,.15)),
    radial-gradient(circle at top,#341300,#080808 70%);
  cursor:pointer;
}

.creative-card h2{
  margin:0 0 8px;
  color:#ff9a2c;
  font-size:30px;
  letter-spacing:.08em;
}

.creative-card p{
  margin:0;
  color:#bbb;
  font-size:13px;
}

.zones{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
}

.zone{
  min-height:96px;
  border-radius:18px;
  padding:13px;
  border:1px solid rgba(255,255,255,.1);
  background:#090909;
}

.zone b{
  color:#ff9a2c;
  display:block;
  margin-bottom:6px;
}

.zone span{
  color:#aaa;
  font-size:12px;
}

.gallery-grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:10px;
}

.gallery-cell{
  aspect-ratio:1/1;
  border-radius:18px;
  border:1px solid rgba(255,255,255,.1);
  background:#111;
  overflow:hidden;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#666;
  font-size:12px;
}

.gallery-cell img,.gallery-cell video{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;
}

/* PAGE 2: GATE */
.gate-card{
  margin:14px;
  min-height:86vh;
  border-radius:30px;
  border:1px solid rgba(255,132,0,.62);
  background:#050505;
  overflow:hidden;
  position:relative;
  box-shadow:0 22px 70px rgba(0,0,0,.65);
}

.gate-empty{
  min-height:86vh;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  text-align:center;
  padding:24px;
  background:
    linear-gradient(to top,rgba(0,0,0,.92),rgba(0,0,0,.18)),
    radial-gradient(circle at top,#301400,#050505 70%);
}

.gate-empty h1{
  margin:0 0 10px;
  color:#ff9a2c;
  font-size:40px;
  letter-spacing:.08em;
}

.gate-empty p{
  margin:0;
  color:#aaa;
}

.gate-card img,.gate-card video{
  width:100%;
  height:86vh;
  min-height:86vh;
  object-fit:cover;
  display:block;
}

.gate-actions{
  position:absolute;
  left:14px;
  right:14px;
  bottom:16px;
  z-index:20;
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
}

.gate-actions label,.gate-actions button{
  min-height:56px;
  display:flex;
  align-items:center;
  justify-content:center;
  border-radius:999px;
  border:1px solid rgba(255,132,0,.65);
  background:rgba(0,0,0,.78);
  color:#ffc17d;
  font-weight:900;
  font-size:14px;
}

/* PAGE 3: CREATIVE ROOM */
.room-box{
  margin:14px;
  border-radius:28px;
  border:1px solid rgba(255,132,0,.45);
  background:#070707;
  padding:18px;
}

.room-title{
  font-size:42px;
  line-height:.95;
  font-weight:1000;
  margin:10px 0 20px;
  color:white;
}

.room-cover{
  min-height:58vh;
  border-radius:24px;
  border:1px solid rgba(255,132,0,.35);
  background:#111;
  overflow:hidden;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#777;
  text-align:center;
  position:relative;
}

.room-cover img,.room-cover video{
  width:100%;
  height:58vh;
  object-fit:cover;
  display:block;
}

.room-plus{
  width:100%;
  margin-top:14px;
  min-height:72px;
  border-radius:999px;
  border:0;
  background:#ffad25;
  color:#050505;
  font-size:42px;
  font-weight:1000;
}

.web-overlay{
  position:fixed;
  inset:0;
  z-index:99999;
  display:none;
  flex-direction:column;
  background:#030303;
}

.web-top{
  height:64px;
  min-height:64px;
  display:flex;
  gap:8px;
  padding:10px;
  border-bottom:1px solid rgba(255,132,0,.35);
  background:rgba(0,0,0,.94);
}

.web-top input{
  flex:1;
  border-radius:999px;
  border:1px solid rgba(255,132,0,.5);
  background:#080808;
  color:white;
  padding:0 14px;
  outline:none;
}

.web-top button{
  border-radius:999px;
  border:1px solid rgba(255,132,0,.5);
  background:#ff9a1f;
  color:#000;
  font-weight:900;
  padding:0 14px;
}

.web-frame{
  flex:1;
  border:0;
  width:100%;
  background:white;
}

@media(min-width:720px){
  .chat-grid{grid-template-columns:1fr 1fr}
  .gallery-grid{grid-template-columns:repeat(4,1fr)}
}
</style>

<style id="INF_TOWER_UPLOAD_SIZE_FIX">
  #creativeGatePage .gate-card{
    min-height:88vh !important;
    height:88vh !important;
  }

  #creativeGatePage .gate-card img,
  #creativeGatePage .gate-card video{
    width:100% !important;
    height:88vh !important;
    min-height:88vh !important;
    object-fit:cover !important;
    object-position:center center !important;
    display:block !important;
  }

  #creativeGatePage .gate-empty{
    min-height:88vh !important;
  }
</style>

</head>

<body>
<div class="swipe-wrap" id="swipeWrap">

  <!-- PAGE 1: ID HOME -->
  <section class="page" id="idHomePage">
    <div class="topbar">
      <div class="brand">INFINI ID HOME</div>
      <div class="hint">กด Creative → เข้าตึก</div>
      <button class="btn" onclick="openSearch()">ค้นหา</button>
    </div>

    <div class="hero" id="idCoverBox">
      <div class="hero-empty" id="idCoverEmpty">
        <div>
          <div style="font-size:28px;">＋</div>
          <b>อัปโหลดรูปปก ID</b>
        </div>
      </div>
      <label class="btn upload-float">
        อัปโหลด
        <input id="idCoverInput" type="file" accept="image/*,video/*">
      </label>
    </div>

    <div class="section">

      <div class="card">
        <div class="card-title">
          <h2>รายละเอียดเจ้าของ ID</h2>
          <button class="btn" onclick="saveProfile()">บันทึก</button>
        </div>

        <div class="grid2">
          <div>
            <label class="label">ชื่อแสดงผล</label>
            <input class="input" id="displayName" placeholder="SIMONLAENG">
          </div>
          <div>
            <label class="label">username</label>
            <input class="input" id="username" placeholder="Simonlaeng">
          </div>
          <div>
            <label class="label">INFINI ID</label>
            <input class="input" id="infiniId" placeholder="INF-000001">
          </div>
          <div>
            <label class="label">สถานะ / เลเวล</label>
            <input class="input" id="level" placeholder="Creator / Member">
          </div>
        </div>

        <label class="label">คำอธิบายตัวเอง / ร้าน / โปรเจกต์</label>
        <textarea class="input" id="bio" placeholder="เขียนรายละเอียดของตัวเอง"></textarea>
      </div>

      <div class="chat-grid">
        <div class="card">
          <div class="card-title">
            <h2>แชท AI</h2>
            <button class="btn" onclick="toggleApi()">API</button>
          </div>
          <div id="apiBox" style="display:none;margin-bottom:12px;">
            <input class="input" id="privateApi" type="password" placeholder="API ส่วนตัว">
          </div>
          <div class="chat-box">
            <div class="chat-head"><b>AI Chat</b><span>API</span></div>
            <div class="chat-body" id="aiBody">ช่องคุยกับ AI ประจำ ID</div>
            <div class="chat-row">
              <input class="input" id="aiText" placeholder="พิมพ์หา AI">
              <button class="btn orange" onclick="fakeSend('ai')">ส่ง</button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">
            <h2>แชทเพื่อน</h2>
            <button class="btn" onclick="toggleFriends()">เพื่อน</button>
          </div>
          <div id="friendsBox" style="display:none;margin-bottom:12px;">
            <textarea class="input" id="friendsList" placeholder="รวมเพื่อน / กลุ่ม"></textarea>
          </div>
          <div class="chat-box">
            <div class="chat-head"><b>Friend Chat</b><span>FRIENDS</span></div>
            <div class="chat-body" id="friendBody">ช่องรวมเพื่อนของเจ้าของ ID</div>
            <div class="chat-row">
              <input class="input" id="friendText" placeholder="พิมพ์หาเพื่อน">
              <button class="btn orange" onclick="fakeSend('friend')">ส่ง</button>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="creative-card" onclick="goGate()">
          <h2>CREATIVE ROOM</h2>
          <p>กดเพื่อไปหน้าตึกก่อน แล้วค่อยเข้าห้อง Creative</p>
        </div>
      </div>

      <div class="card">
        <div class="card-title"><h2>เลือกโซน 4 โซน</h2></div>
        <div class="zones">
          <div class="zone"><b>ZONE 1</b><span>Gallery</span></div>
          <div class="zone"><b>ZONE 2</b><span>Shop</span></div>
          <div class="zone"><b>ZONE 3</b><span>Service</span></div>
          <div class="zone"><b>ZONE 4</b><span>Friend / Fan</span></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <h2>คลังภาพ</h2>
          <label class="btn">เพิ่มรูป<input id="galleryInput" type="file" accept="image/*,video/*" multiple></label>
        </div>
        <div class="gallery-grid" id="galleryGrid">
          <div class="gallery-cell">รูป 1</div>
          <div class="gallery-cell">รูป 2</div>
          <div class="gallery-cell">รูป 3</div>
          <div class="gallery-cell">รูป 4</div>
        </div>
      </div>

    </div>
  </section>

  <!-- PAGE 2: CREATIVE GATE -->
  <section class="page" id="creativeGatePage">
    <div class="topbar">
      <button class="btn" onclick="goId()">← ID Home</button>
      <div class="brand">CREATIVE GATE</div>
      <button class="btn" onclick="openSearch()">ค้นหา</button>
    </div>

    <div class="gate-card" id="gateCard">
      <div class="gate-empty" id="gateEmpty">
        <h1>CREATIVE<br>GATE</h1>
        <p>อัปโหลดรูปตึก / Space Box / ประตูเข้า Creative Room</p>
      </div>

      <div class="gate-actions">
        <label>อัปโหลดรูปตึก<input id="gateInput" type="file" accept="image/*,video/*"></label>
        <button class="orange" onclick="goRoom()">เข้าตึก</button>
      </div>
    </div>
  </section>

  <!-- PAGE 3: CREATIVE ROOM เดิม -->
  <section class="page" id="creativeRoomPage">
    <div class="topbar">
      <div class="brand">CREATIVE ROOM</div>
      <button class="btn" onclick="goGate()">← กลับตึก</button>
      <button class="btn" onclick="openSearch()">ค้นหา</button>
    </div>

    <div class="room-box">
      <button class="btn" onclick="goId()">← กลับ ID Home</button>
      <div class="room-title">CREATIVE<br>ROOM</div>

      <div class="room-cover" id="roomCover">
        <div id="roomEmpty">อัปโหลดรูปห้อง / ผลงาน / พื้นที่สร้างงาน</div>
      </div>

      <label>
        <button class="room-plus" type="button" onclick="document.getElementById('roomInput').click()">+</button>
        <input id="roomInput" type="file" accept="image/*,video/*">
      </label>
    </div>
  </section>

</div>

<div class="web-overlay" id="webOverlay">
  <div class="web-top">
    <input id="webInput" placeholder="ค้นหาเว็บ...">
    <button onclick="runSearch()">ค้นหา</button>
    <button onclick="closeSearch()">ปิด</button>
  </div>
  <iframe class="web-frame" id="webFrame"></iframe>
</div>

<script>
const STORE = "INF_ID_HOME_CLEAN_V8";

function data(){
  try{return JSON.parse(localStorage.getItem(STORE)||"{}")}catch(e){return {}}
}
function save(d){localStorage.setItem(STORE, JSON.stringify(d||{}))}

function mediaEl(src,type){
  let el;
  if(String(type||"").startsWith("video")){
    el=document.createElement("video");
    el.controls=true; el.loop=true; el.muted=true; el.playsInline=true;
  }else{
    el=document.createElement("img");
  }
  el.src=src;
  return el;
}

function setBox(boxId, emptyId, src, type){
  const box=document.getElementById(boxId);
  const empty=document.getElementById(emptyId);
  if(!box) return;
  box.querySelectorAll("img,video").forEach(x=>x.remove());
  if(empty) empty.style.display="none";
  box.insertBefore(mediaEl(src,type), box.firstChild);
}

function readFile(file, cb){
  if(!file) return;

  // วิดีโอปล่อยตรงก่อน
  if(!String(file.type || "").startsWith("image/")){
    const reader = new FileReader();
    reader.onload = () => cb(reader.result, file.type || "video");
    reader.readAsDataURL(file);
    return;
  }

  // บีบรูปใหญ่ให้ใช้กับหน้า Gate / รูปตึกแนวตั้งได้
  const img = new Image();
  const url = URL.createObjectURL(file);

  img.onload = function(){
    try{
      let w = img.naturalWidth || img.width;
      let h = img.naturalHeight || img.height;

      // เหมาะกับรูปตึกแนวตั้ง 9:16 / 4:5 / poster
      const maxW = 1400;
      const maxH = 2400;

      const scale = Math.min(1, maxW / w, maxH / h);
      w = Math.round(w * scale);
      h = Math.round(h * scale);

      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);

      // แปลงเป็น jpg เพื่อลดขนาด ไม่งั้น localStorage เต็ม
      const dataUrl = canvas.toDataURL("image/jpeg", 0.86);

      URL.revokeObjectURL(url);
      cb(dataUrl, "image/jpeg");
    }catch(e){
      URL.revokeObjectURL(url);
      const reader = new FileReader();
      reader.onload = () => cb(reader.result, file.type || "image");
      reader.readAsDataURL(file);
    }
  };

  img.onerror = function(){
    URL.revokeObjectURL(url);
    const reader = new FileReader();
    reader.onload = () => cb(reader.result, file.type || "image");
    reader.readAsDataURL(file);
  };

  img.src = url;
}

function goPage(n){
  document.getElementById("swipeWrap").scrollTo({left:window.innerWidth*n, behavior:"smooth"});
}
function goId(){goPage(0); history.replaceState(null,"","#idHome")}
function goGate(){goPage(1); history.replaceState(null,"","#creativeGate")}
function goRoom(){ window.location.href="/"; }

function saveProfile(){
  const d=data();
  ["displayName","username","infiniId","level","bio","privateApi","friendsList"].forEach(id=>{
    const el=document.getElementById(id);
    if(el) d[id]=el.value;
  });
  save(d);
  alert("บันทึกแล้ว");
}

function restore(){
  const d=data();
  ["displayName","username","infiniId","level","bio","privateApi","friendsList"].forEach(id=>{
    const el=document.getElementById(id);
    if(el && d[id]) el.value=d[id];
  });
  if(d.idCover) setBox("idCoverBox","idCoverEmpty",d.idCover.src,d.idCover.type);
  if(d.gate) setBox("gateCard","gateEmpty",d.gate.src,d.gate.type);
  if(d.room) setBox("roomCover","roomEmpty",d.room.src,d.room.type);
  renderGallery(d.gallery || []);
}

document.getElementById("idCoverInput").onchange=e=>{
  const file=e.target.files[0];
  readFile(file,(src,type)=>{
    const d=data(); d.idCover={src,type}; save(d);
    setBox("idCoverBox","idCoverEmpty",src,type);
  });
};

document.getElementById("gateInput").onchange=e=>{
  const file=e.target.files[0];
  readFile(file,(src,type)=>{
    const d=data(); d.gate={src,type}; save(d);
    setBox("gateCard","gateEmpty",src,type);
  });
};

document.getElementById("roomInput").onchange=e=>{
  const file=e.target.files[0];
  readFile(file,(src,type)=>{
    const d=data(); d.room={src,type}; save(d);
    setBox("roomCover","roomEmpty",src,type);
  });
};

function renderGallery(items){
  const grid=document.getElementById("galleryGrid");
  grid.innerHTML="";
  items.forEach(item=>{
    const cell=document.createElement("div");
    cell.className="gallery-cell";
    cell.appendChild(mediaEl(item.src,item.type));
    grid.appendChild(cell);
  });
  while(grid.children.length<4){
    const cell=document.createElement("div");
    cell.className="gallery-cell";
    cell.textContent="รูป "+(grid.children.length+1);
    grid.appendChild(cell);
  }
}

document.getElementById("galleryInput").onchange=e=>{
  const files=[...e.target.files];
  const d=data(); d.gallery=d.gallery || [];
  let left=files.length;
  if(!left) return;
  files.forEach(file=>{
    readFile(file,(src,type)=>{
      d.gallery.push({src,type});
      left--;
      if(left===0){save(d); renderGallery(d.gallery)}
    });
  });
};

function toggleApi(){
  const box=document.getElementById("apiBox");
  box.style.display = box.style.display==="none" ? "block" : "none";
}
function toggleFriends(){
  const box=document.getElementById("friendsBox");
  box.style.display = box.style.display==="none" ? "block" : "none";
}
function fakeSend(type){
  if(type==="ai"){
    const input=document.getElementById("aiText");
    const body=document.getElementById("aiBody");
    if(input.value.trim()){
      body.innerHTML += "<br><br><b style='color:#ff9a2c'>คุณ:</b> "+input.value;
      body.innerHTML += "<br><b>AI:</b> รับข้อความแล้ว";
      input.value="";
    }
  }else{
    const input=document.getElementById("friendText");
    const body=document.getElementById("friendBody");
    if(input.value.trim()){
      body.innerHTML += "<br><br><b style='color:#ff9a2c'>คุณ:</b> "+input.value;
      body.innerHTML += "<br><b>ระบบ:</b> รับข้อความแล้ว";
      input.value="";
    }
  }
}

function openSearch(){
  document.getElementById("webOverlay").style.display="flex";
  setTimeout(()=>document.getElementById("webInput").focus(),80);
}
function closeSearch(){
  document.getElementById("webOverlay").style.display="none";
}
function runSearch(){
  const q=document.getElementById("webInput").value.trim();
  if(!q) return;
  document.getElementById("webFrame").src="https://www.google.com/search?igu=1&q="+encodeURIComponent(q);
}
document.getElementById("webInput").addEventListener("keydown",e=>{
  if(e.key==="Enter") runSearch();
});

/* swipe gesture */
let sx=0, sy=0, st=0;
document.addEventListener("touchstart",e=>{
  const t=e.touches[0]; sx=t.clientX; sy=t.clientY; st=Date.now();
},{passive:true});
document.addEventListener("touchend",e=>{
  const t=e.changedTouches[0];
  const dx=t.clientX-sx, dy=Math.abs(t.clientY-sy), dt=Date.now()-st;
  if(Math.abs(dx)<70 || dy>100 || dt>1000) return;
  const wrap=document.getElementById("swipeWrap");
  const page=Math.round(wrap.scrollLeft/window.innerWidth);
  if(dx<0 && page<2) goPage(page+1);
  if(dx>0 && page>0) goPage(page-1);
},{passive:true});

restore();
</script>
</body>
</html>
'''

def install_id_home(app: FastAPI):
    @app.get("/id-home", response_class=HTMLResponse)
    async def id_home():
        return HTMLResponse(ID_HOME_HTML)

    @app.get("/id", response_class=HTMLResponse)
    async def id_home_short():
        return HTMLResponse(ID_HOME_HTML)
