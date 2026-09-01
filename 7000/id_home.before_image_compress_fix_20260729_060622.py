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
    min-height:100%;
    background:#050505;
    color:#fff;
    font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }

  body{
    overflow:hidden;
  }

  .swipe-wrap{
    width:100vw;
    height:100vh;
    overflow-x:auto;
    overflow-y:hidden;
    display:flex;
    scroll-snap-type:x mandatory;
    scroll-behavior:smooth;
    -webkit-overflow-scrolling:touch;
  }

  .page{
    min-width:100vw;
    height:100vh;
    overflow-y:auto;
    scroll-snap-align:start;
    background:
      radial-gradient(circle at top,#1e1307 0,#070707 38%,#020202 100%);
  }

  .topbar{
    position:sticky;
    top:0;
    z-index:20;
    height:52px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 14px;
    background:rgba(0,0,0,.72);
    backdrop-filter:blur(12px);
    border-bottom:1px solid rgba(255,132,0,.28);
  }

  .brand{
    font-weight:900;
    letter-spacing:.12em;
    color:#ff8a1c;
    font-size:14px;
  }

  .hint{
    font-size:11px;
    color:#aaa;
  }

  .hero{
    width:100%;
    min-height:46vh;
    background:#111;
    border-bottom:1px solid rgba(255,132,0,.25);
    position:relative;
    overflow:hidden;
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
    padding:22px;
    color:#777;
    background:
      linear-gradient(135deg,rgba(255,132,0,.16),rgba(0,0,0,.2)),
      radial-gradient(circle at center,#1a1a1a,#050505);
  }

  .upload-hero{
    position:absolute;
    right:14px;
    bottom:14px;
    z-index:5;
  }

  .pill-btn{
    border:1px solid rgba(255,132,0,.6);
    background:rgba(0,0,0,.68);
    color:#fff;
    border-radius:999px;
    padding:10px 14px;
    font-weight:800;
    font-size:13px;
  }

  input[type=file]{display:none}

  .section{
    padding:14px;
  }

  .card{
    border:1px solid rgba(255,132,0,.28);
    background:rgba(11,11,11,.82);
    border-radius:22px;
    padding:14px;
    margin-bottom:14px;
    box-shadow:0 12px 35px rgba(0,0,0,.35);
  }

  .card-title{
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:12px;
    gap:10px;
  }

  .card-title h2{
    margin:0;
    font-size:17px;
    color:#ff9a2c;
  }

  .small-action{
    border:1px solid rgba(255,132,0,.45);
    background:#130b04;
    color:#ffc17d;
    border-radius:999px;
    padding:7px 10px;
    font-size:12px;
    white-space:nowrap;
  }

  .grid2{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
  }

  .input{
    width:100%;
    border:1px solid rgba(255,255,255,.12);
    background:#080808;
    color:#fff;
    border-radius:14px;
    padding:12px;
    font-size:14px;
    outline:none;
  }

  textarea.input{
    min-height:86px;
    resize:vertical;
  }

  .label{
    display:block;
    margin:8px 0 6px;
    color:#bdbdbd;
    font-size:12px;
  }

  .chat-grid{
    display:grid;
    grid-template-columns:1fr;
    gap:14px;
  }

  .chat-box{
    min-height:190px;
    border-radius:20px;
    background:#080808;
    border:1px solid rgba(255,255,255,.1);
    overflow:hidden;
  }

  .chat-head{
    height:46px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 12px;
    border-bottom:1px solid rgba(255,255,255,.08);
    background:rgba(255,132,0,.08);
  }

  .chat-head b{
    color:#fff;
    font-size:14px;
  }

  .chat-body{
    padding:12px;
    color:#aaa;
    font-size:13px;
    line-height:1.55;
  }

  .chat-input-row{
    display:flex;
    gap:8px;
    padding:10px;
    border-top:1px solid rgba(255,255,255,.08);
  }

  .chat-input-row input{
    flex:1;
  }

  .send{
    border:0;
    background:#ff8a1c;
    color:#000;
    border-radius:12px;
    padding:0 14px;
    font-weight:900;
  }

  .creative-entry{
    display:block;
    text-decoration:none;
    color:#fff;
    border-radius:24px;
    padding:18px;
    background:
      linear-gradient(135deg,rgba(255,132,0,.28),rgba(255,132,0,.05)),
      #080808;
    border:1px solid rgba(255,132,0,.45);
  }

  .creative-entry h2{
    margin:0 0 8px;
    color:#ff9a2c;
    font-size:22px;
  }

  .creative-entry p{
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
    padding:12px;
    background:#090909;
    border:1px solid rgba(255,255,255,.1);
  }

  .zone b{
    color:#ff9a2c;
    display:block;
    margin-bottom:5px;
  }

  .zone span{
    color:#aaa;
    font-size:12px;
  }

  .gallery-grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:8px;
  }

  .gallery-cell{
    aspect-ratio:1/1;
    border-radius:14px;
    background:#111;
    border:1px solid rgba(255,255,255,.1);
    overflow:hidden;
    display:flex;
    align-items:center;
    justify-content:center;
    color:#666;
    font-size:12px;
  }

  .gallery-cell img{
    width:100%;
    height:100%;
    object-fit:cover;
  }

  .creative-page{
    background:
      radial-gradient(circle at top,#251000 0,#070707 42%,#000 100%);
    padding-bottom:40px;
  }

  .creative-cover{
    margin:14px;
    min-height:42vh;
    border-radius:28px;
    border:1px solid rgba(255,132,0,.45);
    background:
      linear-gradient(135deg,rgba(255,132,0,.24),rgba(255,255,255,.03)),
      #090909;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:24px;
  }

  .creative-cover h1{
    margin:0;
    color:#ff8a1c;
    font-size:34px;
    letter-spacing:.08em;
  }

  .creative-cover p{
    color:#bbb;
    max-width:320px;
  }

  .back-id{
    display:inline-flex;
    margin:14px;
    text-decoration:none;
    color:#ffc17d;
    border:1px solid rgba(255,132,0,.45);
    border-radius:999px;
    padding:10px 14px;
    background:#0a0a0a;
  }

  .save-note{
    margin-top:8px;
    color:#777;
    font-size:11px;
  }

  @media(min-width:720px){
    .chat-grid{grid-template-columns:1fr 1fr}
    .gallery-grid{grid-template-columns:repeat(4,1fr)}
  }
</style>
</head>

<body>
<div class="swipe-wrap" id="swipeWrap">

  <!-- PAGE 1: ID HOME -->
  <section class="page" id="idHomePage">
    <div class="topbar">
      <div class="brand">INFINI ID HOME</div>
      <div class="hint">ปัดซ้าย → Creative Room</div>
    </div>

    <div class="hero" id="heroBox">
      <div class="hero-empty" id="heroEmpty">
        <div>
          <div style="font-size:28px;margin-bottom:8px;">＋</div>
          <b>อัปโหลดรูปหน้าปก ID แบบเต็ม</b>
          <div style="font-size:12px;margin-top:8px;">รูปนี้คือพื้นที่บนสุดของเจ้าของ ID</div>
        </div>
      </div>
      <label class="upload-hero pill-btn">
        อัปโหลดรูป
        <input id="coverInput" type="file" accept="image/*,video/*">
      </label>
    </div>

    <div class="section">

      <div class="card">
        <div class="card-title">
          <h2>รายละเอียดเจ้าของ ID</h2>
          <button class="small-action" onclick="saveProfile()">บันทึก</button>
        </div>

        <div class="grid2">
          <div>
            <label class="label">ชื่อแสดงผล</label>
            <input class="input" id="displayName" placeholder="เช่น Simon">
          </div>
          <div>
            <label class="label">username</label>
            <input class="input" id="username" placeholder="@infini">
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
        <textarea class="input" id="bio" placeholder="เขียนรายละเอียดของตนเอง ร้าน หรือสิ่งที่อยากให้คนเห็น"></textarea>

        <div class="save-note">ข้อมูลหน้านี้เก็บในเครื่องก่อน สำหรับ MVP ทดสอบ</div>
      </div>

      <div class="chat-grid">

        <div class="card">
          <div class="card-title">
            <h2>แชท AI</h2>
            <button class="small-action" onclick="toggleApi()">API ส่วนตัว</button>
          </div>

          <div id="apiBox" style="display:none;margin-bottom:12px;">
            <label class="label">Private AI API Key</label>
            <input class="input" id="privateApi" type="password" placeholder="ใส่ API ส่วนตัวของเจ้าของ ID">
          </div>

          <div class="chat-box">
            <div class="chat-head">
              <b>AI ของเจ้าของ ID</b>
              <span style="color:#ff9a2c;font-size:12px;">API</span>
            </div>
            <div class="chat-body" id="aiChatBody">
              ช่องนี้ไว้คุยกับ AI ประจำ ID ของตัวเอง
            </div>
            <div class="chat-input-row">
              <input class="input" id="aiText" placeholder="พิมพ์หา AI">
              <button class="send" onclick="fakeSend('ai')">ส่ง</button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">
            <h2>แชทเพื่อน</h2>
            <button class="small-action" onclick="toggleFriends()">รวมเพื่อน</button>
          </div>

          <div id="friendsBox" style="display:none;margin-bottom:12px;">
            <label class="label">รายชื่อเพื่อน / กลุ่มเจ้าของ ID</label>
            <textarea class="input" id="friendsList" placeholder="เช่น เพื่อน A, เพื่อน B, กลุ่มลูกค้า, กลุ่มทีมงาน"></textarea>
          </div>

          <div class="chat-box">
            <div class="chat-head">
              <b>Friend Chat</b>
              <span style="color:#ff9a2c;font-size:12px;">FRIENDS</span>
            </div>
            <div class="chat-body" id="friendChatBody">
              ช่องนี้ไว้รวมแชทเพื่อนของเจ้าของ ID
            </div>
            <div class="chat-input-row">
              <input class="input" id="friendText" placeholder="พิมพ์หาเพื่อน">
              <button class="send" onclick="fakeSend('friend')">ส่ง</button>
            </div>
          </div>
        </div>

      </div>

      <div class="card">
        <a class="creative-entry" href="#creativeRoomPage" onclick="goCreative()">
          <h2>CREATIVE ROOM</h2>
          <p>เข้าไปสร้างงาน / จัดร้าน / เลือกโซน / คลังภาพ</p>
        </a>
      </div>

      <div class="card">
        <div class="card-title">
          <h2>เลือกโซน 4 โซน</h2>
        </div>
        <div class="zones">
          <div class="zone"><b>ZONE 1</b><span>โชว์ผลงาน / Gallery</span></div>
          <div class="zone"><b>ZONE 2</b><span>ร้านค้า / Shop</span></div>
          <div class="zone"><b>ZONE 3</b><span>บริการ / Service</span></div>
          <div class="zone"><b>ZONE 4</b><span>ชุมชน / Friend / Fan</span></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <h2>คลังภาพ</h2>
          <label class="small-action">
            เพิ่มรูป
            <input id="galleryInput" type="file" accept="image/*" multiple>
          </label>
        </div>
        <div class="gallery-grid" id="galleryGrid">
          <div class="gallery-cell">รูป 1</div>
          <div class="gallery-cell">รูป 2</div>
          <div class="gallery-cell">รูป 3</div>
          <div class="gallery-cell">รูป 4</div>
          <div class="gallery-cell">รูป 5</div>
          <div class="gallery-cell">รูป 6</div>
        </div>
      </div>

    </div>
  </section>

  <!-- PAGE 2: CREATIVE ROOM -->
  <section class="page creative-page" id="creativeRoomPage">
    <div class="topbar">
      <div class="brand">CREATIVE ROOM</div>
      <div class="hint">← ปัดกลับ ID Home</div>
    </div>

    <a class="back-id" href="#idHomePage" onclick="goId()">← กลับ ID Home</a>

    <div class="creative-cover">
      <h1>CREATIVE ROOM</h1>
      <p>หน้านี้คือห้องสร้างสรรค์ ถัดจาก ID Home สำหรับต่อเข้าระบบจัดร้าน จัดโซน อัปโหลด และเลือกพื้นที่ทำงาน</p>
    </div>

    <div class="section">
      <div class="card">
        <div class="card-title">
          <h2>ทางเข้าโซนสร้างงาน</h2>
        </div>
        <div class="zones">
          <div class="zone"><b>Gallery Zone</b><span>ลงรูปผลงาน</span></div>
          <div class="zone"><b>Shop Zone</b><span>จัดร้าน / ขายของ</span></div>
          <div class="zone"><b>AI Shop Zone</b><span>ให้ AI จัดร้าน</span></div>
          <div class="zone"><b>Space Zone</b><span>พื้นที่สร้างเอง</span></div>
        </div>
      </div>
    </div>
  </section>

</div>

<script>
const LS_KEY = "INF_ID_HOME_V1";

function loadState(){
  try{return JSON.parse(localStorage.getItem(LS_KEY)||"{}")}catch(e){return {}}
}

function saveState(data){
  localStorage.setItem(LS_KEY, JSON.stringify(data||{}));
}

function saveProfile(){
  const data = loadState();
  data.displayName = document.getElementById("displayName").value;
  data.username = document.getElementById("username").value;
  data.infiniId = document.getElementById("infiniId").value;
  data.level = document.getElementById("level").value;
  data.bio = document.getElementById("bio").value;
  data.privateApi = document.getElementById("privateApi").value;
  data.friendsList = document.getElementById("friendsList").value;
  saveState(data);
  alert("บันทึกแล้ว");
}

function restore(){
  const data = loadState();
  ["displayName","username","infiniId","level","bio","privateApi","friendsList"].forEach(id=>{
    const el=document.getElementById(id);
    if(el && data[id]) el.value=data[id];
  });
  if(data.cover) renderCover(data.cover, data.coverType || "image");
  if(Array.isArray(data.gallery)) renderGallery(data.gallery);
}

function renderCover(src,type){
  const hero=document.getElementById("heroBox");
  const old=document.getElementById("heroMedia");
  if(old) old.remove();
  document.getElementById("heroEmpty").style.display="none";

  let el;
  if(String(type).startsWith("video")){
    el=document.createElement("video");
    el.controls=true;
    el.autoplay=true;
    el.muted=true;
    el.loop=true;
  }else{
    el=document.createElement("img");
  }
  el.id="heroMedia";
  el.src=src;
  hero.insertBefore(el, hero.firstChild);
}

document.getElementById("coverInput").addEventListener("change", e=>{
  const file=e.target.files[0];
  if(!file) return;
  const reader=new FileReader();
  reader.onload=()=>{
    const data=loadState();
    data.cover=reader.result;
    data.coverType=file.type || "image";
    saveState(data);
    renderCover(reader.result, file.type);
  };
  reader.readAsDataURL(file);
});

function renderGallery(items){
  const grid=document.getElementById("galleryGrid");
  grid.innerHTML="";
  items.forEach(src=>{
    const cell=document.createElement("div");
    cell.className="gallery-cell";
    const img=document.createElement("img");
    img.src=src;
    cell.appendChild(img);
    grid.appendChild(cell);
  });
  while(grid.children.length < 6){
    const cell=document.createElement("div");
    cell.className="gallery-cell";
    cell.textContent="รูป "+(grid.children.length+1);
    grid.appendChild(cell);
  }
}

document.getElementById("galleryInput").addEventListener("change", e=>{
  const files=[...e.target.files];
  const data=loadState();
  data.gallery=data.gallery || [];
  let left=files.length;
  if(left===0) return;
  files.forEach(file=>{
    const reader=new FileReader();
    reader.onload=()=>{
      data.gallery.push(reader.result);
      left--;
      if(left===0){
        saveState(data);
        renderGallery(data.gallery);
      }
    };
    reader.readAsDataURL(file);
  });
});

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
    const body=document.getElementById("aiChatBody");
    if(input.value.trim()){
      body.innerHTML += "<br><br><b style='color:#ff9a2c'>คุณ:</b> "+escapeHtml(input.value);
      body.innerHTML += "<br><b>AI:</b> รับข้อความแล้ว ขั้นต่อไปค่อยเชื่อม API ส่วนตัว";
      input.value="";
    }
  }else{
    const input=document.getElementById("friendText");
    const body=document.getElementById("friendChatBody");
    if(input.value.trim()){
      body.innerHTML += "<br><br><b style='color:#ff9a2c'>คุณ:</b> "+escapeHtml(input.value);
      body.innerHTML += "<br><b>ระบบ:</b> รับข้อความแล้ว ขั้นต่อไปค่อยเชื่อมเพื่อนจริง";
      input.value="";
    }
  }
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, m => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[m]));
}

function goCreative(){
  document.getElementById("creativeRoomPage").scrollIntoView({behavior:"smooth",inline:"start"});
}

function goId(){
  document.getElementById("idHomePage").scrollIntoView({behavior:"smooth",inline:"start"});
}

restore();
</script>

<!-- INF_ID_LONGPRESS_SEARCH_V1 -->
<style id="INF_ID_LONGPRESS_SEARCH_V1_STYLE">
  .id-search-btn{
    border:1px solid rgba(255,132,0,.5);
    background:#120a03;
    color:#ffc17d;
    border-radius:999px;
    padding:7px 11px;
    font-size:12px;
    font-weight:800;
    margin-left:8px;
  }

  .editable-hold{
    position:relative;
  }

  .editable-hold::after{
    content:"กดค้างเพื่ออัปโหลด";
    position:absolute;
    left:10px;
    bottom:10px;
    z-index:4;
    font-size:10px;
    padding:5px 8px;
    border-radius:999px;
    color:#ffc17d;
    background:rgba(0,0,0,.55);
    border:1px solid rgba(255,132,0,.35);
    opacity:.55;
    pointer-events:none;
  }

  .hold-upload-layer{
    position:fixed;
    inset:0;
    z-index:9998;
    background:rgba(0,0,0,.72);
    display:none;
    align-items:flex-end;
    justify-content:center;
    padding:16px;
  }

  .hold-upload-panel{
    width:100%;
    max-width:520px;
    border-radius:26px;
    border:1px solid rgba(255,132,0,.45);
    background:#070707;
    color:white;
    padding:16px;
    box-shadow:0 20px 60px rgba(0,0,0,.65);
  }

  .hold-upload-panel h3{
    margin:0 0 8px;
    color:#ff9a2c;
  }

  .hold-upload-panel p{
    margin:0 0 14px;
    color:#aaa;
    font-size:13px;
  }

  .hold-actions{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
  }

  .hold-actions label,
  .hold-actions button{
    border:1px solid rgba(255,132,0,.45);
    background:#140b04;
    color:#fff;
    border-radius:16px;
    min-height:48px;
    font-weight:900;
    display:flex;
    align-items:center;
    justify-content:center;
  }

  .hold-actions button{
    background:#111;
  }

  .hold-actions input{
    display:none;
  }

  .slot-media{
    width:100%;
    height:100%;
    object-fit:cover;
    display:block;
    border-radius:inherit;
  }

  .id-web-overlay{
    position:fixed;
    inset:0;
    z-index:9999;
    background:#030303;
    display:none;
    flex-direction:column;
  }

  .id-web-search-top{
    height:64px;
    min-height:64px;
    display:flex;
    gap:8px;
    align-items:center;
    padding:10px;
    background:rgba(0,0,0,.92);
    border-bottom:1px solid rgba(255,132,0,.35);
  }

  .id-web-search-top input{
    flex:1;
    height:44px;
    border-radius:999px;
    border:1px solid rgba(255,132,0,.45);
    background:#090909;
    color:white;
    padding:0 14px;
    outline:none;
    font-size:14px;
  }

  .id-web-search-top button{
    height:44px;
    border-radius:999px;
    border:1px solid rgba(255,132,0,.5);
    background:#ff8a1c;
    color:#000;
    font-weight:900;
    padding:0 14px;
  }

  .id-web-search-top .close-web{
    background:#111;
    color:#ffc17d;
  }

  .id-web-frame{
    flex:1;
    width:100%;
    border:0;
    background:#fff;
  }

  .search-empty{
    flex:1;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:#888;
    padding:24px;
  }
</style>

<div class="hold-upload-layer" id="holdUploadLayer">
  <div class="hold-upload-panel">
    <h3>อัปโหลดใส่ช่องนี้</h3>
    <p>กดเลือกรูปหรือวิดีโอ แล้วระบบจะวางลงช่องที่กดค้างไว้</p>
    <div class="hold-actions">
      <label>
        รูป / วิดีโอ
        <input id="holdUploadInput" type="file" accept="image/*,video/*">
      </label>
      <button type="button" onclick="closeHoldUpload()">ปิด</button>
    </div>
  </div>
</div>

<div class="id-web-overlay" id="idWebOverlay">
  <div class="id-web-search-top">
    <input id="idWebSearchInput" placeholder="ค้นหาเว็บ..." autocomplete="off">
    <button type="button" onclick="runIdWebSearch()">ค้นหา</button>
    <button type="button" class="close-web" onclick="closeIdWebSearch()">ปิด</button>
  </div>
  <div class="search-empty" id="searchEmpty">
    พิมพ์คำค้นหาด้านบน แล้วกดค้นหา
  </div>
  <iframe class="id-web-frame" id="idWebFrame" style="display:none;"></iframe>
</div>

<script id="INF_ID_LONGPRESS_SEARCH_V1">
(function(){
  const STORE_KEY = "INF_ID_LONGPRESS_MEDIA_V1";
  let activeTarget = null;
  let holdTimer = null;

  function loadMedia(){
    try{return JSON.parse(localStorage.getItem(STORE_KEY)||"{}")}catch(e){return {}}
  }

  function saveMedia(data){
    localStorage.setItem(STORE_KEY, JSON.stringify(data||{}));
  }

  function getTargetKey(el){
    if(!el.dataset.holdKey){
      const all = [...document.querySelectorAll(".editable-hold")];
      el.dataset.holdKey = "hold_slot_" + all.indexOf(el);
    }
    return el.dataset.holdKey;
  }

  function renderInto(el, src, type){
    el.classList.add("editable-hold");
    el.innerHTML = "";

    let media;
    if(String(type||"").startsWith("video")){
      media = document.createElement("video");
      media.controls = true;
      media.loop = true;
      media.muted = true;
      media.playsInline = true;
    }else{
      media = document.createElement("img");
    }

    media.className = "slot-media";
    media.src = src;
    el.appendChild(media);
  }

  function restoreAll(){
    const data = loadMedia();
    document.querySelectorAll(".editable-hold").forEach(el=>{
      const key = getTargetKey(el);
      if(data[key]){
        renderInto(el, data[key].src, data[key].type);
      }
    });
  }

  function openHoldUpload(el){
    activeTarget = el;
    document.getElementById("holdUploadLayer").style.display = "flex";
  }

  window.closeHoldUpload = function(){
    document.getElementById("holdUploadLayer").style.display = "none";
    activeTarget = null;
  }

  function bindHold(el){
    el.classList.add("editable-hold");
    getTargetKey(el);

    el.addEventListener("touchstart", function(e){
      holdTimer = setTimeout(()=>openHoldUpload(el), 650);
    }, {passive:true});

    el.addEventListener("touchend", function(){
      clearTimeout(holdTimer);
    });

    el.addEventListener("touchmove", function(){
      clearTimeout(holdTimer);
    });

    el.addEventListener("mousedown", function(){
      holdTimer = setTimeout(()=>openHoldUpload(el), 650);
    });

    el.addEventListener("mouseup", function(){
      clearTimeout(holdTimer);
    });

    el.addEventListener("mouseleave", function(){
      clearTimeout(holdTimer);
    });
  }

  function initEditable(){
    const targets = [
      ".hero",
      ".creative-cover",
      ".creative-entry",
      ".zone",
      ".gallery-cell"
    ];

    document.querySelectorAll(targets.join(",")).forEach(bindHold);
    restoreAll();
  }

  document.getElementById("holdUploadInput").addEventListener("change", function(e){
    const file = e.target.files && e.target.files[0];
    if(!file || !activeTarget) return;

    const reader = new FileReader();
    reader.onload = function(){
      const data = loadMedia();
      const key = getTargetKey(activeTarget);
      data[key] = {
        src: reader.result,
        type: file.type || "image"
      };
      saveMedia(data);
      renderInto(activeTarget, reader.result, file.type);
      closeHoldUpload();
      e.target.value = "";
    };
    reader.readAsDataURL(file);
  });

  function addSearchButton(){
    document.querySelectorAll(".topbar").forEach(bar=>{
      if(bar.querySelector(".id-search-btn")) return;
      const btn = document.createElement("button");
      btn.className = "id-search-btn";
      btn.type = "button";
      btn.textContent = "ค้นหา";
      btn.onclick = openIdWebSearch;

      const hint = bar.querySelector(".hint");
      if(hint){
        hint.parentNode.insertBefore(btn, hint.nextSibling);
      }else{
        bar.appendChild(btn);
      }
    });
  }

  window.openIdWebSearch = function(){
    document.getElementById("idWebOverlay").style.display = "flex";
    setTimeout(()=>document.getElementById("idWebSearchInput").focus(), 80);
  }

  window.closeIdWebSearch = function(){
    document.getElementById("idWebOverlay").style.display = "none";
  }

  window.runIdWebSearch = function(){
    const q = document.getElementById("idWebSearchInput").value.trim();
    if(!q) return;

    const frame = document.getElementById("idWebFrame");
    const empty = document.getElementById("searchEmpty");

    empty.style.display = "none";
    frame.style.display = "block";

    // ใช้ google igu เพื่อให้มีโอกาสแสดงใน iframe ได้มากขึ้น
    frame.src = "https://www.google.com/search?igu=1&q=" + encodeURIComponent(q);
  }

  document.getElementById("idWebSearchInput").addEventListener("keydown", function(e){
    if(e.key === "Enter") runIdWebSearch();
  });

  addSearchButton();
  initEditable();

  setInterval(function(){
    addSearchButton();
    document.querySelectorAll(".zone,.gallery-cell,.creative-cover,.creative-entry,.hero").forEach(el=>{
      if(!el.classList.contains("editable-hold")) bindHold(el);
    });
  }, 1500);
})();
</script>


<!-- INF_ID_BACK_SWIPE_V1 -->
<style id="INF_ID_BACK_SWIPE_V1_STYLE">
  .floating-id-back{
    position:fixed;
    left:14px;
    bottom:18px;
    z-index:9997;
    border:1px solid rgba(255,132,0,.55);
    background:rgba(0,0,0,.78);
    color:#ffc17d;
    border-radius:999px;
    padding:11px 14px;
    font-size:13px;
    font-weight:900;
    box-shadow:0 12px 32px rgba(0,0,0,.45);
    display:none;
  }

  .swipe-back-hint{
    position:fixed;
    left:50%;
    bottom:76px;
    transform:translateX(-50%);
    z-index:9997;
    background:rgba(0,0,0,.7);
    border:1px solid rgba(255,132,0,.35);
    color:#ffc17d;
    border-radius:999px;
    padding:8px 12px;
    font-size:11px;
    display:none;
    pointer-events:none;
  }
</style>

<button class="floating-id-back" id="floatingIdBack" type="button" onclick="forceGoIdHome()">← ID HOME</button>
<div class="swipe-back-hint" id="swipeBackHint">ปัดขวาเพื่อกลับ ID Home</div>

<script id="INF_ID_BACK_SWIPE_V1">
(function(){
  let startX = 0;
  let startY = 0;
  let startTime = 0;

  function getWrap(){
    return document.getElementById("swipeWrap");
  }

  window.forceGoIdHome = function(){
    const wrap = getWrap();
    const idPage = document.getElementById("idHomePage");
    if(wrap){
      wrap.scrollTo({left:0, behavior:"smooth"});
    }
    if(idPage){
      idPage.scrollIntoView({behavior:"smooth", inline:"start"});
    }
    location.hash = "idHomePage";
  }

  function isCreativeVisible(){
    const wrap = getWrap();
    if(!wrap) return false;
    return wrap.scrollLeft > window.innerWidth * 0.45;
  }

  function updateBackUI(){
    const btn = document.getElementById("floatingIdBack");
    const hint = document.getElementById("swipeBackHint");
    const show = isCreativeVisible();

    if(btn) btn.style.display = show ? "block" : "none";

    if(hint){
      hint.style.display = show ? "block" : "none";
      if(show){
        clearTimeout(hint._timer);
        hint._timer = setTimeout(()=>{ hint.style.display="none"; }, 1800);
      }
    }
  }

  document.addEventListener("touchstart", function(e){
    if(!isCreativeVisible()) return;
    const t = e.touches && e.touches[0];
    if(!t) return;
    startX = t.clientX;
    startY = t.clientY;
    startTime = Date.now();
  }, {passive:true});

  document.addEventListener("touchend", function(e){
    if(!isCreativeVisible()) return;
    const t = e.changedTouches && e.changedTouches[0];
    if(!t) return;

    const dx = t.clientX - startX;
    const dy = Math.abs(t.clientY - startY);
    const dt = Date.now() - startTime;

    // อยู่หน้า Creative แล้วปัดจากซ้ายไปขวา = กลับ ID Home
    if(dx > 70 && dy < 90 && dt < 900){
      forceGoIdHome();
    }
  }, {passive:true});

  const wrap = getWrap();
  if(wrap){
    wrap.addEventListener("scroll", updateBackUI, {passive:true});
  }

  setInterval(updateBackUI, 700);

  // กันปุ่มเดิมใช้ไม่ได้: บังคับลิงก์กลับทุกตัวที่ href ไป idHomePage
  document.addEventListener("click", function(e){
    const a = e.target.closest && e.target.closest('a[href="#idHomePage"]');
    if(a){
      e.preventDefault();
      forceGoIdHome();
    }
  });
})();
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
