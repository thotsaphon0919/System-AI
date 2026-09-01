from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json, uuid, shutil

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "remote_sheet_data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_FILE = DATA_DIR / "sheets.json"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

def load_data():
    if not DATA_FILE.exists():
        data = {
            "sheets": [{
                "id": "home",
                "title": "INFINI REMOTE",
                "description": "กดค้างเพื่อแก้ไข",
                "cards": []
            }]
        }
        save_data(data)
        return data
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_data(data):
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def find_sheet(data, sheet_id):
    for sheet in data["sheets"]:
        if sheet["id"] == sheet_id:
            return sheet
    raise HTTPException(404, "ไม่พบแผ่น")

def find_card(sheet, card_id):
    for card in sheet["cards"]:
        if card["id"] == card_id:
            return card
    raise HTTPException(404, "ไม่พบช่อง")
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json, uuid, shutil

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "remote_sheet_data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_FILE = DATA_DIR / "sheets.json"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

def load_data():
    if not DATA_FILE.exists():
        data = {
            "sheets": [{
                "id": "home",
                "title": "INFINI REMOTE",
                "description": "กดค้างเพื่อแก้ไข",
                "cards": []
            }]
        }
        save_data(data)
        return data
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_data(data):
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def find_sheet(data, sheet_id):
    for sheet in data["sheets"]:
        if sheet["id"] == sheet_id:
            return sheet
    raise HTTPException(404, "ไม่พบแผ่น")

def find_card(sheet, card_id):
    for card in sheet["cards"]:
        if card["id"] == card_id:
            return card
    raise HTTPException(404, "ไม่พบช่อง")
HTML = """
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>INFINI REMOTE</title>
<style>
*{box-sizing:border-box}
body{
  margin:0;
  background:#06101c;
  color:white;
  font-family:system-ui,sans-serif;
}
header{
  position:sticky;
  top:0;
  z-index:10;
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:14px;
  background:#091522;
  border-bottom:1px solid #20364f;
}
button{
  border:0;
  border-radius:12px;
  padding:10px 14px;
  background:#32c7ff;
  color:#04101a;
  font-weight:700;
}
.note{
  padding:10px 14px;
  text-align:center;
  color:#9eb4c9;
  font-size:13px;
}
.deck{
  display:flex;
  overflow-x:auto;
  scroll-snap-type:x mandatory;
}
.sheet{
  min-width:100vw;
  scroll-snap-align:start;
  padding:16px;
}
.sheet-head{
  padding:20px;
  border:1px solid #20364f;
  border-radius:20px;
  background:#0d1d2e;
  margin-bottom:14px;
}
.grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:12px;
}
.card{
  min-height:220px;
  border-radius:18px;
  overflow:hidden;
  border:1px solid #20364f;
  background:#0d1a29;
}
.media{
  height:135px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#13283e;
  color:#8fa8bd;
  font-size:12px;
}
.media img,.media video{
  width:100%;
  height:100%;
  object-fit:cover;
}
.card-body{
  padding:12px;
}
.card h3{
  margin:0 0 6px;
}
.card p{
  margin:0 0 10px;
  color:#9eb4c9;
  font-size:13px;
}
.card a{
  display:block;
  text-decoration:none;
  text-align:center;
  padding:9px;
  border-radius:10px;
  background:#17304a;
  color:white;
}
.overlay{
  position:fixed;
  inset:0;
  display:none;
  align-items:flex-end;
  background:rgba(0,0,0,.65);
  z-index:99;
}
.overlay.open{display:flex}
.drawer{
  width:100%;
  max-height:90vh;
  overflow:auto;
  padding:18px;
  border-radius:22px 22px 0 0;
  background:#0d1927;
}
label{
  display:block;
  margin-top:10px;
  font-size:13px;
}
input,textarea{
  width:100%;
  margin-top:5px;
  padding:11px;
  border-radius:10px;
  border:1px solid #29435f;
  background:#07121e;
  color:white;
}
textarea{min-height:80px}
.actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:14px;
}
.danger{
  background:#6b2330;
  color:white;
}
</style>
</head>
<body>

<header>
  <strong>INFINI REMOTE</strong>
  <div>
    <button onclick="addSheet()">+ แผ่น</button>
    <button onclick="openTools()">+ ช่อง</button>
  </div>
</header>

<div class="note">
ปัดซ้ายขวาเปลี่ยนแผ่น • กดค้างเพื่อแก้ไข • ไม่จำเป็นต้องกรอกครบทุกช่อง
</div>

<main id="deck" class="deck"></main>

<div id="overlay" class="overlay">
  <div class="drawer">
    <h2 id="drawerTitle">แก้ไข</h2>
    <p>ไม่จำเป็นต้องกรอกข้อมูลครบทุกช่อง อัปโหลดและบันทึกได้ทันที</p>

    <input type="hidden" id="mode">
    <input type="hidden" id="sheetId">
    <input type="hidden" id="cardId">

    <label>รูปหรือวิดีโอ
      <input id="media" type="file" accept="image/*,video/*">
    </label>

    <label>ชื่อหัวข้อ
      <input id="title">
    </label>

    <label>รายละเอียด
      <textarea id="description"></textarea>
    </label>

    <div id="cardFields">
      <label>ข้อความบนปุ่ม
        <input id="buttonText" value="เปิด">
      </label>

      <label>ลิงก์ปลายทาง
        <input id="url" placeholder="/page หรือ https://...">
      </label>
    </div>


    <div id="extraFields" style="display:none">
      <label id="priceField">ราคา
        <input id="price" placeholder="เช่น 590 บาท">
      </label>

      <label id="contactField">ข้อมูลติดต่อ
        <input id="contact" placeholder="โทรศัพท์ อีเมล หรือโซเชียล">
      </label>

      <label id="mapField">ลิงก์แผนที่
        <input id="mapUrl" placeholder="ลิงก์ตำแหน่งหรือแผนที่">
      </label>

      <label id="downloadField">ลิงก์ไฟล์ดาวน์โหลด
        <input id="downloadUrl" placeholder="ลิงก์ไฟล์">
      </label>

      <label id="sheetLinkField">เชื่อมไปยังแผ่น
        <select id="targetSheet"></select>
      </label>
    </div>

    <div class="actions">
      <button onclick="saveEdit()">บันทึก</button>
      <button onclick="duplicateCurrent()">ทำสำเนา</button>
      <button id="clearBtn" onclick="clearSheet()">เคลียร์แผ่น</button>
      <button class="danger" onclick="deleteCurrent()">ลบ</button>
      <button onclick="closeDrawer()">ปิด</button>
    </div>
  </div>
</div>
<script>

/* INFINI_RUNTIME_DIAG */
function showInfiniError(message) {
  let box = document.getElementById("infiniRuntimeError");
  if (!box) {
    box = document.createElement("pre");
    box.id = "infiniRuntimeError";
    box.style.cssText = `
      position:fixed; inset:110px 12px auto 12px; z-index:99999;
      padding:16px; border:2px solid #ff4d6d; border-radius:14px;
      background:#18070d; color:#fff; white-space:pre-wrap;
      font-size:14px; line-height:1.5;
    `;
    document.body.appendChild(box);
  }
  box.textContent = "INFINI ERROR\n\n" + message;
}

window.addEventListener("error", event => {
  showInfiniError(
    (event.message || "Unknown error") +
    "\nไฟล์: " + (event.filename || "-") +
    "\nบรรทัด: " + (event.lineno || "-") +
    ":" + (event.colno || "-")
  );
});

window.addEventListener("unhandledrejection", event => {
  showInfiniError(
    "Promise error: " +
    (event.reason?.stack || event.reason?.message || String(event.reason))
  );
});

let state = {sheets: []};
let activeIndex = 0;
let pressTimer = null;

const el = id => document.getElementById(id);

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "เกิดข้อผิดพลาด");
  }

  return data;
}

async function loadData() {
  state = await api("/api/remote-sheet");
  render();
}

function render() {
  const deck = el("deck");
  deck.innerHTML = "";

  state.sheets.forEach((sheet, index) => {
    const page = document.createElement("section");
    page.className = "sheet";

    const head = document.createElement("div");
    head.className = "sheet-head";
    head.innerHTML = `
      <h1>${escapeText(sheet.title || "แผ่นไม่มีชื่อ")}</h1>
      <p>${escapeText(sheet.description || "")}</p>
    `;

    longPress(head, () => openSheetEditor(sheet));

    const grid = document.createElement("div");
    grid.className = "grid";

    if (!sheet.cards || sheet.cards.length === 0) {
      const empty = document.createElement("div");
      empty.className = "sheet-head";
      empty.innerHTML = "กดค้างตรงนี้เพื่อเพิ่มช่องใหม่";
      longPress(empty, () => addCard(sheet.id));
      grid.appendChild(empty);
    }

    (sheet.cards || []).forEach(card => {
      const item = document.createElement("article");
      item.className = "card";

      let mediaHtml = `
        <div class="media">
          กดค้างเพื่ออัปโหลดรูปหรือวิดีโอ
        </div>
      `;

      if (card.media) {
        if (card.media_type === "video") {
          mediaHtml = `
            <div class="media">
              <video src="${card.media}" muted loop playsinline></video>
            </div>
          `;
        } else {
          mediaHtml = `
            <div class="media">
              <img src="${card.media}">
            </div>
          `;
        }
      }

      item.innerHTML = `
        ${mediaHtml}
        <div class="card-body">
          <h3>${escapeText(card.title || "ช่องไม่มีชื่อ")}</h3>
          <p>${escapeText(card.description || "")}</p>
          <a href="${escapeText(card.url || "#")}">
            ${escapeText(card.button_text || "เปิด")}
          </a>
        </div>
      `;

      const video = item.querySelector("video");
      if (video) {
        video.play().catch(() => {});
      }

      longPress(item, () => openCardEditor(sheet, card));

        item.addEventListener("click", event => {
          event.preventDefault();
          event.stopPropagation();

          if (item.dataset.longPress === "1") {
            item.dataset.longPress = "0";
            return;
          }

          openCardPreview(sheet, card);
        });

      grid.appendChild(item);
    });

    page.appendChild(head);
    page.appendChild(grid);
    deck.appendChild(page);
  });

  setTimeout(() => {
    deck.scrollLeft = activeIndex * window.innerWidth;
  }, 50);
}

el("deck").addEventListener("scroll", () => {
  activeIndex = Math.round(
    el("deck").scrollLeft / window.innerWidth
  );
});

function longPress(target, callback) {
  const start = () => {
    pressTimer = setTimeout(() => {
      pressTimer = null;
      target.dataset.longPress = "1";
      callback();
    }, 550);
  };

  const cancel = () => {
    if (pressTimer) {
      clearTimeout(pressTimer);
      pressTimer = null;
    }
  };

  target.addEventListener("pointerdown", start);
  target.addEventListener("pointerup", cancel);
  target.addEventListener("pointercancel", cancel);
  target.addEventListener("pointermove", cancel);
  target.addEventListener("contextmenu", event => {
    event.preventDefault();
  });
}



function openTargetSheet(targetSheetId) {
  const index = state.sheets.findIndex(
    sheet => String(sheet.id) === String(targetSheetId)
  );

  if (index < 0) {
    alert("ไม่พบแผ่นปลายทาง");
    return;
  }

  const preview = document.getElementById("cardPreview");
  if (preview) {
    preview.style.display = "none";
  }

  document.body.style.overflow = "";
  activeIndex = index;
  render();
}


function openCardPreview(sheet, card) {
  let preview = document.getElementById("cardPreview");

  if (!preview) {
    preview = document.createElement("div");
    preview.id = "cardPreview";
    preview.style.cssText = `
      position:fixed;
      inset:0;
      z-index:9999;
      display:none;
      overflow-y:auto;
      padding:70px 14px 32px;
      background:rgba(2,10,20,.98);
    `;

    preview.innerHTML = `
      <button id="closeCardPreview" type="button" style="
        position:fixed;
        top:16px;
        right:16px;
        z-index:10000;
        width:48px;
        height:48px;
        border:1px solid #38bdf8;
        border-radius:50%;
        background:#071525;
        color:#fff;
        font-size:30px;
      ">×</button>

      <div id="cardPreviewContent" style="
        width:min(100%,720px);
        margin:auto;
      "></div>
    `;

    document.body.appendChild(preview);

    document
      .getElementById("closeCardPreview")
      .addEventListener("click", () => {
        preview.style.display = "none";
        document.body.style.overflow = "";
      });
  }

  const ratio = String(card.ratio || "4:5").replace(":", " / ");

  let mediaHtml = `
    <div style="
      height:100%;
      display:grid;
      place-items:center;
      padding:30px;
      color:#8294aa;
      text-align:center;
    ">ยังไม่มีรูปหรือวิดีโอ</div>
  `;

  if (card.media) {
    if (card.media_type === "video") {
      mediaHtml = `
        <video
          src="${card.media}"
          controls
          playsinline
          style="width:100%;height:100%;object-fit:cover"
        ></video>
      `;
    } else {
      mediaHtml = `
        <img
          src="${card.media}"
          alt=""
          style="width:100%;height:100%;object-fit:cover"
        >
      `;
    }
  }

  let actionHtml = "";

  if (card.url) {
    actionHtml = `
      <a href="${escapeText(card.url)}" style="
        display:block;
        padding:17px;
        border-radius:16px;
        background:linear-gradient(135deg,#38bdf8,#8b5cf6);
        color:white;
        text-align:center;
        text-decoration:none;
        font-size:20px;
        font-weight:800;
      ">${escapeText(card.button_text || "เปิด")}</a>
    `;
  } else if (card.target_sheet_id) {
    actionHtml = `
      <button id="previewTargetButton" type="button" style="
        width:100%;
        border:0;
        padding:17px;
        border-radius:16px;
        background:linear-gradient(135deg,#38bdf8,#8b5cf6);
        color:white;
        font-size:20px;
        font-weight:800;
      ">${escapeText(card.button_text || "เข้าแผ่น")}</button>
    `;
  }

  document.getElementById("cardPreviewContent").innerHTML = `
    <section style="
      overflow:hidden;
      border:1px solid #274867;
      border-radius:24px;
      background:#0b1b2b;
      box-shadow:0 20px 70px rgba(0,0,0,.6);
    ">
      <div style="
        width:100%;
        aspect-ratio:${ratio};
        background:#10263a;
      ">${mediaHtml}</div>

      <div style="padding:24px">
        <div style="color:#67e8f9;margin-bottom:8px">
          ${escapeText(sheet.title || "แผ่นไม่มีชื่อ")}
        </div>

        <h1 style="
          margin:0 0 12px;
          color:white;
          font-size:clamp(30px,8vw,54px);
          line-height:1.1;
        ">${escapeText(card.title || "ช่องไม่มีชื่อ")}</h1>

        <p style="
          margin:0 0 18px;
          color:#bdcad8;
          font-size:18px;
          line-height:1.7;
          white-space:pre-wrap;
        ">${escapeText(card.description || "")}</p>

        ${card.price ? `
          <div style="
            margin-bottom:18px;
            color:#facc15;
            font-size:28px;
            font-weight:800;
          ">${escapeText(card.price)}</div>
        ` : ""}

        ${actionHtml}
      </div>
    </section>
  `;

  const targetButton = document.getElementById("previewTargetButton");
  if (targetButton) {
    targetButton.addEventListener("click", () => {
      openTargetSheet(card.target_sheet_id);
    });
  }

  preview.style.display = "block";
  document.body.style.overflow = "hidden";
}

function openSheetEditor(sheet) {
  el("mode").value = "sheet";
  el("sheetId").value = sheet.id;
  el("cardId").value = "";
  el("title").value = sheet.title || "";
  el("description").value = sheet.description || "";
  el("media").value = "";
  el("cardFields").style.display = "none";
  el("clearBtn").style.display = "inline-block";
  el("drawerTitle").textContent = "แก้ไขแผ่น";
  el("overlay").classList.add("open");
}

function openCardEditor(sheet, card) {
  el("mode").value = "card";
  el("sheetId").value = sheet.id;
  el("cardId").value = card.id;
  el("title").value = card.title || "";
  el("description").value = card.description || "";
  el("buttonText").value = card.button_text || "เปิด";
  el("url").value = card.url || "";
  el("media").value = "";
  el("cardFields").style.display = "block";
  el("clearBtn").style.display = "none";
  el("drawerTitle").textContent = "แก้ไขช่อง";

  const type = card.type || "text";
  el("extraFields").style.display = "block";

  el("priceField").style.display =
    type === "product" ? "block" : "none";

  el("contactField").style.display =
    ["contact", "profile"].includes(type) ? "block" : "none";

  el("mapField").style.display =
    type === "map" ? "block" : "none";

  el("downloadField").style.display =
    type === "download" ? "block" : "none";

  el("sheetLinkField").style.display =
    type === "sheet_link" ? "block" : "none";

  el("price").value = card.price || "";
  el("contact").value = card.contact || "";
  el("mapUrl").value = card.map_url || "";
  el("downloadUrl").value = card.download_url || "";

  el("targetSheet").innerHTML =
    '<option value="">เลือกแผ่นปลายทาง</option>' +
    state.sheets
      .filter(item => item.id !== sheet.id)
      .map(item => `
        <option value="${item.id}">
          ${escapeText(item.title || "แผ่นไม่มีชื่อ")}
        </option>
      `)
      .join("");

  el("targetSheet").value =
    card.target_sheet_id || "";

  el("overlay").classList.add("open");
}

function closeDrawer() {
  el("overlay").classList.remove("open");
}
async function saveEdit() {
  try {
    const mode = el("mode").value;
    const sheetId = el("sheetId").value;
    const cardId = el("cardId").value;

    const form = new FormData();
    form.append("title", el("title").value);
    form.append("description", el("description").value);

    const mediaFile = el("media").files[0];
    if (mediaFile) {
      
const mediaInput = el("media");
if (mediaInput && mediaInput.files && mediaInput.files.length) {
  [...mediaInput.files].forEach(f => form.append("media", f));
} else if (mediaFile) {
  form.append("media", mediaFile);
}
form.append("ai_prompt", el("aiPrompt")?.value || "");

    }

    let targetUrl = `/api/remote-sheet/sheets/${sheetId}`;

    if (mode === "card") {
      form.append("button_text", el("buttonText").value);
      form.append("url", el("url").value);
      form.append("price", el("price").value);
      form.append("contact", el("contact").value);
      form.append("map_url", el("mapUrl").value);
      form.append("download_url", el("downloadUrl").value);
      form.append("target_sheet_id", el("targetSheet").value);

      targetUrl =
        `/api/remote-sheet/sheets/${sheetId}/cards/${cardId}`;
    }

    await api(targetUrl, {
      method: "PUT",
      body: form
    });

    closeDrawer();
    await loadData();

      if (mode === "card") {
        const savedSheet = state.sheets.find(
          item => String(item.id) === String(sheetId)
        );

        const savedCard = savedSheet?.cards?.find(
          item => String(item.id) === String(cardId)
        );

        if (savedSheet && savedCard) {
          openCardPreview(savedSheet, savedCard);
        }
      }

  } catch (error) {
    alert(error.message);
  }
}

async function addSheet() {
  try {
    await api("/api/remote-sheet/sheets", {
      method: "POST"
    });

    activeIndex = state.sheets.length;
    await loadData();

  } catch (error) {
    alert(error.message);
  }
}

async function addCard(sheetId = null) {
  try {
    const currentSheetId =
      sheetId || state.sheets[activeIndex]?.id;

    if (!currentSheetId) {
      return;
    }

    await api(
      `/api/remote-sheet/sheets/${currentSheetId}/cards`,
      {method: "POST"}
    );

    await loadData();

  } catch (error) {
    alert(error.message);
  }
}

async function duplicateCurrent() {
  try {
    const mode = el("mode").value;
    const sheetId = el("sheetId").value;
    const cardId = el("cardId").value;

    let targetUrl =
      `/api/remote-sheet/sheets/${sheetId}/duplicate`;

    if (mode === "card") {
      targetUrl =
        `/api/remote-sheet/sheets/${sheetId}/cards/${cardId}/duplicate`;
    }

    await api(targetUrl, {
      method: "POST"
    });

    closeDrawer();
    await loadData();

  } catch (error) {
    alert(error.message);
  }
}

async function clearSheet() {
  const confirmed = confirm(
    "เคลียร์รูป ข้อความ และทุกช่องในแผ่นนี้ใช่ไหม ตัวแผ่นจะยังอยู่"
  );

  if (!confirmed) {
    return;
  }

  try {
    await api(
      `/api/remote-sheet/sheets/${el("sheetId").value}/clear`,
      {method: "POST"}
    );

    closeDrawer();
    await loadData();

  } catch (error) {
    alert(error.message);
  }
}

async function deleteCurrent() {
  const mode = el("mode").value;

  const message =
    mode === "card"
      ? "ลบช่องนี้ใช่ไหม"
      : "ลบทั้งแผ่นนี้ใช่ไหม";

  if (!confirm(message)) {
    return;
  }

  if (!confirm("ยืนยันอีกครั้ง")) {
    return;
  }

  try {
    const sheetId = el("sheetId").value;
    const cardId = el("cardId").value;

    let targetUrl =
      `/api/remote-sheet/sheets/${sheetId}`;

    if (mode === "card") {
      targetUrl =
        `/api/remote-sheet/sheets/${sheetId}/cards/${cardId}`;
    }

    await api(targetUrl, {
      method: "DELETE"
    });

    activeIndex = Math.max(0, activeIndex - 1);

    closeDrawer();
    await loadData();

  } catch (error) {
    alert(error.message);
  }
}

function escapeText(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function openTools() {
  const sheetId = state.sheets[activeIndex]?.id;
  if (!sheetId) { alert("ไม่พบแผ่น"); return; }
  location.href = "/remote-sheet-tools?sheet_id=" + encodeURIComponent(sheetId);
}

loadData();
</script>

<script id="infini-ai-shop-panel">
document.addEventListener("DOMContentLoaded", function () {
  const fileInputs = document.querySelectorAll('input[type="file"]');

  fileInputs.forEach(input => {
    input.multiple = true;
    input.accept = "image/*";
  });

  const firstFile = document.querySelector('input[type="file"]');
  if (!firstFile) return;

  const form = firstFile.closest("form") || document.body;

  const box = document.createElement("div");
  box.id = "infini-ai-upload";
  box.style.cssText = "margin:16px 0;padding:14px;border:1px solid #2b6b9a;border-radius:14px;background:#071426;color:white;";
  box.innerHTML = `
    <h3>🤖 AI จัดร้านให้หน่อย</h3>
    <textarea id="aiPrompt"
      placeholder="เช่น จัดร้านรองเท้าโทนดำ / เรียงสินค้าให้ดูแพง / ทำเป็นแกลเลอรี"
      style="width:100%;min-height:90px;border-radius:10px;padding:10px;background:#081b2e;color:white;border:1px solid #2b6b9a;"></textarea>
    <div id="preview" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;"></div>
    <button type="button" id="runAI" style="margin-top:12px;padding:12px 16px;border-radius:12px;border:0;background:linear-gradient(90deg,#35c8ff,#8b5cff);font-weight:800;">
      ✨ จัดร้านด้วย AI
    </button>
  `;

  form.insertBefore(box, firstFile.parentElement || firstFile);

  fileInputs.forEach(input => {
    input.addEventListener("change", function () {
      const preview = document.getElementById("preview");
      if (!preview) return;
      preview.innerHTML = "";

      [...this.files].forEach(file => {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        img.style.cssText = "width:90px;height:90px;object-fit:cover;border-radius:10px;border:1px solid #2b6b9a;";
        preview.appendChild(img);
      });
    });
  });

  document.getElementById("runAI")?.addEventListener("click", function () {
    const prompt = document.getElementById("aiPrompt")?.value || "";
    alert("พร้อมจัดร้านด้วย AI:\\n\\n" + prompt);
  });
});
</script>

</body>
</html>
"""
def install_remote_sheet(app: FastAPI):

    if not any(
        getattr(route, "path", "") == "/remote-sheet-media"
        for route in app.routes
    ):
        app.mount(
            "/remote-sheet-media",
            StaticFiles(directory=str(UPLOAD_DIR)),
            name="remote-sheet-media"
        )

    @app.get("/remote-sheet", response_class=HTMLResponse)
    async def remote_sheet_page():
        return HTML

    @app.get("/api/remote-sheet")
    async def get_remote_sheet():
        return load_data()

    @app.post("/api/remote-sheet/sheets")
    async def create_sheet():
        data = load_data()

        sheet = {
            "id": uuid.uuid4().hex,
            "title": "แผ่นใหม่",
            "description": "กดค้างเพื่อแก้ไข",
            "cards": []
        }

        data["sheets"].append(sheet)
        save_data(data)

        return {"ok": True}

    @app.put("/api/remote-sheet/sheets/{sheet_id}")
    async def update_sheet(
        sheet_id: str,
        title: str = Form(""),
        description: str = Form("")
    ):
        data = load_data()
        sheet = find_sheet(data, sheet_id)

        sheet["title"] = title
        sheet["description"] = description

        save_data(data)
        return {"ok": True}

    @app.post("/api/remote-sheet/sheets/{sheet_id}/cards")
    async def create_card(sheet_id: str):
        data = load_data()
        sheet = find_sheet(data, sheet_id)

        card = {
            "id": uuid.uuid4().hex,
            "title": "ช่องใหม่",
            "description": "",
            "button_text": "เปิด",
            "url": "#",
            "media": "",
            "media_type": ""
        }

        sheet["cards"].append(card)
        save_data(data)

        return {"ok": True}

    @app.put(
        "/api/remote-sheet/sheets/{sheet_id}/cards/{card_id}"
    )
    async def update_card(
        sheet_id: str,
        card_id: str,
        title: str = Form(""),
        description: str = Form(""),
        button_text: str = Form(""),
        url: str = Form(""),
        price: str = Form(""),
        contact: str = Form(""),
        map_url: str = Form(""),
        download_url: str = Form(""),
        target_sheet_id: str = Form(""),
        media: UploadFile = File(None)
    ):
        data = load_data()
        sheet = find_sheet(data, sheet_id)
        card = find_card(sheet, card_id)

        card["title"] = title
        card["description"] = description
        card["button_text"] = button_text
        card["url"] = url
        card["price"] = price
        card["contact"] = contact
        card["map_url"] = map_url
        card["download_url"] = download_url
        card["target_sheet_id"] = target_sheet_id

        if media and media.filename:
            suffix = Path(media.filename).suffix.lower()

            allowed = [
                ".jpg", ".jpeg", ".png", ".webp",
                ".gif", ".mp4", ".webm", ".mov"
            ]

            if suffix not in allowed:
                raise HTTPException(
                    400,
                    "รองรับเฉพาะรูปหรือวิดีโอ"
                )

            filename = uuid.uuid4().hex + suffix
            target = UPLOAD_DIR / filename

            with target.open("wb") as output:
                shutil.copyfileobj(media.file, output)

            card["media"] = (
                "/remote-sheet-media/" + filename
            )

            if suffix in [".mp4", ".webm", ".mov"]:
                card["media_type"] = "video"
            else:
                card["media_type"] = "image"

        save_data(data)
        return {"ok": True}

    @app.post(
        "/api/remote-sheet/sheets/{sheet_id}/duplicate"
    )
    async def duplicate_sheet(sheet_id: str):
        data = load_data()
        sheet = find_sheet(data, sheet_id)

        copied = json.loads(json.dumps(sheet))
        copied["id"] = uuid.uuid4().hex
        copied["title"] = copied["title"] + " สำเนา"

        for card in copied["cards"]:
            card["id"] = uuid.uuid4().hex

        data["sheets"].append(copied)
        save_data(data)

        return {"ok": True}

    @app.post(
        "/api/remote-sheet/sheets/{sheet_id}/cards/{card_id}/duplicate"
    )
    async def duplicate_card(
        sheet_id: str,
        card_id: str
    ):
        data = load_data()
        sheet = find_sheet(data, sheet_id)
        card = find_card(sheet, card_id)

        copied = json.loads(json.dumps(card))
        copied["id"] = uuid.uuid4().hex
        copied["title"] = copied["title"] + " สำเนา"

        sheet["cards"].append(copied)
        save_data(data)

        return {"ok": True}

    @app.post(
        "/api/remote-sheet/sheets/{sheet_id}/clear"
    )
    async def clear_sheet(sheet_id: str):
        data = load_data()
        sheet = find_sheet(data, sheet_id)

        sheet["description"] = ""
        sheet["cards"] = []

        save_data(data)
        return {"ok": True}

    @app.delete(
        "/api/remote-sheet/sheets/{sheet_id}/cards/{card_id}"
    )
    async def delete_card(
        sheet_id: str,
        card_id: str
    ):
        data = load_data()
        sheet = find_sheet(data, sheet_id)

        sheet["cards"] = [
            card for card in sheet["cards"]
            if card["id"] != card_id
        ]

        save_data(data)
        return {"ok": True}

    @app.delete(
        "/api/remote-sheet/sheets/{sheet_id}"
    )
    async def delete_sheet(sheet_id: str):
        data = load_data()

        if len(data["sheets"]) <= 1:
            raise HTTPException(
                400,
                "ต้องเหลืออย่างน้อยหนึ่งแผ่น"
            )

        data["sheets"] = [
            sheet for sheet in data["sheets"]
            if sheet["id"] != sheet_id
        ]

        save_data(data)
        return {"ok": True}
