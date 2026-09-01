#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/downloads/infini_point_tower"

# สำรองไฟล์เดิม
cp main.py "main.py.before_home_panel_$(date +%Y%m%d_%H%M%S).backup"

cat > home_upload_panel.py <<'PY'
from __future__ import annotations

import html
import json
import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "home_uploads"
CONFIG_FILE = BASE_DIR / "home_page_config.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    default = {
        "image": "",
        "enter_link": "/tower/dashboard",
        "earn_link": "/tower/ad-market",
        "reward_link": "/tower/rewards",
    }

    if not CONFIG_FILE.exists():
        return default

    try:
        saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        default.update(saved)
    except Exception:
        pass

    return default


def save_config(config: dict) -> None:
    CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def setup_home_upload_panel(app) -> None:
    @app.middleware("http")
    async def home_upload_panel_middleware(request: Request, call_next):
        path = request.url.path

        # เปิดรูปที่อัปโหลด
        if path.startswith("/tower/home-media/"):
            filename = Path(path).name
            file_path = UPLOAD_DIR / filename

            if not file_path.exists():
                return HTMLResponse("ไม่พบรูป", status_code=404)

            return FileResponse(file_path)

        # รับรูปจากแผงอัปโหลด
        if path == "/tower/home-upload" and request.method == "POST":
            form = await request.form()

            image = form.get("hero_image")
            config = load_config()

            config["enter_link"] = str(
                form.get("enter_link") or "/tower/dashboard"
            )
            config["earn_link"] = str(
                form.get("earn_link") or "/tower/ad-market"
            )
            config["reward_link"] = str(
                form.get("reward_link") or "/tower/rewards"
            )

            if image and getattr(image, "filename", ""):
                extension = Path(image.filename).suffix.lower()

                allowed = {
                    ".jpg", ".jpeg", ".png",
                    ".webp", ".gif",
                }

                if extension not in allowed:
                    return HTMLResponse(
                        """
                        <h2>ชนิดไฟล์ไม่รองรับ</h2>
                        <p>รองรับ JPG, PNG, WEBP และ GIF</p>
                        <a href="/tower">กลับหน้าแรก</a>
                        """,
                        status_code=400,
                    )

                filename = uuid.uuid4().hex + extension
                file_path = UPLOAD_DIR / filename

                content = await image.read()
                file_path.write_bytes(content)

                config["image"] = filename

            save_config(config)
            return RedirectResponse("/tower", status_code=303)

        response = await call_next(request)

        # เพิ่มแผงเฉพาะหน้าแรก
        if path != "/tower" or request.method != "GET":
            return response

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        page_html = body.decode("utf-8", errors="replace")
        config = load_config()

        image_name = html.escape(config.get("image", ""))
        enter_link = html.escape(config.get("enter_link", "/tower/dashboard"))
        earn_link = html.escape(config.get("earn_link", "/tower/ad-market"))
        reward_link = html.escape(config.get("reward_link", "/tower/rewards"))

        hero_html = ""

        if image_name:
            hero_html = f"""
            <section class="infini-home-picture">
              <img
                src="/tower/home-media/{image_name}"
                alt="INFINI Point Tower"
              >

              <a
                class="infini-hotspot infini-enter"
                href="{enter_link}"
                aria-label="Enter Tower"
              ></a>

              <a
                class="infini-hotspot infini-earn"
                href="{earn_link}"
                aria-label="How to Earn"
              ></a>

              <a
                class="infini-hotspot infini-reward"
                href="{reward_link}"
                aria-label="Redeem Rewards"
              ></a>
            </section>
            """

        injection = f"""
        <style>
          .infini-home-picture {{
            position: relative;
            width: 100%;
            max-width: 1080px;
            margin: 16px auto;
            overflow: hidden;
            border-radius: 20px;
            border: 1px solid rgba(154,77,255,.7);
            background: #050714;
          }}

          .infini-home-picture img {{
            width: 100%;
            height: auto;
            display: block;
          }}

          .infini-hotspot {{
            position: absolute;
            display: block;
            background: rgba(154,77,255,.02);
            border-radius: 16px;
          }}

          .infini-hotspot:active {{
            background: rgba(154,77,255,.25);
          }}

          .infini-enter {{
            left: 36%;
            bottom: 2%;
            width: 28%;
            height: 11%;
          }}

          .infini-earn {{
            left: 3%;
            bottom: 2%;
            width: 29%;
            height: 11%;
          }}

          .infini-reward {{
            right: 3%;
            bottom: 2%;
            width: 29%;
            height: 11%;
          }}

          .infini-upload-toggle {{
            position: fixed;
            right: 14px;
            top: 92px;
            z-index: 10002;
            width: 52px;
            height: 52px;
            border: 1px solid #9a4dff;
            border-radius: 50%;
            background: #0b1022;
            color: white;
            font-size: 24px;
            box-shadow: 0 0 22px rgba(154,77,255,.5);
          }}

          .infini-upload-panel {{
            position: fixed;
            top: 0;
            right: -105%;
            z-index: 10001;
            width: min(92vw, 430px);
            height: 100vh;
            padding: 24px;
            overflow-y: auto;
            background: #080c1b;
            color: white;
            border-left: 1px solid #864aff;
            transition: right .28s ease;
            box-shadow: -12px 0 40px rgba(0,0,0,.55);
          }}

          .infini-upload-panel.open {{
            right: 0;
          }}

          .infini-upload-panel h2 {{
            margin-top: 12px;
            color: #c985ff;
          }}

          .infini-upload-panel label {{
            display: block;
            margin: 16px 0 7px;
          }}

          .infini-upload-panel input {{
            width: 100%;
            padding: 13px;
            border: 1px solid #7139c9;
            border-radius: 12px;
            background: #050817;
            color: white;
          }}

          .infini-upload-panel button[type="submit"] {{
            width: 100%;
            margin-top: 20px;
            padding: 14px;
            border: 1px solid #b875ff;
            border-radius: 14px;
            background: linear-gradient(135deg,#5420ad,#9a4dff);
            color: white;
            font-weight: bold;
          }}

          .infini-close {{
            float: right;
            border: 0;
            background: transparent;
            color: white;
            font-size: 32px;
          }}

          #infiniImagePreview {{
            width: 100%;
            margin-top: 14px;
            border-radius: 14px;
            display: none;
          }}
        </style>

        {hero_html}

        <button
          class="infini-upload-toggle"
          type="button"
          onclick="toggleInfiniUploadPanel()"
          aria-label="จัดการรูปหน้าแรก"
        >⚙</button>

        <aside
          id="infiniUploadPanel"
          class="infini-upload-panel"
        >
          <button
            class="infini-close"
            type="button"
            onclick="toggleInfiniUploadPanel()"
          >×</button>

          <h2>จัดการหน้าแรก Point Tower</h2>
          <p>อัปโหลดภาพ และกำหนดลิงก์ของช่องในภาพ</p>

          <form
            method="post"
            action="/tower/home-upload"
            enctype="multipart/form-data"
          >
            <label>อัปโหลดภาพหน้าแรก</label>
            <input
              type="file"
              name="hero_image"
              accept="image/*"
              onchange="previewInfiniHomeImage(event)"
            >

            <img id="infiniImagePreview" alt="ตัวอย่างรูป">

            <label>ลิงก์ ENTER TOWER</label>
            <input
              name="enter_link"
              value="{enter_link}"
              required
            >

            <label>ลิงก์ HOW TO EARN</label>
            <input
              name="earn_link"
              value="{earn_link}"
              required
            >

            <label>ลิงก์ REDEEM REWARDS</label>
            <input
              name="reward_link"
              value="{reward_link}"
              required
            >

            <button type="submit">
              อัปโหลดและเผยแพร่
            </button>
          </form>
        </aside>

        <script>
          function toggleInfiniUploadPanel() {{
            document
              .getElementById("infiniUploadPanel")
              .classList.toggle("open");
          }}

          function previewInfiniHomeImage(event) {{
            const file = event.target.files[0];
            const preview =
              document.getElementById("infiniImagePreview");

            if (!file) {{
              preview.style.display = "none";
              return;
            }}

            preview.src = URL.createObjectURL(file);
            preview.style.display = "block";
          }}
        </script>
        """

        if "</body>" in page_html:
            page_html = page_html.replace(
                "</body>",
                injection + "</body>",
                1,
            )
        else:
            page_html += injection

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in {
                "content-length",
                "content-encoding",
            }
        }

        return HTMLResponse(
            page_html,
            status_code=response.status_code,
            headers=headers,
        )
PY

python - <<'PY'
from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8")

marker = 'if __name__ == "__main__":'

install_code = '''
# เพิ่มแผงอัปโหลดรูปหน้าแรก Point Tower
from home_upload_panel import setup_home_upload_panel
setup_home_upload_panel(app)

'''

if "setup_home_upload_panel(app)" not in text:
    if marker in text:
        text = text.replace(
            marker,
            install_code + marker,
            1,
        )
    else:
        text += "\\n" + install_code

    path.write_text(text, encoding="utf-8")
    print("เพิ่มระบบอัปโหลดหน้าแรกเรียบร้อย")
else:
    print("ระบบนี้ถูกเพิ่มไว้แล้ว ไม่ได้เพิ่มซ้ำ")
PY

echo ""
echo "ติดตั้งสำเร็จ"
echo "รันด้วย:"
echo "cd ~/downloads/infini_point_tower"
echo "python main.py"
