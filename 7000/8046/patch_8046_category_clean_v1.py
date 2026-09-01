from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8")

start = s.find('@app.get("/tower/ad-market/{category}")')
if start == -1:
    raise SystemExit("ไม่พบ route /tower/ad-market/{category}")

end = s.find('@app.get("/tower/ad/{ad_id}")', start)
if end == -1:
    raise SystemExit("ไม่พบจุดจบ route category ก่อนหน้า /tower/ad/{ad_id}")

new_block = r'''
@app.get("/tower/ad-market/{category}")
def ad_market_category(category: str):
    title = category.upper()
    total_slots = 8

    cards = []
    for i in range(1, total_slots + 1):
        ad_id = f"{category}-{i}"
        cards.append(f"""
        <div class="adcat-card">
            <a class="adcat-thumb-link" href="/normal-ad-upload/{ad_id}?back_url=/tower/ad-market/{category}">
                <div class="adcat-thumb-slot">
                    {normal_ad_media_html(ad_id)}
                </div>
            </a>

            <div class="adcat-body">
                <h3>{title} #{i}</h3>
                <p class="meta">ดูครบ 30 วินาที</p>
                <p class="reward">รับ 5 INF</p>
                <a class="watch-btn" href="/tower/ad/{ad_id}">ดูโฆษณา</a>
            </div>
        </div>
        """)

    rows = "".join(cards)

    return page("รายการโฆษณา", f"""
    <style>
      body {{
        background:#000 !important;
      }}

      .adcat-shell {{
        background:#000;
        min-height:100vh;
        padding:12px 0 28px;
      }}

      .adcat-hero {{
        margin:0 14px 16px;
        padding:20px 18px;
        border-radius:24px;
        border:1px solid rgba(142, 77, 255, 0.65);
        background:linear-gradient(135deg,#050511 0%, #0a0c19 58%, #26124a 100%);
        box-shadow:0 0 0 1px rgba(144,89,255,.18), 0 12px 28px rgba(0,0,0,.35);
      }}

      .adcat-hero .eyebrow {{
        color:#8ee7ff;
        font-size:13px;
        font-weight:800;
        letter-spacing:.08em;
        margin-bottom:10px;
      }}

      .adcat-hero h1 {{
        margin:0;
        color:#fff;
        font-size:32px;
        line-height:1.05;
        font-weight:900;
      }}

      .adcat-hero p {{
        margin:14px 0 0;
        color:#c9c9d7;
        font-size:14px;
        line-height:1.55;
      }}

      .adcat-count {{
        display:inline-flex;
        align-items:center;
        margin-top:14px;
        padding:10px 16px;
        border-radius:999px;
        border:1px solid rgba(108,202,255,.28);
        background:rgba(5,14,30,.85);
        color:#8ee7ff;
        font-size:14px;
        font-weight:800;
      }}

      .adcat-grid {{
        display:grid;
        grid-template-columns:repeat(2, minmax(0,1fr));
        gap:14px;
        padding:0 14px;
      }}

      .adcat-card {{
        background:linear-gradient(180deg,#070a14 0%, #060814 100%);
        border:1px solid rgba(142,77,255,.62);
        border-radius:22px;
        overflow:hidden;
        box-shadow:0 10px 24px rgba(0,0,0,.28);
      }}

      .adcat-thumb-link {{
        display:block;
        height:110px;
        background:#090d18;
        overflow:hidden;
        border-bottom:1px solid rgba(142,77,255,.28);
        text-decoration:none;
      }}

      .adcat-thumb-slot {{
        width:100%;
        height:100%;
        overflow:hidden;
        position:relative;
        background:linear-gradient(135deg,#0b0f18 0%, #12182a 100%);
      }}

      .adcat-thumb-slot img,
      .adcat-thumb-slot video,
      .adcat-thumb-slot iframe {{
        width:100% !important;
        height:100% !important;
        object-fit:cover !important;
        display:block;
        border:0 !important;
      }}

      .adcat-thumb-slot .placeholder {{
        width:100%;
        height:100%;
        display:flex;
        align-items:center;
        justify-content:center;
        color:#aeb6d6;
        font-size:13px;
        font-weight:700;
        letter-spacing:.02em;
      }}

      .adcat-body {{
        padding:14px 14px 16px;
      }}

      .adcat-body h3 {{
        margin:0 0 10px;
        color:#fff;
        font-size:17px;
        line-height:1.15;
        font-weight:900;
      }}

      .adcat-body .meta {{
        margin:0 0 8px;
        color:#d7d7e7;
        font-size:14px;
        line-height:1.35;
      }}

      .adcat-body .reward {{
        margin:0 0 14px;
        color:#d98cff;
        font-size:15px;
        line-height:1.35;
        font-weight:900;
      }}

      .watch-btn {{
        display:block;
        width:100%;
        text-align:center;
        padding:12px 14px;
        border-radius:16px;
        text-decoration:none;
        color:#fff;
        font-size:15px;
        font-weight:900;
        background:linear-gradient(180deg,#b85cff 0%, #8b3dff 100%);
        box-shadow:inset 0 0 0 1px rgba(255,255,255,.14);
      }}

      .add-slot-wrap {{
        padding:14px 14px 0;
      }}

      .add-slot-bar {{
        display:flex;
        align-items:center;
        justify-content:center;
        width:100%;
        height:50px;
        border-radius:16px;
        text-decoration:none;
        color:#fff;
        font-size:15px;
        font-weight:900;
        border:1px dashed rgba(154,103,255,.6);
        background:linear-gradient(180deg,rgba(27,17,50,.96) 0%, rgba(16,10,30,.96) 100%);
        box-shadow:0 8px 20px rgba(0,0,0,.25);
      }}

      .add-slot-bar .plus {{
        font-size:22px;
        line-height:1;
        margin-right:8px;
        color:#dca8ff;
      }}
    </style>

    <div class="adcat-shell">
      <div class="adcat-hero">
        <div class="eyebrow">INFINI AD MARKET</div>
        <h1>{title}</h1>
        <p>แตะรูปด้านบนของแต่ละช่องเพื่ออัปโหลดหรือเปลี่ยนสื่อ และกดปุ่ม “ดูโฆษณา” เพื่อเปิดรายการ</p>
        <div class="adcat-count">{total_slots} ช่องโฆษณา</div>
      </div>

      <div class="adcat-grid">
        {rows}
      </div>

      <div class="add-slot-wrap">
        <a class="add-slot-bar" href="/normal-ad-upload/{category}-{total_slots + 1}?back_url=/tower/ad-market/{category}">
          <span class="plus">＋</span> เพิ่มช่องโฆษณา
        </a>
      </div>
    </div>
    """)
'''

p.write_text(s[:start] + new_block + "\n" + s[end:], encoding="utf-8")
print("CATEGORY_CLEAN_V1_OK")
