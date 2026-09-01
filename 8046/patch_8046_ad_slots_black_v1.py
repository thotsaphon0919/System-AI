from __future__ import annotations

from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MAIN_FILE = BASE_DIR / "main.py"

if not MAIN_FILE.exists():
    raise SystemExit("ไม่พบ main.py ในโฟลเดอร์นี้")

source = MAIN_FILE.read_text(encoding="utf-8")

start_marker = '@app.get("/tower/ad-market/{category}")'
end_marker = "# หน้า 5"

start = source.find(start_marker)
end = source.find(end_marker, start)

if start < 0:
    raise SystemExit("ไม่พบ Route /tower/ad-market/{category}")

if end < 0:
    raise SystemExit("ไม่พบจุดเริ่ม # หน้า 5")

backup = BASE_DIR / (
    "main.py.before_ad_slots_black_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)
backup.write_text(source, encoding="utf-8")

NEW_BLOCK = r'''from pathlib import Path as _AdSlotPath

AD_MARKET_SLOT_FILE = (
    _AdSlotPath(__file__).resolve().parent
    / "ad_market_slot_counts.json"
)


def _ad_market_clean_category(value: str) -> str:
    cleaned = "".join(
        char
        for char in value.strip().lower()
        if char in "abcdefghijklmnopqrstuvwxyz0123456789-_"
    )
    return cleaned[:50] or "general"


def _ad_market_load_slot_counts() -> dict:
    import json

    if not AD_MARKET_SLOT_FILE.exists():
        return {}

    try:
        data = json.loads(
            AD_MARKET_SLOT_FILE.read_text(encoding="utf-8")
        )
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _ad_market_save_slot_counts(data: dict) -> None:
    import json

    temp_file = AD_MARKET_SLOT_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_file.replace(AD_MARKET_SLOT_FILE)


@app.post("/tower/ad-market/{category}/add-slot")
async def ad_market_add_slot(category: str):
    from fastapi.responses import RedirectResponse as _AdSlotRedirect

    safe_category = _ad_market_clean_category(category)
    counts = _ad_market_load_slot_counts()

    try:
        current = int(counts.get(safe_category, 6))
    except (TypeError, ValueError):
        current = 6

    counts[safe_category] = min(max(current, 1) + 1, 50)
    _ad_market_save_slot_counts(counts)

    return _AdSlotRedirect(
        url=f"/tower/ad-market/{safe_category}",
        status_code=303,
    )


@app.get("/tower/ad-market/{category}")
def ad_list(category: str):
    safe_category = _ad_market_clean_category(category)
    counts = _ad_market_load_slot_counts()

    try:
        slot_count = int(counts.get(safe_category, 6))
    except (TypeError, ValueError):
        slot_count = 6

    slot_count = min(max(slot_count, 1), 50)
    rows = ""

    for i in range(1, slot_count + 1):
        ad_id = f"{safe_category}-{i}"

        rows += f"""
        <article class="iadslot-card">
            <div class="iadslot-media">
                {normal_ad_media_html(ad_id)}
            </div>

            <div class="iadslot-shade"></div>

            <div class="iadslot-tag">
                {safe_category.upper()}
            </div>

            <div class="iadslot-copy">
                <h3>โฆษณา {safe_category.upper()} #{i}</h3>
                <p>ดูครบ 30 วินาที</p>

                <div class="iadslot-bottom">
                    <div>
                        <small>รางวัล</small>
                        <strong>รับ 5 INF</strong>
                    </div>

                    <a
                        class="iadslot-watch"
                        href="/tower/ad/{ad_id}"
                    >
                        ดูโฆษณา
                    </a>

                    <span class="iadslot-plus">+5</span>
                </div>
            </div>
        </article>
        """

    return page("รายการโฆษณา", f"""
    <style>
    html, body {{
        background:#000 !important;
    }}

    body {{
        color:#fff !important;
    }}

    .wrap {{
        max-width:920px !important;
        padding-left:14px !important;
        padding-right:14px !important;
    }}

    .iadslot-page,
    .iadslot-page * {{
        box-sizing:border-box;
    }}

    .iadslot-page {{
        width:100%;
        padding:8px 0 110px;
    }}

    .iadslot-head {{
        margin-bottom:16px;
        padding:20px 18px;
        border:1px solid rgba(139,70,255,.42);
        border-radius:24px;
        background:
            radial-gradient(
                circle at 90% 10%,
                rgba(143,54,255,.22),
                transparent 34%
            ),
            #050509;
    }}

    .iadslot-head small {{
        color:#8cecff;
        font-size:11px;
        font-weight:900;
        letter-spacing:1.6px;
    }}

    .iadslot-head h1 {{
        margin:7px 0 5px;
        color:#fff;
        font-size:clamp(30px,9vw,48px);
        line-height:1;
    }}

    .iadslot-head p {{
        margin:0;
        color:#8f8d98;
        font-size:14px;
    }}

    .iadslot-count {{
        display:inline-flex;
        margin-top:14px;
        padding:8px 12px;
        border:1px solid rgba(125,221,255,.24);
        border-radius:999px;
        background:#080b12;
        color:#79e3ff;
        font-size:12px;
        font-weight:900;
    }}

    .iadslot-grid {{
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:12px;
    }}

    .iadslot-card {{
        position:relative;
        min-width:0;
        aspect-ratio:2/3;
        overflow:hidden;
        border:1px solid rgba(154,77,255,.52);
        border-radius:22px;
        background:#050505;
        box-shadow:
            0 13px 34px rgba(0,0,0,.55),
            0 0 20px rgba(126,48,255,.10);
    }}

    .iadslot-media {{
        position:absolute;
        inset:0;
    }}

    .iadslot-media > a {{
        width:100% !important;
        height:100% !important;
        aspect-ratio:auto !important;
        border-radius:0 !important;
        background:#050505 !important;
    }}

    .iadslot-media img,
    .iadslot-media video {{
        width:100% !important;
        height:100% !important;
        object-fit:cover !important;
        border-radius:0 !important;
    }}

    .iadslot-shade {{
        position:absolute;
        inset:0;
        pointer-events:none;
        background:
            linear-gradient(
                180deg,
                rgba(0,0,0,.04) 28%,
                rgba(0,0,0,.34) 58%,
                rgba(0,0,0,.96) 100%
            );
    }}

    .iadslot-tag {{
        position:absolute;
        top:11px;
        left:11px;
        z-index:3;
        padding:6px 9px;
        border:1px solid rgba(205,111,255,.58);
        border-radius:9px;
        background:rgba(8,4,18,.72);
        color:#e6bdff;
        font-size:10px;
        font-weight:900;
        letter-spacing:.7px;
        backdrop-filter:blur(8px);
    }}

    .iadslot-copy {{
        position:absolute;
        right:0;
        bottom:0;
        left:0;
        z-index:4;
        padding:14px;
    }}

    .iadslot-copy h3 {{
        margin:0;
        color:#fff;
        font-size:clamp(16px,4.4vw,23px);
        line-height:1.1;
        text-shadow:0 2px 10px #000;
    }}

    .iadslot-copy p {{
        margin:6px 0 12px;
        color:#d2d0d7;
        font-size:12px;
    }}

    .iadslot-bottom {{
        display:grid;
        grid-template-columns:minmax(0,1fr) auto;
        gap:9px;
        align-items:end;
    }}

    .iadslot-bottom small {{
        display:block;
        color:#87848f;
        font-size:9px;
    }}

    .iadslot-bottom strong {{
        display:block;
        color:#d66cff;
        font-size:14px;
    }}

    .iadslot-watch {{
        display:inline-flex;
        min-height:38px;
        padding:0 12px;
        align-items:center;
        justify-content:center;
        border:1px solid rgba(202,99,255,.62);
        border-radius:12px;
        background:linear-gradient(135deg,#6d27dc,#a73bff);
        color:#fff !important;
        text-decoration:none;
        font-size:11px;
        font-weight:900;
        box-shadow:0 8px 18px rgba(125,37,232,.27);
    }}

    .iadslot-plus {{
        position:absolute;
        right:12px;
        top:-49px;
        width:46px;
        height:46px;
        display:flex;
        align-items:center;
        justify-content:center;
        border:1px solid rgba(220,129,255,.72);
        border-radius:50%;
        background:rgba(85,25,156,.88);
        color:#fff;
        font-size:17px;
        font-weight:900;
        box-shadow:0 0 20px rgba(165,61,255,.32);
        backdrop-filter:blur(8px);
    }}

    .iadslot-add-form {{
        position:fixed;
        right:18px;
        bottom:82px;
        z-index:10020;
        margin:0;
    }}

    .iadslot-add-button {{
        width:66px;
        height:66px;
        display:flex;
        align-items:center;
        justify-content:center;
        border:1px solid #d178ff;
        border-radius:50%;
        background:linear-gradient(145deg,#c64cff,#6326d9);
        color:#fff;
        font-size:34px;
        font-weight:300;
        box-shadow:
            0 14px 34px rgba(120,30,220,.48),
            0 0 25px rgba(184,70,255,.27);
    }}

    .iadslot-add-label {{
        position:fixed;
        right:15px;
        bottom:58px;
        z-index:10019;
        color:#bcb8c4;
        font-size:10px;
        font-weight:800;
    }}

    @media(min-width:720px) {{
        .iadslot-grid {{
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:16px;
        }}
    }}

    @media(max-width:380px) {{
        .iadslot-grid {{
            gap:9px;
        }}

        .iadslot-card {{
            border-radius:18px;
        }}

        .iadslot-copy {{
            padding:11px;
        }}

        .iadslot-watch {{
            min-height:34px;
            padding:0 9px;
        }}
    }}
    </style>

    <main class="iadslot-page">
        <header class="iadslot-head">
            <small>INFINI AD MARKET</small>
            <h1>{safe_category.upper()}</h1>
            <p>
                แตะรูปเพื่ออัปโหลดหรือเปลี่ยนสื่อ
                และกดดูโฆษณาเพื่อเปิดรายการ
            </p>
            <span class="iadslot-count">
                {slot_count} ช่องโฆษณา
            </span>
        </header>

        <section class="iadslot-grid">
            {rows}
        </section>

        <form
            class="iadslot-add-form"
            method="post"
            action="/tower/ad-market/{safe_category}/add-slot"
        >
            <button
                class="iadslot-add-button"
                type="submit"
                aria-label="เพิ่มช่องโฆษณา"
                title="เพิ่มช่องโฆษณา"
            >
                +
            </button>
        </form>

        <span class="iadslot-add-label">เพิ่มช่อง</span>
    </main>
    """)

'''

updated = source[:start] + NEW_BLOCK + "\n\n" + source[end:]
MAIN_FILE.write_text(updated, encoding="utf-8")

print("8046_AD_SLOTS_BLACK_V1_OK")
print(f"backup: {backup.name}")
