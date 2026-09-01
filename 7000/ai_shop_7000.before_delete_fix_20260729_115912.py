from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
import uuid
import json

AI_SHOP_DIR = Path("ai_shop_uploads")
AI_SHOP_STATE = Path("ai_shop_state.json")

AI_SHOP_HTML = r'''
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>AI จัดร้าน</title>
<style>
*{box-sizing:border-box}
html,body{
  margin:0;
  background:#050100;
  color:white;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
body{overflow-x:hidden}
.page{
  min-height:100vh;
  padding-bottom:130px;
  background:radial-gradient(circle at top,#1b0900,#050100 48%,#000);
}
.topbar{
  position:sticky;
  top:0;
  z-index:50;
  height:58px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:0 14px;
  background:rgba(0,0,0,.9);
  border-bottom:1px solid rgba(255,132,0,.35);
}
.brand{
  color:#ff8a1c;
  font-weight:1000;
  letter-spacing:.12em;
  font-size:14px;
}
.btn,label.btn{
  border:1px solid rgba(255,132,0,.62);
  background:rgba(0,0,0,.78);
  color:#ffc17d;
  border-radius:999px;
  padding:10px 14px;
  font-size:13px;
  font-weight:900;
  text-decoration:none;
  display:inline-flex;
  align-items:center;
  justify-content:center;
}
.btn.orange{
  background:#ff9a1f;
  color:#050505;
  border:0;
}
input[type=file]{display:none}
.section{padding:14px}
.card{
  border:1px solid rgba(255,132,0,.28);
  background:rgba(8,8,8,.92);
  border-radius:24px;
  padding:16px;
  margin-bottom:14px;
}
h1,h2,h3{margin:0}
h1{
  font-size:34px;
  color:#ff9a2c;
  letter-spacing:.06em;
}
h2{
  color:#ff9a2c;
  font-size:21px;
  margin-bottom:12px;
}
.label{
  color:#aaa;
  font-size:12px;
  display:block;
  margin:9px 0 6px;
}
.input,select,textarea{
  width:100%;
  border:1px solid rgba(255,255,255,.12);
  background:#080808;
  color:white;
  border-radius:15px;
  padding:12px;
  font-size:14px;
  outline:none;
}
textarea{min-height:76px;resize:vertical}
.grid2{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
}
.upload-preview{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:10px;
  margin-top:12px;
}
.thumb{
  aspect-ratio:1/1;
  border-radius:16px;
  overflow:hidden;
  background:#111;
  border:1px solid rgba(255,132,0,.25);
}
.thumb img,.thumb video{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;
}
.action-row{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
  margin-top:12px;
}
.preview{
  border-radius:28px;
  border:1px solid rgba(255,132,0,.45);
  background:#050505;
  overflow:hidden;
  min-height:360px;
}
.shop-poster{
  padding:18px;
  background:
    linear-gradient(to bottom,rgba(0,0,0,.15),rgba(0,0,0,.9)),
    radial-gradient(circle at top,#351500,#060606 72%);
}
.shop-title{
  font-size:38px;
  line-height:.95;
  font-weight:1000;
  letter-spacing:.06em;
  margin-bottom:8px;
}
.shop-sub{
  color:#c9b18e;
  font-size:14px;
  margin-bottom:14px;
}
.hero-layout{
  display:grid;
  grid-template-columns:1.5fr .9fr;
  gap:10px;
}
.hero-img{
  min-height:360px;
  border-radius:22px;
  overflow:hidden;
  border:1px solid rgba(255,132,0,.36);
  background:#111;
}
.hero-img img,.hero-img video{
  width:100%;
  height:100%;
  min-height:360px;
  object-fit:cover;
  display:block;
}
.info-panel{
  border-radius:22px;
  border:1px solid rgba(255,132,0,.34);
  padding:14px;
  background:rgba(0,0,0,.55);
}
.price{
  color:#ffbd62;
  font-size:32px;
  font-weight:1000;
  margin:8px 0 14px;
}
.spec{
  border-top:1px solid rgba(255,132,0,.22);
  padding:11px 0;
  color:#ddd;
  font-size:14px;
}
.small-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
  margin-top:10px;
}
.small-img{
  aspect-ratio:1/1;
  border-radius:18px;
  overflow:hidden;
  background:#111;
  border:1px solid rgba(255,132,0,.28);
}
.small-img img,.small-img video{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;
}
.badges{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:8px;
  margin-top:14px;
}
.badge{
  border:1px solid rgba(255,132,0,.25);
  border-radius:16px;
  padding:12px 8px;
  text-align:center;
  color:#e8cfa8;
  background:rgba(255,132,0,.06);
  font-size:12px;
}
.gallery-layout{
  padding:18px;
}
.gallery-head{
  margin-bottom:16px;
}
.gallery-head h1{
  font-size:34px;
}
.gallery-grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:12px;
}
.gallery-item{
  border-radius:22px;
  overflow:hidden;
  background:#111;
  border:1px solid rgba(255,132,0,.32);
}
.gallery-item .media{
  aspect-ratio:1/1.15;
}
.gallery-item img,.gallery-item video{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;
}
.gallery-cap{
  padding:12px;
  background:linear-gradient(to bottom,rgba(0,0,0,.2),rgba(0,0,0,.88));
}
.gallery-cap b{
  display:block;
  font-size:18px;
}
.gallery-cap span{
  color:#aaa;
  font-size:12px;
}
.full-shop{
  min-height:760px;
  padding:18px;
  display:flex;
  flex-direction:column;
  justify-content:flex-end;
  background:
    linear-gradient(to top,rgba(0,0,0,.92),rgba(0,0,0,.1)),
    radial-gradient(circle at top,#3a1a00,#050505 70%);
}
.full-shop .wall{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:8px;
  margin:16px 0;
}
.full-shop .wall .small-img{
  aspect-ratio:.78/1;
}
.empty{
  min-height:360px;
  display:flex;
  align-items:center;
  justify-content:center;
  text-align:center;
  color:#777;
  padding:20px;
}
@media(max-width:520px){
  .hero-layout{grid-template-columns:1fr}
  .info-panel{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .price{font-size:28px}
  .shop-title{font-size:34px}
}
</style>
</head>
<body>
<div class="page">
  <div class="topbar">
    <a class="btn" href="/id-home">← ID</a>
    <div class="brand">AI จัดร้าน</div>
    <a class="btn" href="/">Creative เดิม</a>
  </div>

  <div class="section">
    <div class="card">
      <h1>AI SHOP ARRANGE</h1>
      <div class="label">อัปโหลดรูปสินค้า / รูปร้าน / รูปตัวอย่าง หลายรูป</div>
      <label class="btn orange">
        + เลือกรูปหลายรูป
        <input id="fileInput" type="file" accept="image/*,video/*" multiple>
      </label>

      <div class="upload-preview" id="uploadPreview"></div>
    </div>

    <div class="card">
      <h2>ตั้งค่าหน้าร้าน</h2>

      <div class="grid2">
        <div>
          <label class="label">ชื่อร้าน</label>
          <input class="input" id="shopName" placeholder="เช่น GOODRICH MARKET">
        </div>
        <div>
          <label class="label">ราคา / เริ่มต้น</label>
          <input class="input" id="price" placeholder="เช่น เริ่มต้น 150.-">
        </div>
      </div>

      <label class="label">หมวด / คำโปรย</label>
      <input class="input" id="subtitle" placeholder="เช่น vintage jacket / second hand / AI shop">

      <div class="grid2">
        <div>
          <label class="label">โหมดจัดร้าน</label>
          <select id="mode">
            <option value="poster">แผ่นขายสินค้าเดี่ยว</option>
            <option value="gallery">แกลเลอรีหลายชิ้น</option>
            <option value="fullshop">หน้าร้านเต็ม / ตึก / โชว์รูม</option>
          </select>
        </div>
        <div>
          <label class="label">โทน</label>
          <select id="tone">
            <option value="gold">ดำทอง หรู</option>
            <option value="neon">นีออน ล้ำ</option>
            <option value="vintage">วินเทจ อบอุ่น</option>
          </select>
        </div>
      </div>

      <label class="label">รายละเอียด / คำสั่งให้ AI จัด</label>
      <textarea id="prompt" placeholder="เช่น เรียงสินค้าให้ดูแพง ทำเป็นร้านวินเทจ มีรูปใหญ่หนึ่งช่อง รูปย่อยหลายช่อง"></textarea>

      <div class="action-row">
        <button class="btn orange" onclick="arrangeShop()">AI จัดร้าน</button>
        <button class="btn" onclick="saveShop()">บันทึกหน้านี้</button>
      </div>
    </div>

    <div class="card">
      <h2>ผลลัพธ์</h2>
      <div class="preview" id="result">
        <div class="empty">อัปโหลดรูป แล้วกด “AI จัดร้าน”</div>
      </div>
    </div>
  </div>
</div>

<script>
let STATE = {
  images: [],
  shopName: "",
  price: "",
  subtitle: "",
  mode: "poster",
  tone: "gold",
  prompt: ""
};

function mediaEl(item){
  let el;
  if(String(item.type||"").startsWith("video")){
    el = document.createElement("video");
    el.controls = true;
    el.loop = true;
    el.muted = true;
    el.playsInline = true;
  }else{
    el = document.createElement("img");
  }
  el.src = item.src;
  return el;
}

function uploadFile(file){
  const form = new FormData();
  form.append("file", file);
  return fetch("/api/ai-shop/upload",{method:"POST",body:form}).then(r=>r.json());
}

function renderUploads(){
  const box = document.getElementById("uploadPreview");
  box.innerHTML = "";
  STATE.images.forEach((item,i)=>{
    const t = document.createElement("div");
    t.className = "thumb";
    t.title = "รูป " + (i+1);
    t.appendChild(mediaEl(item));
    box.appendChild(t);
  });
}

document.getElementById("fileInput").addEventListener("change", async e=>{
  const files = [...e.target.files];
  if(!files.length) return;

  for(const file of files){
    const res = await uploadFile(file);
    if(res.ok){
      STATE.images.push({src:res.url+"?t="+Date.now(), type:res.type});
    }
  }
  renderUploads();
  await saveShop(false);
});

function syncForm(){
  STATE.shopName = document.getElementById("shopName").value || "CREATIVE SHOP";
  STATE.price = document.getElementById("price").value || "ราคา / สอบถาม";
  STATE.subtitle = document.getElementById("subtitle").value || "curated by INFINI";
  STATE.mode = document.getElementById("mode").value;
  STATE.tone = document.getElementById("tone").value;
  STATE.prompt = document.getElementById("prompt").value || "";
}

function imgHTML(item, cls=""){
  if(!item) return `<div class="${cls}"></div>`;
  if(String(item.type||"").startsWith("video")){
    return `<video class="${cls}" src="${item.src}" controls muted loop playsinline></video>`;
  }
  return `<img class="${cls}" src="${item.src}">`;
}

function arrangeShop(){
  syncForm();

  const result = document.getElementById("result");
  const imgs = STATE.images;

  if(!imgs.length){
    result.innerHTML = `<div class="empty">ยังไม่มีรูป ให้กดเลือกรูปก่อน</div>`;
    return;
  }

  if(STATE.mode === "gallery"){
    result.innerHTML = `
      <div class="gallery-layout">
        <div class="gallery-head">
          <h1>${STATE.shopName}</h1>
          <div class="shop-sub">${STATE.subtitle}</div>
        </div>
        <div class="gallery-grid">
          ${imgs.map((x,i)=>`
            <div class="gallery-item">
              <div class="media">${imgHTML(x)}</div>
              <div class="gallery-cap">
                <b>ITEM ${i+1}</b>
                <span>${STATE.price}</span>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
    return;
  }

  if(STATE.mode === "fullshop"){
    result.innerHTML = `
      <div class="full-shop">
        <div class="shop-title">${STATE.shopName}</div>
        <div class="shop-sub">${STATE.subtitle}</div>
        <div class="wall">
          ${imgs.slice(0,9).map(x=>`<div class="small-img">${imgHTML(x)}</div>`).join("")}
        </div>
        <div class="badges">
          <div class="badge">จัดร้านอัตโนมัติ</div>
          <div class="badge">หลายรูป</div>
          <div class="badge">พร้อมขาย</div>
        </div>
      </div>
    `;
    return;
  }

  const hero = imgs[0];
  const smalls = imgs.slice(1,5);

  result.innerHTML = `
    <div class="shop-poster">
      <div class="shop-title">${STATE.shopName}</div>
      <div class="shop-sub">${STATE.subtitle}</div>

      <div class="hero-layout">
        <div class="hero-img">${imgHTML(hero)}</div>
        <div class="info-panel">
          <div style="color:#c9b18e">ราคา</div>
          <div class="price">${STATE.price}</div>
          <div class="spec">สภาพ: พร้อมใช้งาน / พร้อมโชว์</div>
          <div class="spec">โทน: ${STATE.tone}</div>
          <div class="spec">AI Prompt: ${STATE.prompt || "จัดให้ดูแพงและอ่านง่าย"}</div>
        </div>
      </div>

      <div class="small-grid">
        ${smalls.map(x=>`<div class="small-img">${imgHTML(x)}</div>`).join("")}
      </div>

      <div class="badges">
        <div class="badge">รูปใหญ่</div>
        <div class="badge">รูปย่อย</div>
        <div class="badge">จัดอัตโนมัติ</div>
      </div>
    </div>
  `;
}

async function saveShop(showAlert=true){
  syncForm();
  await fetch("/api/ai-shop/state",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(STATE)
  });
  if(showAlert) alert("บันทึกแล้ว");
}

function loadShop(){
  fetch("/api/ai-shop/state?t="+Date.now())
    .then(r=>r.json())
    .then(d=>{
      if(d && Object.keys(d).length){
        STATE = Object.assign(STATE,d);
        document.getElementById("shopName").value = STATE.shopName || "";
        document.getElementById("price").value = STATE.price || "";
        document.getElementById("subtitle").value = STATE.subtitle || "";
        document.getElementById("mode").value = STATE.mode || "poster";
        document.getElementById("tone").value = STATE.tone || "gold";
        document.getElementById("prompt").value = STATE.prompt || "";
        renderUploads();
        if(STATE.images && STATE.images.length) arrangeShop();
      }
    });
}

loadShop();
</script>
</body>
</html>
'''

def install_ai_shop_7000(app: FastAPI):
    @app.post("/api/ai-shop/upload")
    async def ai_shop_upload(file: UploadFile = File(...)):
        AI_SHOP_DIR.mkdir(exist_ok=True)

        content_type = file.content_type or "application/octet-stream"
        ext = Path(file.filename or "").suffix.lower()

        if not ext:
            if content_type.startswith("image/"):
                ext = ".jpg"
            elif content_type.startswith("video/"):
                ext = ".mp4"
            else:
                ext = ".bin"

        name = f"{uuid.uuid4().hex}{ext}"
        out = AI_SHOP_DIR / name
        out.write_bytes(await file.read())

        return JSONResponse({
            "ok": True,
            "url": f"/ai-shop-media/{name}",
            "type": content_type
        })

    @app.get("/ai-shop-media/{name}")
    async def ai_shop_media(name: str):
        path = AI_SHOP_DIR / name
        if not path.exists():
            return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
        return FileResponse(path)

    @app.get("/api/ai-shop/state")
    async def ai_shop_get_state():
        if not AI_SHOP_STATE.exists():
            return JSONResponse({})
        try:
            return JSONResponse(json.loads(AI_SHOP_STATE.read_text(encoding="utf-8")))
        except Exception:
            return JSONResponse({})

    @app.post("/api/ai-shop/state")
    async def ai_shop_save_state(request: Request):
        try:
            data = await request.json()
            AI_SHOP_STATE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return JSONResponse({"ok": True})
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    @app.get("/ai-shop", response_class=HTMLResponse)
    async def ai_shop_page():
        return HTMLResponse(AI_SHOP_HTML)
