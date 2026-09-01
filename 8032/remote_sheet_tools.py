from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parent
REMOTE_DATA_DIR = BASE_DIR / "remote_sheet_data"
REMOTE_DATA_FILE = REMOTE_DATA_DIR / "sheets.json"

REMOTE_DATA_DIR.mkdir(parents=True, exist_ok=True)

BLOCK_TYPES = [
    {
        "type": "text",
        "name": "ข้อความ",
        "icon": "T",
        "description": "หัวข้อและรายละเอียด",
    },
    {
        "type": "image",
        "name": "รูปภาพ",
        "icon": "🖼️",
        "description": "รูปปกหรือรูปผลงาน",
    },
    {
        "type": "video",
        "name": "วิดีโอ",
        "icon": "🎬",
        "description": "วิดีโอแนะนำหรือผลงาน",
    },
    {
        "type": "button",
        "name": "ปุ่ม",
        "icon": "🔘",
        "description": "ปุ่มเปิดลิงก์หรือคำสั่ง",
    },
    {
        "type": "product",
        "name": "สินค้าและราคา",
        "icon": "🛍️",
        "description": "สินค้า บริการ และราคา",
    },
    {
        "type": "gallery",
        "name": "แกลเลอรี",
        "icon": "🖼",
        "description": "รวมรูปหลายภาพ",
    },
    {
        "type": "profile",
        "name": "โปรไฟล์",
        "icon": "👤",
        "description": "ข้อมูลเจ้าของพื้นที่",
    },
    {
        "type": "contact",
        "name": "ติดต่อ",
        "icon": "☎️",
        "description": "โทร อีเมล หรือโซเชียล",
    },
    {
        "type": "map",
        "name": "แผนที่",
        "icon": "📍",
        "description": "ตำแหน่งหรือสถานที่",
    },
    {
        "type": "form",
        "name": "แบบฟอร์ม",
        "icon": "📝",
        "description": "รับข้อมูลจากผู้ชม",
    },
    {
        "type": "download",
        "name": "ไฟล์ดาวน์โหลด",
        "icon": "📥",
        "description": "ไฟล์ให้ผู้ชมดาวน์โหลด",
    },
    {
        "type": "sheet_link",
        "name": "เชื่อมไปแผ่นอื่น",
        "icon": "🔗",
        "description": "เปิดแผ่นอื่นใน Space เดียวกัน",
    },
]


def load_remote_data() -> dict[str, Any]:
    if not REMOTE_DATA_FILE.exists():
        return {"sheets": []}

    try:
        data = json.loads(
            REMOTE_DATA_FILE.read_text(encoding="utf-8")
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"อ่านข้อมูล Remote ไม่สำเร็จ: {error}",
        )

    if not isinstance(data, dict):
        return {"sheets": []}

    data.setdefault("sheets", [])
    return data


def save_remote_data(data: dict[str, Any]) -> None:
    temporary = REMOTE_DATA_FILE.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(REMOTE_DATA_FILE)


def find_sheet(
    data: dict[str, Any],
    sheet_id: str,
) -> dict[str, Any]:
    for sheet in data.get("sheets", []):
        if sheet.get("id") == sheet_id:
            return sheet

    raise HTTPException(
        status_code=404,
        detail="ไม่พบแผ่นที่เลือก",
    )
TOOLS_HTML = """
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>INFINI Tools</title>
<style>
*{box-sizing:border-box}
body{
  margin:0;
  background:#07111d;
  color:white;
  font-family:system-ui,sans-serif;
}
header{
  position:sticky;
  top:0;
  z-index:5;
  padding:16px;
  background:#0b1725;
  border-bottom:1px solid #213850;
}
h1{margin:0;font-size:22px}
.note{
  margin:6px 0 0;
  color:#9cb0c4;
  font-size:13px;
}
.grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:12px;
  padding:16px;
}
.tool{
  min-height:145px;
  padding:16px;
  border:1px solid #29445f;
  border-radius:18px;
  background:linear-gradient(145deg,#102238,#0b1726);
}
.icon{font-size:30px;margin-bottom:12px}
.tool h3{margin:0 0 7px}
.tool p{
  margin:0 0 12px;
  color:#9cb0c4;
  font-size:13px;
}
button{
  width:100%;
  border:0;
  border-radius:11px;
  padding:10px;
  background:#36c8ff;
  color:#04111b;
  font-weight:800;
}
@media(min-width:800px){
  .grid{grid-template-columns:repeat(4,1fr)}
}
</style>
</head>
<body>
<header>
  <h1>คลังช่อง INFINI</h1>
  <p class="note">
    เลือกใช้เฉพาะช่องที่ต้องการ ไม่จำเป็นต้องกรอกข้อมูลครบทุกช่อง
  </p>
</header>

<main id="grid" class="grid"></main>

<script>
const params = new URLSearchParams(location.search);
const sheetId = params.get("sheet_id");

async function loadTools(){
  const response = await fetch("/api/remote-sheet-tools");
  const tools = await response.json();

  const grid = document.getElementById("grid");

  grid.innerHTML = tools.map(tool => `
    <article class="tool">
      <div class="icon">${tool.icon}</div>
      <h3>${tool.name}</h3>
      <p>${tool.description}</p>
      <button onclick="createBlock('${tool.type}')">
        เพิ่มช่องนี้
      </button>
    </article>
  `).join("");
}

async function createBlock(type){
  if(!sheetId){
    alert("ไม่พบรหัสแผ่น");
    return;
  }

  const form = new FormData();
  form.append("block_type", type);

  const response = await fetch(
    `/api/remote-sheet-tools/sheets/${sheetId}/blocks`,
    {
      method:"POST",
      body:form
    }
  );

  const data = await response.json();

  if(!response.ok){
    alert(data.detail || "เพิ่มช่องไม่สำเร็จ");
    return;
  }

  location.href = "/remote-sheet";
}

loadTools();
</script>
</body>
</html>
"""


def default_block(block_type: str) -> dict[str, Any]:
    selected = next(
        (
            item
            for item in BLOCK_TYPES
            if item["type"] == block_type
        ),
        None,
    )

    if selected is None:
        raise HTTPException(
            status_code=400,
            detail="ไม่พบชนิดช่องที่เลือก",
        )

    return {
        "id": uuid.uuid4().hex,
        "type": block_type,
        "title": selected["name"],
        "description": "",
        "button_text": "เปิด",
        "url": "",
        "target_sheet_id": "",
        "media": "",
        "media_type": "",
        "price": "",
        "contact": "",
        "map_url": "",
        "download_url": "",
        "hidden": False,
        "order": 0,
        "width": 1,
        "height": 1,
    }


def install_remote_sheet_tools(app: FastAPI) -> None:

    @app.get(
        "/remote-sheet-tools",
        response_class=HTMLResponse,
    )
    async def remote_sheet_tools_page():
        return TOOLS_HTML

    @app.get("/api/remote-sheet-tools")
    async def get_remote_sheet_tools():
        return BLOCK_TYPES
    @app.get(
        "/api/remote-sheet-tools/sheets"
    )
    async def get_sheet_choices():
        data = load_remote_data()

        return [
            {
                "id": sheet.get("id", ""),
                "title": sheet.get(
                    "title",
                    "แผ่นไม่มีชื่อ",
                ),
            }
            for sheet in data.get("sheets", [])
        ]

    @app.post(
        "/api/remote-sheet-tools/sheets/{sheet_id}/blocks"
    )
    async def create_block(
        sheet_id: str,
        block_type: str = Form(...),
    ):
        data = load_remote_data()
        sheet = find_sheet(data, sheet_id)

        block = default_block(block_type)
        block["order"] = len(
            sheet.setdefault("cards", [])
        )

        sheet["cards"].append(block)
        save_remote_data(data)

        return {
            "ok": True,
            "block": block,
        }

    @app.put(
        "/api/remote-sheet-tools/sheets/{sheet_id}/blocks/{block_id}"
    )
    async def update_block(
        sheet_id: str,
        block_id: str,
        block_type: str = Form(""),
        title: str = Form(""),
        description: str = Form(""),
        button_text: str = Form(""),
        url: str = Form(""),
        target_sheet_id: str = Form(""),
        price: str = Form(""),
        contact: str = Form(""),
        map_url: str = Form(""),
        download_url: str = Form(""),
        width: int = Form(1),
        height: int = Form(1),
    ):
        data = load_remote_data()
        sheet = find_sheet(data, sheet_id)

        block = next(
            (
                item
                for item in sheet.get("cards", [])
                if item.get("id") == block_id
            ),
            None,
        )

        if block is None:
            raise HTTPException(
                status_code=404,
                detail="ไม่พบช่องที่เลือก",
            )

        if block_type:
            block["type"] = block_type

        block["title"] = title
        block["description"] = description
        block["button_text"] = button_text
        block["url"] = url
        block["target_sheet_id"] = target_sheet_id
        block["price"] = price
        block["contact"] = contact
        block["map_url"] = map_url
        block["download_url"] = download_url
        block["width"] = max(1, min(width, 4))
        block["height"] = max(1, min(height, 4))

        save_remote_data(data)

        return {
            "ok": True,
            "block": block,
        }

    @app.post(
        "/api/remote-sheet-tools/sheets/{sheet_id}/blocks/{block_id}/move"
    )
    async def move_block(
        sheet_id: str,
        block_id: str,
        direction: str = Form(...),
    ):
        data = load_remote_data()
        sheet = find_sheet(data, sheet_id)
        cards = sheet.get("cards", [])

        index = next(
            (
                position
                for position, item in enumerate(cards)
                if item.get("id") == block_id
            ),
            None,
        )

        if index is None:
            raise HTTPException(
                status_code=404,
                detail="ไม่พบช่องที่เลือก",
            )

        if direction == "left" and index > 0:
            cards[index - 1], cards[index] = (
                cards[index],
                cards[index - 1],
            )

        elif (
            direction == "right"
            and index < len(cards) - 1
        ):
            cards[index + 1], cards[index] = (
                cards[index],
                cards[index + 1],
            )

        for order, item in enumerate(cards):
            item["order"] = order

        save_remote_data(data)

        return {
            "ok": True,
            "cards": cards,
        }
    @app.post(
        "/api/remote-sheet-tools/sheets/{sheet_id}/blocks/{block_id}/toggle-hidden"
    )
    async def toggle_block_hidden(
        sheet_id: str,
        block_id: str,
    ):
        data = load_remote_data()
        sheet = find_sheet(data, sheet_id)

        block = next(
            (
                item
                for item in sheet.get("cards", [])
                if item.get("id") == block_id
            ),
            None,
        )

        if block is None:
            raise HTTPException(
                status_code=404,
                detail="ไม่พบช่องที่เลือก",
            )

        block["hidden"] = not bool(
            block.get("hidden", False)
        )

        save_remote_data(data)

        return {
            "ok": True,
            "hidden": block["hidden"],
        }

    @app.delete(
        "/api/remote-sheet-tools/sheets/{sheet_id}/blocks/{block_id}"
    )
    async def delete_block(
        sheet_id: str,
        block_id: str,
    ):
        data = load_remote_data()
        sheet = find_sheet(data, sheet_id)

        before = len(sheet.get("cards", []))

        sheet["cards"] = [
            item
            for item in sheet.get("cards", [])
            if item.get("id") != block_id
        ]

        if len(sheet["cards"]) == before:
            raise HTTPException(
                status_code=404,
                detail="ไม่พบช่องที่เลือก",
            )

        for order, item in enumerate(
            sheet["cards"]
        ):
            item["order"] = order

        save_remote_data(data)

        return {"ok": True}

    @app.get(
        "/api/remote-sheet-tools/sheets/{sheet_id}/public-url"
    )
    async def get_public_url(
        sheet_id: str,
    ):
        data = load_remote_data()
        sheet = find_sheet(data, sheet_id)

        return {
            "ok": True,
            "sheet_id": sheet_id,
            "public_url":
                f"/remote-sheet/view/{sheet_id}",
            "title": sheet.get(
                "title",
                "แผ่นไม่มีชื่อ",
            ),
        }
