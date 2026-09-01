from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

app = FastAPI(title="INFINI Point Tower")

USER_POINTS = 12450

STYLE = """
<style>
*{box-sizing:border-box}
body{
 margin:0;background:radial-gradient(circle at top,#231052,#050611 55%);
 color:#fff;font-family:Arial,sans-serif
}
.wrap{max-width:1000px;margin:auto;padding:18px}
header{
 display:flex;justify-content:space-between;align-items:center;
 padding:16px;border:1px solid #864aff;border-radius:18px;
 background:#0d1022;margin-bottom:18px
}
.logo{font-size:22px;font-weight:bold;color:#b96cff}
.points{color:#62dcff}
.panel{
 background:#0d1124;border:1px solid #7139c9;border-radius:18px;
 padding:18px;margin-bottom:16px
}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{
 display:block;padding:18px;min-height:130px;border-radius:16px;
 background:linear-gradient(145deg,#11162d,#221448);
 border:1px solid #7d45db;color:white;text-decoration:none
}
.card:hover{box-shadow:0 0 20px #863fff}
.card h3{margin:0 0 8px;color:#d8b8ff}
.card p{color:#aaa6be}
.btn{
 display:inline-block;padding:13px 18px;background:#7432d7;
 border:1px solid #aa71ff;border-radius:12px;color:white;
 text-decoration:none;font-weight:bold
}
.btn.alt{background:transparent}
.list{display:grid;gap:14px}
.row{
 display:grid;grid-template-columns:150px 1fr auto;
 gap:14px;align-items:center
}
.placeholder{
 min-height:100px;border-radius:12px;background:
 linear-gradient(135deg,#301277,#071328);
 display:grid;place-items:center;color:#c7a4ff
}
input,textarea,select{
 width:100%;padding:13px;margin-bottom:10px;
 border-radius:10px;border:1px solid #6738ae;
 background:#080c19;color:white
}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.summary div{text-align:center;padding:14px}
nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.media{
 min-height:65vh;display:grid;place-items:center;
 background:#090c19;border:1px solid #6e3ac2;border-radius:18px;
 font-size:28px;text-align:center;padding:20px
}
.controls{
 display:grid;grid-template-columns:repeat(4,1fr);
 gap:10px;margin-top:12px
}
@media(max-width:700px){
 .grid{grid-template-columns:1fr}
 .cols{grid-template-columns:1fr}
 .row{grid-template-columns:100px 1fr}
 .row .action{grid-column:1/-1}
 .summary{grid-template-columns:1fr}
}

/* === AD MARKET CARD RIGHT FILL SAFE === */
/* เติมพื้นที่ด้านขวาของการ์ดหมวดโฆษณา ไม่แตะระบบอัปโหลด */
a.card[href^="/tower/ad-market/"] {
  position: relative !important;
  overflow: hidden !important;
  min-height: 180px !important;
  padding-right: 150px !important;
}

a.card[href^="/tower/ad-market/"]::before {
  content: "";
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  width: 104px;
  height: 104px;
  border-radius: 28px;
  border: 1px solid rgba(190,110,255,.55);
  background:
    radial-gradient(circle at 35% 30%, rgba(190,110,255,.9), transparent 28%),
    radial-gradient(circle at 70% 75%, rgba(55,220,255,.45), transparent 30%),
    linear-gradient(135deg, rgba(60,20,120,.85), rgba(5,8,25,.9));
  box-shadow: 0 0 28px rgba(150,70,255,.55);
  opacity: .95;
}

a.card[href^="/tower/ad-market/"]::after {
  content: "AD";
  position: absolute;
  right: 42px;
  top: 50%;
  transform: translateY(-50%);
  color: white;
  font-size: 26px;
  font-weight: 1000;
  letter-spacing: 1px;
  text-shadow: 0 0 16px rgba(255,255,255,.65);
}

a.card[href="/tower/ad-market/tech"]::after {
  content: "TECH";
  font-size: 20px;
  right: 35px;
}

a.card[href="/tower/ad-market/fashion"]::after {
  content: "STYLE";
  font-size: 18px;
  right: 32px;
}

a.card[href="/tower/ad-market/auto"]::after {
  content: "AUTO";
  font-size: 20px;
  right: 36px;
}

a.card[href="/tower/ad-market/food"]::after {
  content: "FOOD";
  font-size: 20px;
  right: 36px;
}







</style>
"""

def page(title, content):
    return HTMLResponse(f"""
    <!doctype html>
    <html lang="th">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>{title}</title>
      {STYLE}
    </head>
    <body>
      <div class="wrap">
        <header>
          <a href="/tower" class="logo">∞ INFINI POINT TOWER</a>
          <div class="points">MY POINT {USER_POINTS:,} INF</div>
        </header>
        {content}
      </div>
    






</body>
    </html>
    """)

@app.get("/")
def root():
    return RedirectResponse("/tower")

# หน้า 1
@app.get("/tower")
def tower():
    return page("INFINI POINT TOWER", f"""
    <style>
      .wrap > header{{display:none}}
      html,body{{background:#000!important}}
      body{{background-image:none!important}}
      .wrap{{max-width:760px!important;padding:14px 14px 110px!important}}
      .ptv2,.ptv2 *{{box-sizing:border-box}}
      .ptv2{{color:#fff}}
      .ptv2-top{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:2px 2px 14px}}
      .ptv2-brand small{{display:block;color:#8f8ca0;font-size:10px;letter-spacing:1.7px}}
      .ptv2-brand strong{{display:block;margin-top:3px;font-size:20px;letter-spacing:1.2px}}
      .ptv2-brand b{{color:#b34dff;font-size:28px;vertical-align:-2px}}
      .ptv2-point{{padding:10px 13px;border:1px solid rgba(83,216,255,.28);border-radius:16px;background:#090c14;color:#66ddff;text-align:right}}
      .ptv2-point small{{display:block;color:#8f8ca0;font-size:9px;font-weight:800;letter-spacing:1px}}
      .ptv2-point strong{{font-size:18px}}
      .ptv2-search{{display:flex;align-items:center;gap:10px;height:50px;padding:0 15px;border:1px solid rgba(155,72,255,.25);border-radius:17px;background:#090a10}}
      .ptv2-search span{{color:#68e3ff;font-size:20px}}
      .ptv2-search input{{width:100%;margin:0;border:0;outline:0;background:transparent;color:#fff;font:inherit}}
      .ptv2-search input::placeholder{{color:#716e80}}
      .ptv2-hero{{position:relative;overflow:hidden;min-height:246px;margin-top:14px;border:1px solid rgba(157,75,255,.52);border-radius:25px;background:linear-gradient(145deg,#15102c,#080912 70%);box-shadow:0 18px 44px rgba(0,0,0,.42)}}
      .ptv2-hero img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.72}}
      .ptv2-hero::after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(4,5,13,.93) 0%,rgba(4,5,13,.55) 55%,rgba(4,5,13,.18)),linear-gradient(0deg,rgba(6,3,18,.9),transparent 58%)}}
      .ptv2-hero-copy{{position:relative;z-index:2;max-width:68%;padding:25px 21px}}
      .ptv2-hero-copy small{{color:#78e6ff;font-size:10px;font-weight:900;letter-spacing:1.5px}}
      .ptv2-hero-copy h1{{margin:10px 0 9px;font-size:clamp(31px,9vw,47px);line-height:.96;letter-spacing:-1.8px}}
      .ptv2-hero-copy p{{margin:0;color:#c2bfd0;font-size:13px;line-height:1.55}}
      .ptv2-hero-copy a{{display:inline-flex;margin-top:18px;padding:11px 16px;border:1px solid rgba(202,103,255,.55);border-radius:14px;background:linear-gradient(135deg,#7c2dff,#b946ff);color:#fff;text-decoration:none;font-weight:900}}
      .ptv2-upload{{margin-top:12px;padding:11px 12px;border:1px solid rgba(156,75,255,.22);border-radius:17px;background:#08090e}}
      .ptv2-upload-title{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px}}
      .ptv2-upload-title strong{{font-size:13px}}
      .ptv2-upload-title span{{color:#7f7c89;font-size:10px}}
      .ptv2-upload form{{display:flex;gap:8px}}
      .ptv2-upload input{{min-width:0;flex:1;margin:0;padding:9px 10px;border:1px solid rgba(160,85,255,.20);border-radius:11px;background:#040509;color:#8e8b97;font-size:10px}}
      .ptv2-upload button{{flex:0 0 auto;padding:0 13px;border:0;border-radius:11px;background:linear-gradient(135deg,#7d2eff,#bd48ff);color:#fff;font-weight:900}}
      .ptv2-section-head{{display:flex;align-items:end;justify-content:space-between;gap:12px;margin:22px 2px 12px}}
      .ptv2-section-head h2{{margin:0;font-size:17px}}
      .ptv2-section-head span{{color:#8c8998;font-size:11px}}
      .ptv2-quick{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}}
      .ptv2-quick a{{min-width:0;padding:13px 6px;border:1px solid rgba(151,75,255,.22);border-radius:17px;background:#0a0b12;color:#fff;text-align:center;text-decoration:none}}
      .ptv2-quick b{{display:flex;width:38px;height:38px;margin:0 auto 8px;align-items:center;justify-content:center;border-radius:13px;background:rgba(137,53,255,.13);color:#c879ff;font-size:19px}}
      .ptv2-quick span{{display:block;overflow:hidden;text-overflow:ellipsis;font-size:10px;font-weight:800;white-space:nowrap}}
      .ptv2-stats{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
      .ptv2-stat{{padding:14px;border:1px solid rgba(151,75,255,.20);border-radius:18px;background:#090a10}}
      .ptv2-stat small{{display:block;color:#8f8c9d;font-size:9px;letter-spacing:1px}}
      .ptv2-stat strong{{display:block;margin-top:5px;font-size:18px}}
      .ptv2-stat span{{display:block;margin-top:3px;color:#6fddff;font-size:10px}}
      .ptv2-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}}
      .ptv2-card{{position:relative;min-height:184px;display:flex;flex-direction:column;overflow:hidden;padding:14px;border:1px solid rgba(151,75,255,.25);border-radius:21px;background:radial-gradient(circle at 80% 16%,rgba(171,62,255,.18),transparent 26%),#090a11;color:#fff;text-decoration:none}}
      .ptv2-card em{{display:flex;width:48px;height:48px;align-items:center;justify-content:center;border:1px solid rgba(184,99,255,.27);border-radius:15px;background:rgba(114,42,214,.10);color:#ca78ff;font-size:22px;font-style:normal}}
      .ptv2-card h3{{margin:18px 0 7px;font-size:18px;line-height:1.1}}
      .ptv2-card p{{margin:0;color:#9d9aaa;font-size:11px;line-height:1.45}}
      .ptv2-card footer{{display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:15px;color:#70e2ff;font-size:11px;font-weight:900}}
      .ptv2-card footer b{{display:flex;width:31px;height:31px;align-items:center;justify-content:center;border:1px solid rgba(88,222,255,.24);border-radius:50%;color:#fff}}
      .ptv2-note{{margin-top:11px;padding:15px;border:1px solid rgba(67,234,170,.20);border-radius:18px;background:#07100e;color:#bdeeda;font-size:12px;line-height:1.55}}
      .ptv2-nav{{position:sticky;bottom:8px;z-index:20;display:grid;grid-template-columns:repeat(5,1fr);gap:3px;margin-top:24px;padding:9px;border:1px solid rgba(148,75,255,.25);border-radius:23px;background:rgba(6,7,12,.96);backdrop-filter:blur(14px);box-shadow:0 16px 35px rgba(0,0,0,.45)}}
      .ptv2-nav a{{padding:7px 2px;color:#777485;text-align:center;text-decoration:none;font-size:9px}}
      .ptv2-nav b{{display:block;margin-bottom:3px;color:#a974ff;font-size:19px}}
      .ptv2-nav .active{{color:#fff}}
      .ptv2-nav .active b{{color:#fff;text-shadow:0 0 14px #b84cff}}
      @media(max-width:380px){{.ptv2-hero-copy{{max-width:74%}}.ptv2-quick{{gap:7px}}.ptv2-quick span{{font-size:9px}}.ptv2-card{{min-height:174px;padding:12px}}.ptv2-card h3{{font-size:16px}}}}
    </style>

    <main class="ptv2">
      <section class="ptv2-top">
        <div class="ptv2-brand"><small>INFINI ACTIVITY POINT</small><strong>POINT TOWER <b>∞</b></strong></div>
        <div class="ptv2-point"><small>MY POINT</small><strong>{USER_POINTS:,} INF</strong></div>
      </section>

      <label class="ptv2-search"><span>⌕</span><input id="ptv2Search" type="search" placeholder="ค้นหาเมนู กิจกรรม หรือรางวัล"></label>

      <section class="ptv2-hero">
        <img src="/tower/header-image" alt="INFINI POINT TOWER" onerror="this.style.display='none'">
        <div class="ptv2-hero-copy">
          <small>ACTIVITY • MISSION • REWARD</small>
          <h1>POINT<br>TOWER</h1>
          <p>ชมกิจกรรม รับ INF แลกรางวัล และใช้สิทธิ์กับร้านค้าพาร์ทเนอร์</p>
          <a href="/tower/dashboard">เริ่มใช้งาน →</a>
        </div>
      </section>

      <section class="ptv2-upload">
        <div class="ptv2-upload-title"><strong>เปลี่ยนภาพหัวข้อ</strong><span>แตะเลือกภาพแล้วอัปโหลด</span></div>
        <form method="post" action="/tower/header-upload" enctype="multipart/form-data">
          <input type="file" name="file" accept="image/*" required>
          <button type="submit">อัปโหลด</button>
        </form>
      </section>

      <div class="ptv2-section-head"><h2>QUICK ACCESS</h2><span>เมนูหลัก</span></div>
      <section class="ptv2-quick">
        <a href="/tower/dashboard"><b>▣</b><span>หน้าหลัก</span></a>
        <a href="/tower/ad-market"><b>▶</b><span>รับแต้ม</span></a>
        <a href="/tower/rewards"><b>★</b><span>รางวัล</span></a>
        <a href="/tower/cards"><b>▤</b><span>การ์ด</span></a>
      </section>

      <div class="ptv2-section-head"><h2>STATUS</h2><span>ข้อมูลเดิมของระบบ</span></div>
      <section class="ptv2-stats">
        <div class="ptv2-stat"><small>MY POINT</small><strong>{USER_POINTS:,} INF</strong><span>พร้อมใช้ในระบบ</span></div>
        <div class="ptv2-stat"><small>CAMPAIGN</small><strong>6 ACTIVE</strong><span>แคมเปญเปิดอยู่</span></div>
        <div class="ptv2-stat"><small>REWARD CARD</small><strong>120+</strong><span>การ์ดและรางวัล</span></div>
        <div class="ptv2-stat"><small>PARTNER</small><strong>28 SHOP</strong><span>ร้านค้าพาร์ทเนอร์</span></div>
      </section>

      <div class="ptv2-section-head"><h2>MY CONTENT</h2><span>เลือกใช้งาน</span></div>
      <section class="ptv2-grid" id="ptv2Grid">
        <a class="ptv2-card" data-search="tower dashboard wallet" href="/tower/dashboard"><em>∞</em><h3>ENTER TOWER</h3><p>ดูยอดแต้ม Wallet Campaign และกิจกรรมในระบบ</p><footer><span>เข้าสู่ตึก</span><b>→</b></footer></a>
        <a class="ptv2-card" data-search="earn ad market mission" href="/tower/ad-market"><em>▶</em><h3>HOW TO EARN</h3><p>เลือกกิจกรรมและชมสื่อเพื่อรับ INF</p><footer><span>เริ่มรับแต้ม</span><b>→</b></footer></a>
        <a class="ptv2-card" data-search="rewards partner shop" href="/tower/rewards"><em>★</em><h3>REWARDS</h3><p>เลือกและแลกรางวัลจากระบบและร้านค้าพาร์ทเนอร์</p><footer><span>ดูรางวัล</span><b>→</b></footer></a>
        <a class="ptv2-card" data-search="card system book" href="/tower/cards"><em>▤</em><h3>CARD SYSTEM</h3><p>ออกสำเนา สมุดการ์ด ตรวจและใช้สิทธิ์</p><footer><span>เปิดระบบการ์ด</span><b>→</b></footer></a>
        <a class="ptv2-card" data-search="history transaction" href="/tower/transaction?type=history"><em>◷</em><h3>ประวัติ</h3><p>ดูรายการย้อนหลังและความเคลื่อนไหวในระบบ</p><footer><span>ดูประวัติ</span><b>→</b></footer></a>
        <a class="ptv2-card" data-search="my point wallet" href="/tower/transaction?type=wallet"><em>◆</em><h3>MY POINT</h3><p>ดูกระเป๋าแต้มและยอดคงเหลือของสมาชิก</p><footer><span>เปิดกระเป๋า</span><b>→</b></footer></a>
      </section>

      <section class="ptv2-note"><strong>POINT ECONOMY SYSTEM</strong><br>ดูแคมเปญ รับ INF แปลงเป็นการ์ด เก็บไว้ในกระเป๋า และนำไปใช้ตามเงื่อนไขของระบบ</section>

      <nav class="ptv2-nav">
        <a class="active" href="/tower"><b>⌂</b>HOME</a>
        <a href="/tower/dashboard"><b>▣</b>TOWER</a>
        <a href="/tower/ad-market"><b>▶</b>EARN</a>
        <a href="/tower/rewards"><b>★</b>REWARD</a>
        <a href="/tower/cards"><b>▤</b>CARD</a>
      </nav>
    </main>

    <script>
      (() => {{
        const input = document.getElementById("ptv2Search");
        const cards = Array.from(document.querySelectorAll(".ptv2-card"));
        if (!input) return;
        input.addEventListener("input", () => {{
          const q = input.value.trim().toLowerCase();
          cards.forEach(card => {{
            const text = (card.dataset.search + " " + card.textContent).toLowerCase();
            card.style.display = !q || text.includes(q) ? "" : "none";
          }});
        }});
      }})();
    </script>
    """)

# หน้า 2
@app.get("/tower/dashboard")
def dashboard():
    return page("Dashboard", """
    <div class="panel">
      <h1>Point Tower Dashboard</h1>
      <p>เลือกสิ่งที่ต้องการทำ</p>
    </div>

    <div class="grid">
      <a class="card" href="/tower/transaction?type=buy-point">
        <h3>ซื้อแต้ม</h3><p>เข้าสู่ห้องธุรกรรม</p>
      </a>

      <a class="card" href="/tower/transaction?type=create-campaign">
        <h3>สร้างแคมเปญ</h3><p>อัปโหลดและตั้งค่ากิจกรรม</p>
      </a>

      <a class="card" href="/tower/ad-market">
        <h3>เลือกชมโฆษณา</h3><p>เลือกหมวดและรับแต้ม</p>
      </a>

      <a class="card" href="/tower/rewards">
        <h3>แลกรางวัล</h3><p>ดูของรางวัลพิเศษ</p>
      </a>

      <a class="card" href="/tower/transaction?type=history">
        <h3>ประวัติ</h3><p>ดูรายการย้อนหลัง</p>
      </a>

      <a class="card" href="/tower/transaction?type=wallet">
        <h3>MY POINT</h3><p>ดูกระเป๋าแต้ม</p>
      </a>

      <a class="card" href="/tower/cards">
        <h3>CARD SYSTEM</h3>
        <p>ออกสำเนา · สมุดการ์ด · ตรวจและแลก</p>
      </a>
    </div>
    """)

# หน้า 3
@app.get("/tower/ad-market")
def ad_market():
    from ad_market_layout_editor_8046 import render_ad_market_page
    return render_ad_market_page(page, USER_POINTS)


# หน้า 4
from pathlib import Path as _AdSlotPath

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
    category_name = category.upper()
    cards = ""

    for i in range(1, 7):
        ad_id = f"{category}-{i}"
        cards += f"""
        <article class="adfv2-card">
          <div class="adfv2-media">{normal_ad_media_html(ad_id)}</div>
          <div class="adfv2-copy">
            <div class="adfv2-title"><h3>{category_name} #{i}</h3><span>30 วินาที</span></div>
            <div class="adfv2-meta"><strong>รับ 5 INF</strong><small>งบคงเหลือ 8,500 INF</small></div>
            <a class="adfv2-watch" href="/tower/ad/{ad_id}">เปิดดู →</a>
          </div>
        </article>
        """

    return page("รายการกิจกรรม", f"""
    <style>
      .wrap > header{{display:none}}
      html,body{{background:#000!important}}
      body{{background-image:none!important}}
      .wrap{{max-width:760px!important;padding:14px 14px 110px!important}}
      .adfv2,.adfv2 *{{box-sizing:border-box}}
      .adfv2{{color:#fff}}
      .adfv2-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}}
      .adfv2-back{{display:flex;width:42px;height:42px;align-items:center;justify-content:center;border:1px solid rgba(154,77,255,.25);border-radius:14px;background:#090a10;color:#fff;text-decoration:none;font-size:20px}}
      .adfv2-name small{{display:block;color:#817e8d;font-size:9px;letter-spacing:1.3px}}
      .adfv2-name h1{{margin:3px 0 0;font-size:24px}}
      .adfv2-points{{padding:9px 12px;border:1px solid rgba(83,216,255,.24);border-radius:14px;background:#080b10;color:#66ddff;text-align:right}}
      .adfv2-points small{{display:block;color:#817e8d;font-size:8px;letter-spacing:1px}}
      .adfv2-points strong{{font-size:15px}}
      .adfv2-intro{{margin-bottom:14px;padding:14px 15px;border:1px solid rgba(154,77,255,.19);border-radius:18px;background:#08090e}}
      .adfv2-intro h2{{margin:0;font-size:17px}}
      .adfv2-intro p{{margin:6px 0 0;color:#9693a1;font-size:11px;line-height:1.45}}
      .adfv2-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
      .adfv2-card{{overflow:hidden;border:1px solid rgba(151,72,255,.24);border-radius:20px;background:#090a10}}
      .adfv2-media{{padding:0;background:#030305}}
      .adfv2-media>a{{width:100%!important;aspect-ratio:4/5!important;border-radius:0!important;background:#030305!important}}
      .adfv2-media img,.adfv2-media video{{object-fit:cover!important}}
      .adfv2-media>a>span{{display:none!important}}
      .adfv2-copy{{padding:12px}}
      .adfv2-title{{display:flex;align-items:flex-start;justify-content:space-between;gap:7px}}
      .adfv2-title h3{{margin:0;font-size:15px;line-height:1.15}}
      .adfv2-title span{{flex:0 0 auto;color:#8e8b98;font-size:9px}}
      .adfv2-meta{{display:flex;flex-direction:column;gap:3px;margin-top:9px}}
      .adfv2-meta strong{{color:#ffd56d;font-size:12px}}
      .adfv2-meta small{{color:#797684;font-size:9px}}
      .adfv2-watch{{display:flex;align-items:center;justify-content:center;margin-top:11px;padding:10px;border-radius:12px;background:linear-gradient(135deg,#7628e8,#a934f2);color:#fff;text-decoration:none;font-size:11px;font-weight:900}}
      .adfv2-upload-note{{display:flex;align-items:center;justify-content:center;margin-top:11px;padding:10px 12px;border:1px dashed rgba(151,72,255,.28);border-radius:13px;background:#050609;color:#8d8997;font-size:10px;text-align:center}}
      .adfv2-nav{{position:sticky;bottom:8px;z-index:20;display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:22px;padding:8px;border:1px solid rgba(148,75,255,.23);border-radius:21px;background:rgba(6,7,12,.96);backdrop-filter:blur(14px)}}
      .adfv2-nav a{{padding:8px 2px;color:#777485;text-align:center;text-decoration:none;font-size:9px}}
      .adfv2-nav b{{display:block;margin-bottom:3px;color:#a974ff;font-size:18px}}
      .adfv2-nav .active{{color:#fff}}
      @media(max-width:360px){{.adfv2-grid{{gap:8px}}.adfv2-copy{{padding:10px}}.adfv2-title h3{{font-size:13px}}}}
    </style>

    <main class="adfv2">
      <section class="adfv2-head">
        <a class="adfv2-back" href="/tower/ad-market">←</a>
        <div class="adfv2-name"><small>AD MARKET</small><h1>{category_name}</h1></div>
        <div class="adfv2-points"><small>MY POINT</small><strong>{USER_POINTS:,} INF</strong></div>
      </section>

      <section class="adfv2-intro"><h2>กิจกรรม {category_name}</h2><p>เลือกช่องที่ต้องการ ดูครบตามเวลา แล้วรับแต้มตามเงื่อนไขเดิม</p></section>
      <section class="adfv2-grid">{cards}</section>
      <div class="adfv2-upload-note">แตะรูปในแต่ละช่องเพื่ออัปโหลดหรือเปลี่ยนสื่อ</div>

      <nav class="adfv2-nav">
        <a href="/tower"><b>⌂</b>HOME</a>
        <a class="active" href="/tower/ad-market"><b>▶</b>EARN</a>
        <a href="/tower/rewards"><b>★</b>REWARD</a>
        <a href="/tower/cards"><b>▤</b>CARD</a>
      </nav>
    </main>
    """)

# หน้า 5
@app.get("/tower/ad/{ad_id}")
def watch_ad(ad_id: str):
    return page("ดูสื่อกิจกรรม", f"""
    <style>
      .wrap > header{{display:none}}
      html,body{{background:#000!important}}
      body{{background-image:none!important}}
      .wrap{{max-width:760px!important;padding:14px 14px 70px!important}}
      .watchv2,.watchv2 *{{box-sizing:border-box}}
      .watchv2{{color:#fff}}
      .watchv2-top{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:13px}}
      .watchv2-top a{{display:flex;width:42px;height:42px;align-items:center;justify-content:center;border:1px solid rgba(154,77,255,.25);border-radius:14px;background:#090a10;color:#fff;text-decoration:none;font-size:20px}}
      .watchv2-top h1{{margin:0;font-size:18px}}
      .watchv2-top span{{color:#68ddff;font-size:12px;font-weight:900}}
      .watchv2-media{{overflow:hidden;border:1px solid rgba(151,72,255,.25);border-radius:22px;background:#030305}}
      .watchv2-media>.media{{min-height:auto!important;padding:0!important;border:0!important;border-radius:0!important;background:#030305!important}}
      .watchv2-media .media>a{{width:100%!important;aspect-ratio:4/5!important;border-radius:0!important}}
      .watchv2-media .media>a>span{{display:none!important}}
      .watchv2-info{{margin-top:12px;padding:13px 14px;border:1px solid rgba(151,72,255,.18);border-radius:17px;background:#08090e}}
      .watchv2-info small{{color:#7f7c89}}
      .watchv2-info strong{{display:block;margin-top:3px;color:#ffd56d;font-size:14px}}
      .watchv2-actions{{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin-top:12px}}
      .watchv2-actions a{{display:flex;align-items:center;justify-content:center;min-height:45px;border:1px solid rgba(151,72,255,.23);border-radius:14px;background:#090a10;color:#fff;text-decoration:none;font-size:11px;font-weight:900}}
      .watchv2-actions .primary{{border:0;background:linear-gradient(135deg,#7628e8,#a934f2)}}
    </style>

    <main class="watchv2">
      <section class="watchv2-top"><a href="javascript:history.back()">←</a><h1>ดูสื่อกิจกรรม</h1><span>+5 INF</span></section>
      <section class="watchv2-media"><div class="media">{normal_ad_media_html(ad_id)}</div></section>
      <section class="watchv2-info"><small>รหัสรายการ</small><strong>{ad_id}</strong></section>
      <section class="watchv2-actions">
        <a href="/normal-ad-upload/{ad_id}?back_url=/tower/ad/{ad_id}">เปลี่ยนสื่อ</a>
        <a class="primary" href="/tower/transaction?type=ad-view&ref={ad_id}">รับแต้ม / ธุรกรรม</a>
        <a href="/tower">หน้าโฮม</a>
        <a href="/tower/ad-market">ดูรายการอื่น</a>
      </section>
    </main>
    """)

# ห้องธุรกรรมร่วม
@app.get("/tower/transaction")
def transaction(type: str = "general", ref: str = ""):
    return page("ห้องธุรกรรม", f"""
    <div class="panel">
      <h1>ห้องธุรกรรมร่วม</h1>
      <p>ประเภท: <strong>{type}</strong></p>
      <p>รายการอ้างอิง: <strong>{ref or "-"}</strong></p>
    </div>

    <div class="panel">
      <h2>อัปโหลดและกรอกข้อมูลหลัก</h2>

      <input placeholder="ชื่อรายการ">
      <select>
        <option>เลือกโซนหรือหมวด</option>
        <option>Tech & Gadget</option>
        <option>Fashion</option>
        <option>Food & Drink</option>
        <option>Everything</option>
      </select>
      <input placeholder="แต้มที่ใช้">
      <input placeholder="แต้มที่ผู้ชมได้รับ">
      <input placeholder="แต้มคงเหลือ">
      <input placeholder="ระยะเวลาที่ต้องดู">
      <input placeholder="ลิงก์ปลายทาง">
      <textarea placeholder="รายละเอียดเพิ่มเติม"></textarea>

      <a class="btn" href="/tower/dashboard">
        บันทึกข้อมูลจำลอง
      </a>
    </div>
    """)

# หน้ารางวัล
REWARD_ITEMS = [
    ("watch",    "INFINI WATCH X1",       8900, 18),
    ("shoe",     "INFINI SNEAKER PRO",    6500, 24),
    ("gift",     "INFINI GIFT CARD",      1000, 200),
    ("bag",      "INFINI BACKPACK",       3500, 35),
    ("voucher",  "HOTEL VOUCHER",         2800, 50),
    ("vr",       "VR EXPERIENCE",         1200, 40),
    ("reward07", "INFINI REWARD 07",      1500, 30),
    ("reward08", "INFINI REWARD 08",      1800, 30),
    ("reward09", "INFINI REWARD 09",      2100, 25),
    ("reward10", "INFINI REWARD 10",      2400, 25),
    ("reward11", "INFINI REWARD 11",      2700, 20),
    ("reward12", "INFINI REWARD 12",      3000, 20),
    ("reward13", "INFINI REWARD 13",      3300, 18),
    ("reward14", "INFINI REWARD 14",      3600, 18),
    ("reward15", "INFINI REWARD 15",      3900, 15),
    ("reward16", "INFINI REWARD 16",      4200, 15),
    ("reward17", "INFINI REWARD 17",      4500, 12),
    ("reward18", "INFINI REWARD 18",      4800, 12),
    ("reward19", "INFINI REWARD 19",      5200, 10),
    ("reward20", "INFINI REWARD 20",      5900, 10),
]

# รางวัลทั่วไปใช้รหัสคนละชุดกับรางวัลพิเศษ
# จึงเริ่มต้นเป็นช่องเปล่า และไม่ดึงรูปเดิมของรางวัลพิเศษมาใช้
BASIC_REWARD_ITEMS = [
    ("basic01", "รางวัลทั่วไป 01", 0, 0),
    ("basic02", "รางวัลทั่วไป 02", 0, 0),
    ("basic03", "รางวัลทั่วไป 03", 0, 0),
    ("basic04", "รางวัลทั่วไป 04", 0, 0),
    ("basic05", "รางวัลทั่วไป 05", 0, 0),
    ("basic06", "รางวัลทั่วไป 06", 0, 0),
    ("basic07", "รางวัลทั่วไป 07", 0, 0),
    ("basic08", "รางวัลทั่วไป 08", 0, 0),
    ("basic09", "รางวัลทั่วไป 09", 0, 0),
    ("basic10", "รางวัลทั่วไป 10", 0, 0),
]

def get_reward_item(reward_id: str):
    return next(
        (item for item in (REWARD_ITEMS + BASIC_REWARD_ITEMS) if item[0] == reward_id),
        None
    )

def reward_media_html(reward_id: str, large: bool = False):
    height = "420px" if large else "300px"
    media_path = f"/normal-reward-media/{reward_id}"

    return f"""
    <div style="
        position:relative;
        width:100%;
        min-height:220px;
        overflow:hidden;
        border-radius:24px;
        background:linear-gradient(145deg,#11142b,#070914);
        border:1px solid rgba(154,87,255,.55);
    ">
        <img
            src="{media_path}"
            alt="สื่อรางวัล {reward_id}"
            style="
                width:100%;
                height:auto;
                object-fit:contain;
                background:#050611;
                display:block;
            "
            onerror="
                this.style.display='none';
                this.nextElementSibling.style.display='flex';
            "
        >
        <div style="
            display:none;
            width:100%;
            height:100%;
            align-items:center;
            justify-content:center;
            text-align:center;
            color:#ae8cff;
            font-weight:800;
            padding:20px;
            box-sizing:border-box;
        ">
            แตะเข้าเพื่อดูรายละเอียด
        </div>
    </div>
    """

# หน้าเลือกรางวัล: แยกข้อมูลรางวัลทั่วไปออกจากรางวัลพิเศษอย่างชัดเจน
# - รางวัลทั่วไป = ช่องใหม่ว่าง 10 ช่อง (basic01-basic10)
# - รางวัลพิเศษ = รายการเดิมทั้งหมด พร้อมรูปเดิม


def reward_cards_html(items):
    cards = ""

    for rid, name, cost, stock in items:
        cards += f"""
        <article class="rwv2-card">
          <div class="rwv2-media">{normal_reward_media_html(rid)}</div>
          <div class="rwv2-copy">
            <h3>{name}</h3>
            <div class="rwv2-meta"><strong>{cost:,} INF</strong><span>คงเหลือ {stock}</span></div>
            <a href="/tower/redeem/{rid}">ดูรายละเอียด →</a>
          </div>
        </article>
        """

    return cards


def reward_catalog_page(title, subtitle, items):
    cards = reward_cards_html(items)
    return page(title, f"""
    <style>
      .wrap > header{{display:none}}
      html,body{{background:#000!important}}
      body{{background-image:none!important}}
      .wrap{{max-width:760px!important;padding:14px 14px 110px!important}}
      .rwv2,.rwv2 *{{box-sizing:border-box}}
      .rwv2{{color:#fff}}
      .rwv2-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}}
      .rwv2-back{{display:flex;width:42px;height:42px;align-items:center;justify-content:center;border:1px solid rgba(154,77,255,.25);border-radius:14px;background:#090a10;color:#fff;text-decoration:none;font-size:20px}}
      .rwv2-title small{{display:block;color:#817e8d;font-size:9px;letter-spacing:1.3px}}
      .rwv2-title h1{{margin:3px 0 0;font-size:22px}}
      .rwv2-point{{padding:9px 12px;border:1px solid rgba(83,216,255,.24);border-radius:14px;background:#080b10;color:#66ddff;text-align:right}}
      .rwv2-point small{{display:block;color:#817e8d;font-size:8px;letter-spacing:1px}}
      .rwv2-point strong{{font-size:15px}}
      .rwv2-intro{{margin-bottom:14px;padding:14px 15px;border:1px solid rgba(154,77,255,.18);border-radius:18px;background:#08090e}}
      .rwv2-intro p{{margin:0;color:#9693a1;font-size:11px;line-height:1.45}}
      .rwv2-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
      .rwv2-card{{overflow:hidden;border:1px solid rgba(151,72,255,.22);border-radius:20px;background:#090a10}}
      .rwv2-media{{background:#030305}}
      .rwv2-media>a{{width:100%!important;aspect-ratio:4/5!important;border-radius:0!important;background:#030305!important}}
      .rwv2-media img,.rwv2-media video{{object-fit:cover!important}}
      .rwv2-media>a>span{{display:none!important}}
      .rwv2-copy{{padding:12px}}
      .rwv2-copy h3{{margin:0;font-size:14px;line-height:1.25}}
      .rwv2-meta{{display:flex;align-items:center;justify-content:space-between;gap:7px;margin-top:8px}}
      .rwv2-meta strong{{color:#72dfff;font-size:12px}}
      .rwv2-meta span{{color:#7f7c89;font-size:9px}}
      .rwv2-copy>a{{display:flex;align-items:center;justify-content:center;margin-top:10px;padding:9px;border:1px solid rgba(151,72,255,.20);border-radius:11px;background:#0c0d14;color:#fff;text-decoration:none;font-size:10px;font-weight:900}}
      .rwv2-nav{{position:sticky;bottom:8px;z-index:20;display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:22px;padding:8px;border:1px solid rgba(148,75,255,.23);border-radius:21px;background:rgba(6,7,12,.96);backdrop-filter:blur(14px)}}
      .rwv2-nav a{{padding:8px 2px;color:#777485;text-align:center;text-decoration:none;font-size:9px}}
      .rwv2-nav b{{display:block;margin-bottom:3px;color:#a974ff;font-size:18px}}
      .rwv2-nav .active{{color:#fff}}
      @media(max-width:360px){{.rwv2-grid{{gap:8px}}.rwv2-copy{{padding:10px}}.rwv2-copy h3{{font-size:13px}}}}
    </style>

    <main class="rwv2">
      <section class="rwv2-head">
        <a class="rwv2-back" href="/tower/rewards">←</a>
        <div class="rwv2-title"><small>REWARD MARKET</small><h1>{title}</h1></div>
        <div class="rwv2-point"><small>MY POINT</small><strong>{USER_POINTS:,} INF</strong></div>
      </section>
      <section class="rwv2-intro"><p>{subtitle}</p></section>
      <section class="rwv2-grid">{cards}</section>
      <nav class="rwv2-nav">
        <a href="/tower"><b>⌂</b>HOME</a>
        <a href="/tower/ad-market"><b>▶</b>EARN</a>
        <a class="active" href="/tower/rewards"><b>★</b>REWARD</a>
        <a href="/tower/cards"><b>▤</b>CARD</a>
      </nav>
    </main>
    """)

@app.get("/tower/rewards")
def rewards():
    return page("หมวดรางวัล", f"""
    <style>
      .wrap > header{{display:none}}
      html,body{{background:#000!important}}
      body{{background-image:none!important}}
      .wrap{{max-width:760px!important;padding:14px 14px 100px!important}}
      .rselv2,.rselv2 *{{box-sizing:border-box}}
      .rselv2{{color:#fff}}
      .rselv2-top{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}}
      .rselv2-top a{{display:flex;width:42px;height:42px;align-items:center;justify-content:center;border:1px solid rgba(154,77,255,.25);border-radius:14px;background:#090a10;color:#fff;text-decoration:none;font-size:20px}}
      .rselv2-title small{{display:block;color:#817e8d;font-size:9px;letter-spacing:1.3px}}
      .rselv2-title h1{{margin:3px 0 0;font-size:22px}}
      .rselv2-point{{padding:9px 12px;border:1px solid rgba(83,216,255,.24);border-radius:14px;background:#080b10;color:#66ddff;text-align:right}}
      .rselv2-point small{{display:block;color:#817e8d;font-size:8px;letter-spacing:1px}}
      .rselv2-point strong{{font-size:15px}}
      .rselv2-copy{{margin-bottom:14px;padding:14px 15px;border:1px solid rgba(154,77,255,.18);border-radius:18px;background:#08090e;color:#9693a1;font-size:11px;line-height:1.45}}
      .rselv2-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
      .rselv2-card{{position:relative;display:flex;min-height:270px;flex-direction:column;overflow:hidden;padding:17px;border:1px solid rgba(151,72,255,.26);border-radius:22px;background:radial-gradient(circle at 80% 17%,rgba(177,67,255,.20),transparent 28%),#090a10;color:#fff;text-decoration:none}}
      .rselv2-card.basic{{border-color:rgba(81,218,255,.24);background:radial-gradient(circle at 80% 17%,rgba(48,205,255,.16),transparent 28%),#090a10}}
      .rselv2-icon{{display:flex;width:50px;height:50px;align-items:center;justify-content:center;border:1px solid rgba(177,92,255,.28);border-radius:15px;background:rgba(126,43,220,.10);color:#cf78ff;font-size:25px}}
      .rselv2-card.basic .rselv2-icon{{border-color:rgba(83,218,255,.25);background:rgba(40,166,205,.08);color:#65ddff}}
      .rselv2-card h2{{margin:22px 0 8px;font-size:21px;line-height:1.1}}
      .rselv2-card p{{margin:0;color:#9693a1;font-size:11px;line-height:1.5}}
      .rselv2-action{{display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:20px;color:#fff;font-size:11px;font-weight:900}}
      .rselv2-action b{{display:flex;width:31px;height:31px;align-items:center;justify-content:center;border:1px solid rgba(151,72,255,.25);border-radius:50%}}
      .rselv2-nav{{position:sticky;bottom:8px;display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:22px;padding:8px;border:1px solid rgba(148,75,255,.23);border-radius:21px;background:rgba(6,7,12,.96);backdrop-filter:blur(14px)}}
      .rselv2-nav a{{padding:8px 2px;color:#777485;text-align:center;text-decoration:none;font-size:9px}}
      .rselv2-nav b{{display:block;margin-bottom:3px;color:#a974ff;font-size:18px}}
      .rselv2-nav .active{{color:#fff}}
      @media(max-width:360px){{.rselv2-card{{min-height:245px;padding:14px}}.rselv2-card h2{{font-size:18px}}}}
    </style>

    <main class="rselv2">
      <section class="rselv2-top">
        <a href="/tower">←</a>
        <div class="rselv2-title"><small>POINT TOWER</small><h1>REWARD MARKET</h1></div>
        <div class="rselv2-point"><small>MY POINT</small><strong>{USER_POINTS:,} INF</strong></div>
      </section>
      <section class="rselv2-copy">เลือกประเภทรางวัลที่ต้องการ รายการและข้อมูลเดิมยังคงอยู่ครบ</section>
      <section class="rselv2-grid">
        <a class="rselv2-card basic" href="/tower/rewards/basic"><div class="rselv2-icon">◇</div><h2>รางวัลทั่วไป</h2><p>ของใช้ทั่วไป อาหาร เสื้อผ้า และรายการสำหรับสมาชิก</p><div class="rselv2-action"><span>เปิดรายการ</span><b>→</b></div></a>
        <a class="rselv2-card" href="/tower/rewards/special"><div class="rselv2-icon">★</div><h2>รางวัลพิเศษ</h2><p>ของพรีเมียม Limited และรางวัลมูลค่าสูง</p><div class="rselv2-action"><span>เปิดรายการ</span><b>→</b></div></a>
      </section>
      <nav class="rselv2-nav">
        <a href="/tower"><b>⌂</b>HOME</a>
        <a href="/tower/ad-market"><b>▶</b>EARN</a>
        <a class="active" href="/tower/rewards"><b>★</b>REWARD</a>
        <a href="/tower/cards"><b>▤</b>CARD</a>
      </nav>
    </main>
    """)

@app.get("/tower/rewards/basic")
def basic_rewards():
    return reward_catalog_page(
        "รางวัลทั่วไป",
        "รายการทั่วไป 10 ช่อง แยกข้อมูลและรูปออกจากรางวัลพิเศษ",
        BASIC_REWARD_ITEMS,
    )

@app.get("/tower/rewards/special")
def special_rewards():
    return reward_catalog_page(
        "รางวัลพิเศษ",
        "ของพรีเมียม Limited และรางวัลมูลค่าสูงจากระบบ",
        REWARD_ITEMS,
    )

# หน้ารูปใหญ่และรายละเอียดของแต่ละช่อง
@app.get("/tower/redeem/{reward_id}")
def redeem_form(reward_id: str):
    item = get_reward_item(reward_id)

    if item is None:
        return page("ไม่พบรางวัล", """
        <div class="panel">
            <h1>ไม่พบรางวัลนี้</h1>
            <a class="btn" href="/tower/rewards">กลับหน้ารางวัล</a>
        </div>
        """)

    rid, name, cost, stock = item
    remaining = USER_POINTS - cost

    return page("ยืนยันการแลก", f"""
    <div class="panel">
        <h1>ยืนยันการแลกของรางวัล</h1>
        <p>รหัสรางวัล: {rid}</p>
    </div>

    <div class="cols">
        <div class="panel">
            {normal_reward_media_html(rid, large=True)}

            <a class="btn"
               href="/normal-reward-upload/{rid}?back_url=/tower/redeem/{rid}">
                อัปโหลดหรือเปลี่ยนรูป
            </a>

            <h2>{name}</h2>
            <p>จำนวนคงเหลือ: {stock} ชิ้น</p>
            <p>ใช้แต้ม: <strong style="color:#ffd66d">{cost:,} INF</strong></p>
        </div>

        <div class="panel">
            <div class="summary">
                <div class="panel">
                    ก่อนแลก<br>
                    <strong>{USER_POINTS:,} INF</strong>
                </div>

                <div class="panel">
                    ใช้<br>
                    <strong>{cost:,} INF</strong>
                </div>

                <div class="panel">
                    คงเหลือ<br>
                    <strong>{remaining:,} INF</strong>
                </div>
            </div>

            <form method="post" action="/tower/redeem/{reward_id}">
                <input
                    name="recipient_name"
                    placeholder="ชื่อ-นามสกุลผู้รับ"
                    required
                >

                <input
                    name="phone"
                    placeholder="เบอร์โทรศัพท์"
                    required
                >

                <input
                    name="email"
                    type="email"
                    placeholder="อีเมล"
                    required
                >

                <textarea
                    name="address"
                    placeholder="ที่อยู่จัดส่ง"
                ></textarea>

                <textarea
                    name="note"
                    placeholder="หมายเหตุเพิ่มเติม"
                ></textarea>

                <label>
                    <input
                        type="checkbox"
                        name="accept"
                        required
                        style="width:auto"
                    >
                    ยอมรับเงื่อนไขการแลก
                </label>

                <br><br>

                <button class="btn" type="submit">
                    ยืนยันการแลก
                </button>
            </form>
        </div>
    </div>
    """)

@app.post("/tower/redeem/{reward_id}")
def redeem_submit(
    reward_id: str,
    recipient_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    address: str = Form(""),
    note: str = Form(""),
    accept: str = Form(...)
):
    return RedirectResponse(
      f"/tower/success?reward={reward_id}",
      status_code=303
    )

# หน้าสำเร็จ
@app.get("/tower/success")
def success(reward: str):
    return page("สำเร็จ", f"""
    <div class="panel" style="text-align:center;padding:50px">
      <h1>ทำรายการสำเร็จ</h1>
      <p>รางวัล: {reward}</p>
      <p>เลขธุรกรรม: TX-INFINI-0001</p>
      <p>
        ตอนนี้เป็นข้อมูลจำลอง<br>
        ระบบหักแต้มและลดจำนวนจริงค่อยเชื่อมภายหลัง
      </p>
      <a class="btn" href="/tower/dashboard">
        กลับ Point Tower
      </a>
    </div>
    """)

from fastapi import File, UploadFile
from pathlib import Path
import shutil
import uuid


CONTROL_UPLOAD_DIR = Path.home() / "downloads" / "infini_point_tower" / "uploads"
CONTROL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/tower/control-room")
def control_room():
    return page("INFINI Point Tower Control Room", """
    <div class="panel">
      <h1>∞ INFINI POINT TOWER CONTROL ROOM</h1>
      <p>
        อัปโหลด จัดหมวด ตั้งค่า และเชื่อมไปยังหน้าที่ต้องการ
      </p>
    </div>

    <form method="post"
          action="/tower/control-room"
          enctype="multipart/form-data">

      <!-- 1. เลือกปลายทาง -->
      <div class="panel">
        <h2>1. เลือกปลายทาง</h2>
        <p>เลือกหน้าที่ต้องการส่งข้อมูลไปแสดง</p>

        <select name="destination"
                id="destination"
                onchange="changeControlFields()"
                required>
          <option value="">— เลือกหน้าปลายทาง —</option>
          <option value="tower">หน้าแรก Point Tower</option>
          <option value="dashboard">Dashboard</option>
          <option value="ad-market">AD Market</option>
          <option value="ad-list">รายการโฆษณา</option>
          <option value="ad-view">หน้าดูโฆษณา</option>
          <option value="reward">หน้าแลกรางวัล</option>
          <option value="campaign">หน้าแคมเปญ</option>
        </select>
      </div>

      <div class="cols">

        <div>
          <!-- 2. อัปโหลดสื่อ -->
          <div class="panel">
            <h2>2. อัปโหลดสื่อ</h2>

            <select name="media_type" required>
              <option value="image">รูปภาพ</option>
              <option value="video">วิดีโอ</option>
              <option value="cover">ภาพปก</option>
              <option value="banner">แบนเนอร์</option>
            </select>

            <input type="file"
                   name="media"
                   id="mediaInput"
                   accept="image/*,video/*"
                   onchange="previewMedia(event)"
                   required>

            <div id="uploadPreview"
                 class="placeholder"
                 style="min-height:220px">
              ตัวอย่างรูปหรือวิดีโอ
            </div>
          </div>

          <!-- 3. ข้อมูลหลัก -->
          <div class="panel">
            <h2>3. ข้อมูลหลัก</h2>

            <label>ชื่อรายการ</label>
            <input name="title"
                   id="titleInput"
                   placeholder="ชื่อโฆษณา รางวัล หรือแคมเปญ"
                   oninput="updatePreview()"
                   required>

            <label>หัวข้อ</label>
            <input name="headline"
                   placeholder="ข้อความหัวเรื่อง">

            <label>คำอธิบาย</label>
            <textarea name="description"
                      id="descriptionInput"
                      placeholder="รายละเอียดของรายการ"
                      oninput="updatePreview()"></textarea>

            <label>หมวดหรือโซน</label>
            <select name="category">
              <option value="everything">Everything</option>
              <option value="tech">Tech &amp; Gadget</option>
              <option value="fashion">Fashion</option>
              <option value="auto">Auto &amp; Vehicle</option>
              <option value="food">Food &amp; Drink</option>
              <option value="game">Game &amp; Entertainment</option>
              <option value="finance">Finance &amp; Investment</option>
              <option value="health">Health &amp; Beauty</option>
              <option value="travel">Travel &amp; Hotel</option>
              <option value="real-estate">Real Estate</option>
              <option value="education">Education</option>
              <option value="lifestyle">Lifestyle</option>
            </select>

            <label>สถานะ</label>
            <select name="status">
              <option value="draft">ฉบับร่าง</option>
              <option value="review">รอตรวจสอบ</option>
              <option value="active">เผยแพร่</option>
              <option value="closed">ปิดรายการ</option>
            </select>
          </div>

          <!-- 4A. ข้อมูลโฆษณา -->
          <div class="panel"
               id="adFields"
               style="display:none">
            <h2>4. ข้อมูลเฉพาะโฆษณา</h2>

            <label>แต้มที่ใช้สร้างแคมเปญ</label>
            <input type="number"
                   name="campaign_points"
                   min="0"
                   value="0">

            <label>แต้มที่ผู้ชมได้รับ</label>
            <input type="number"
                   name="viewer_reward"
                   min="0"
                   value="0">

            <label>งบหรือแต้มคงเหลือ</label>
            <input type="number"
                   name="budget_left"
                   min="0"
                   value="0">

            <label>เวลาที่ต้องดู</label>
            <select name="watch_seconds">
              <option value="15">15 วินาที</option>
              <option value="30">30 วินาที</option>
              <option value="60">1 นาที</option>
              <option value="120">2 นาที</option>
            </select>

            <label>ลิงก์ปลายทาง</label>
            <input type="url"
                   name="target_url"
                   placeholder="https://...">
          </div>

          <!-- 4B. ข้อมูลรางวัล -->
          <div class="panel"
               id="rewardFields"
               style="display:none">
            <h2>4. ข้อมูลเฉพาะของรางวัล</h2>

            <label>แต้มที่ใช้แลก</label>
            <input type="number"
                   name="reward_cost"
                   id="rewardCost"
                   min="0"
                   value="0"
                   oninput="updatePointSummary()">

            <label>จำนวนของคงเหลือ</label>
            <input type="number"
                   name="reward_stock"
                   min="0"
                   value="0">

            <label>ประเภทของรางวัล</label>
            <select name="reward_type">
              <option value="physical">สินค้าจริง</option>
              <option value="digital">ดิจิทัล</option>
              <option value="voucher">คูปอง</option>
              <option value="experience">ประสบการณ์</option>
            </select>

            <label>วิธีรับของ</label>
            <select name="delivery_method">
              <option value="shipping">จัดส่งถึงที่อยู่</option>
              <option value="email">ส่งทางอีเมล</option>
              <option value="pickup">รับด้วยตนเอง</option>
            </select>

            <label>เงื่อนไขการแลก</label>
            <textarea name="reward_terms"
                      placeholder="ระบุเงื่อนไขของรางวัล"></textarea>
          </div>

          <!-- 4C. ข้อมูลแคมเปญ -->
          <div class="panel"
               id="campaignFields"
               style="display:none">
            <h2>4. ข้อมูลเฉพาะแคมเปญ</h2>

            <label>งบแคมเปญ</label>
            <input type="number"
                   name="campaign_budget"
                   min="0"
                   value="0">

            <label>วันเริ่มต้น</label>
            <input type="date"
                   name="start_date">

            <label>วันสิ้นสุด</label>
            <input type="date"
                   name="end_date">

            <label>กลุ่มเป้าหมาย</label>
            <input name="target_audience"
                   placeholder="เช่น ผู้สนใจเทคโนโลยี อายุ 18–35 ปี">
          </div>
        </div>

        <!-- 5. ตัวอย่าง -->
        <div>
          <div class="panel"
               style="position:sticky;top:14px">
            <h2>5. ตัวอย่างก่อนเผยแพร่</h2>

            <div class="panel">
              <div id="cardPreview"
                   class="placeholder"
                   style="min-height:320px">
                ตัวอย่างสื่อ
              </div>

              <h2 id="previewTitle"
                  style="margin-top:18px">
                ชื่อรายการ
              </h2>

              <p id="previewDescription">
                รายละเอียดจะแสดงตรงนี้
              </p>

              <a class="btn"
                 style="width:100%;text-align:center">
                ดูรายการ
              </a>
            </div>

            <div class="panel">
              <h3>สรุปการใช้แต้ม</h3>

              <p>
                แต้มคงเหลือปัจจุบัน
                <strong style="float:right">
                  12,450 INF
                </strong>
              </p>

              <p>
                แต้มที่ใช้
                <strong id="previewCost"
                        style="float:right;color:#ff6978">
                  0 INF
                </strong>
              </p>

              <p>
                แต้มคงเหลือหลังทำรายการ
                <strong id="previewRemaining"
                        style="float:right;color:#63f5a5">
                  12,450 INF
                </strong>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 6. ปุ่มควบคุม -->
      <div class="panel">
        <h2>6. ปุ่มควบคุม</h2>

        <div class="grid">
          <button class="btn alt"
                  type="submit"
                  name="action"
                  value="draft">
            บันทึกฉบับร่าง
          </button>

          <button class="btn alt"
                  type="button"
                  onclick="window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                  })">
            ดูตัวอย่าง
          </button>

          <button class="btn"
                  type="submit"
                  name="action"
                  value="publish">
            อัปโหลดและเผยแพร่
          </button>

          <a class="btn alt"
             href="/tower/transaction?type=control-room">
            ห้องธุรกรรม
          </a>

          <a class="btn alt"
             href="/tower/dashboard">
            กลับ Dashboard
          </a>
        </div>
      </div>
    </form>

    <script>
      function changeControlFields() {
        const value =
          document.getElementById("destination").value;

        const adFields =
          document.getElementById("adFields");

        const rewardFields =
          document.getElementById("rewardFields");

        const campaignFields =
          document.getElementById("campaignFields");

        adFields.style.display = "none";
        rewardFields.style.display = "none";
        campaignFields.style.display = "none";

        if (
          value === "ad-market" ||
          value === "ad-list" ||
          value === "ad-view"
        ) {
          adFields.style.display = "block";
        }

        if (value === "reward") {
          rewardFields.style.display = "block";
        }

        if (value === "campaign") {
          campaignFields.style.display = "block";
        }
      }

      function previewMedia(event) {
        const file = event.target.files[0];

        if (!file) {
          return;
        }

        const url = URL.createObjectURL(file);

        const uploadPreview =
          document.getElementById("uploadPreview");

        const cardPreview =
          document.getElementById("cardPreview");

        if (file.type.startsWith("video/")) {
          uploadPreview.innerHTML =
            '<video controls style="width:100%;' +
            'max-height:260px;border-radius:12px">' +
            '<source src="' + url + '">' +
            '</video>';

          cardPreview.innerHTML =
            '<video controls style="width:100%;' +
            'max-height:320px;border-radius:12px">' +
            '<source src="' + url + '">' +
            '</video>';
        } else {
          uploadPreview.innerHTML =
            '<img src="' + url + '" ' +
            'style="width:100%;max-height:260px;' +
            'object-fit:contain;background:#050611;border-radius:12px">';

          cardPreview.innerHTML =
            '<img src="' + url + '" ' +
            'style="width:100%;max-height:320px;' +
            'object-fit:contain;background:#050611;border-radius:12px">';
        }
      }

      function updatePreview() {
        const title =
          document.getElementById("titleInput").value;

        const description =
          document.getElementById(
            "descriptionInput"
          ).value;

        document.getElementById(
          "previewTitle"
        ).textContent = title || "ชื่อรายการ";

        document.getElementById(
          "previewDescription"
        ).textContent =
          description || "รายละเอียดจะแสดงตรงนี้";
      }

      function updatePointSummary() {
        const cost =
          Number(
            document.getElementById(
              "rewardCost"
            ).value || 0
          );

        const currentPoints = 12450;
        const remaining =
          Math.max(0, currentPoints - cost);

        document.getElementById(
          "previewCost"
        ).textContent =
          cost.toLocaleString() + " INF";

        document.getElementById(
          "previewRemaining"
        ).textContent =
          remaining.toLocaleString() + " INF";
      }
    </script>
    """)


@app.post("/tower/control-room")
async def control_room_submit(
    destination: str = Form(...),
    media_type: str = Form(...),
    media: UploadFile = File(...),

    title: str = Form(...),
    headline: str = Form(""),
    description: str = Form(""),
    category: str = Form("everything"),
    status: str = Form("draft"),

    campaign_points: int = Form(0),
    viewer_reward: int = Form(0),
    budget_left: int = Form(0),
    watch_seconds: int = Form(30),
    target_url: str = Form(""),

    reward_cost: int = Form(0),
    reward_stock: int = Form(0),
    reward_type: str = Form("physical"),
    delivery_method: str = Form("shipping"),
    reward_terms: str = Form(""),

    campaign_budget: int = Form(0),
    start_date: str = Form(""),
    end_date: str = Form(""),
    target_audience: str = Form(""),

    action: str = Form("draft")
):
    extension = Path(
        media.filename or "upload.bin"
    ).suffix.lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".mp4",
        ".mov",
        ".webm"
    }

    if extension not in allowed_extensions:
        return page(
            "อัปโหลดไม่สำเร็จ",
            """
            <div class="panel">
              <h1>ชนิดไฟล์ไม่รองรับ</h1>
              <p>
                รองรับ JPG, PNG, WEBP, GIF,
                MP4, MOV และ WEBM
              </p>
              <a class="btn"
                 href="/tower/control-room">
                กลับห้องควบคุม
              </a>
            </div>
            """
        )

    safe_filename = (
        uuid.uuid4().hex + extension
    )

    file_path = (
        CONTROL_UPLOAD_DIR / safe_filename
    )

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(
            media.file,
            buffer
        )

    if action == "draft":
        return RedirectResponse(
            "/tower/transaction"
            "?type=control-draft"
            f"&ref={safe_filename}",
            status_code=303
        )

    if destination == "tower":
        target = "/tower"

    elif destination == "dashboard":
        target = "/tower/dashboard"

    elif destination == "reward":
        target = "/tower/rewards"

    elif destination == "campaign":
        target = (
            "/tower/transaction"
            "?type=campaign"
            f"&ref={safe_filename}"
        )

    elif destination in {
        "ad-market",
        "ad-list",
        "ad-view"
    }:
        target = (
            f"/tower/ad-market/"
            f"{category or 'everything'}"
        )

    else:
        target = "/tower/dashboard"

    return RedirectResponse(
        target,
        status_code=303
    )

# เพิ่มแผงอัปโหลดรูปหน้าแรก Point Tower
from home_upload_panel import setup_home_upload_panel
setup_home_upload_panel(app)


from dashboard_upload_panel import setup_dashboard_upload_panel
setup_dashboard_upload_panel(app)


# ad_market_upload_panel รุ่นเดิมปิดไว้ เพราะใช้เครื่องมือจัดหน้ารุ่นใหม่
from ad_market_layout_editor_8046 import setup_ad_market_layout_editor
setup_ad_market_layout_editor(app)

if __name__ == "__main__":
    uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=8046,
      reload=True
    )

from video_ad_upload import setup_video_upload
setup_video_upload(app)

from member_home import setup_member_home
setup_member_home(app)

from reward_images import setup_reward_images
setup_reward_images(app)

from normal_reward_images import setup_normal_reward_images, _media_block as _normal_reward_media_block
setup_normal_reward_images(app)

# === REWARD MEDIA COMPAT WRAPPER ===
# ใช้ normal reward media เป็นระบบหลัก แต่รับ argument เก่าได้ด้วย
def normal_reward_media_html(reward_id, *args, **kwargs):
    detail = bool(kwargs.get("detail", False))
    try:
        return _normal_reward_media_block(str(reward_id), detail=detail)
    except TypeError:
        return _normal_reward_media_block(str(reward_id))



from normal_ad_images import setup_normal_ad_images, _media_block as _normal_ad_media_block
setup_normal_ad_images(app)

# === NORMAL AD MEDIA DISPLAY WRAPPER ===
def normal_ad_media_html(ad_id, *args, **kwargs):
    detail = bool(kwargs.get("detail", False))
    try:
        return _normal_ad_media_block(str(ad_id), detail=detail)
    except TypeError:
        return _normal_ad_media_block(str(ad_id))


# === TOWER HEADER REAL UPLOAD PATCH ===
from pathlib import Path as _TowerPath
from fastapi import UploadFile as _TowerUploadFile, File as _TowerFile
from fastapi.responses import RedirectResponse as _TowerRedirectResponse, FileResponse as _TowerFileResponse
from starlette.responses import Response as _TowerResponse

_TOWER_HEADER_DIR = _TowerPath("data/tower_header")
_TOWER_HEADER_CURRENT = _TOWER_HEADER_DIR / "current.txt"

@app.post("/tower/header-upload")
async def tower_header_upload(file: _TowerUploadFile = _TowerFile(...)):
    _TOWER_HEADER_DIR.mkdir(parents=True, exist_ok=True)

    name = file.filename or "header.jpg"
    ext = _TowerPath(name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        return _TowerRedirectResponse("/tower", status_code=303)

    data = await file.read()
    if not data:
        return _TowerRedirectResponse("/tower", status_code=303)

    if len(data) > 15 * 1024 * 1024:
        return _TowerRedirectResponse("/tower", status_code=303)

    out = _TOWER_HEADER_DIR / ("header" + ext)
    out.write_bytes(data)
    _TOWER_HEADER_CURRENT.write_text(out.name, encoding="utf-8")

    return _TowerRedirectResponse("/tower", status_code=303)

@app.get("/tower/header-image")
def tower_header_image():
    try:
        name = _TOWER_HEADER_CURRENT.read_text(encoding="utf-8").strip()
        target = _TOWER_HEADER_DIR / name
        if target.exists():
            return _TowerFileResponse(
                target,
                headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
            )
    except Exception:
        pass

    return _TowerResponse(status_code=404)
# === END TOWER HEADER REAL UPLOAD PATCH ===
# ======================================================
# INFINI CARD COPY SYSTEM — TEMPLATE FIRST
# เลือกลาย -> ระบุจำนวน -> คำนวณราคา -> ออก QR -> ดาวน์โหลด ZIP
# ======================================================
from fastapi.staticfiles import StaticFiles as _CardStaticFiles
from pathlib import Path as _CardPath
from fastapi.responses import (
    HTMLResponse as _CardHTMLResponse,
    RedirectResponse as _CardRedirectResponse,
    JSONResponse as _CardJSONResponse,
    Response as _CardResponse,
)
from fastapi import (
    Form as _CardForm,
    File as _CardFile,
    UploadFile as _CardUploadFile,
    Request as _CardRequest,
)
import json as _card_json
import time as _card_time
import hmac as _card_hmac
import hashlib as _card_hashlib
import secrets as _card_secrets
import html as _card_html
import io as _card_io
import zipfile as _card_zipfile
import csv as _card_csv
from datetime import datetime as _CardDateTime, timezone as _CardTimezone

import qrcode as _card_qrcode
from qrcode.image.svg import SvgPathImage as _CardSvgPathImage

_CARD_BASE = _CardPath(__file__).resolve().parent
_CARD_ASSET_DIR = _CARD_BASE / "tower_card_assets"
_CARD_TEMPLATE_DIR = _CARD_ASSET_DIR / "templates"
_CARD_DATA_DIR = _CARD_BASE / "data"
_CARD_DATA_FILE = _CARD_DATA_DIR / "point_card_system.json"
_CARD_SECRET_FILE = _CARD_DATA_DIR / "point_card_secret.txt"
_CARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
_CARD_ASSET_DIR.mkdir(parents=True, exist_ok=True)
_CARD_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# วิดีโอ/รูปเป็นหน้าตาการ์ด การรับรองจริงมาจากข้อมูลบนเซิร์ฟเวอร์
app.mount(
    "/tower-card-assets",
    _CardStaticFiles(directory=str(_CARD_ASSET_DIR)),
    name="tower-card-assets",
)


def _card_now_iso():
    return _CardDateTime.now(_CardTimezone.utc).isoformat()


def _card_builtin_templates():
    return [
        {
            "id": "builtin-activity",
            "name": "ACTIVITY POINT",
            "value_inf": 50,
            "media_url": "/tower-card-assets/card_live.mp4",
            "media_type": "video",
            "builtin": True,
        },
        {
            "id": "builtin-book",
            "name": "INFINI CARD BOOK",
            "value_inf": 50,
            "media_url": "/tower-card-assets/card_book.mp4",
            "media_type": "video",
            "builtin": True,
        },
    ]


def _card_default_state():
    return {
        "version": 2,
        "wallet": {
            "available_inf": 100000,
            "reserved_inf": 0,
            "redeemed_inf": 0,
            "system_fee_inf": 0,
        },
        "templates": [],
        "campaigns": [],
        "copies": [],
    }


def _card_save_state(data):
    tmp = _CARD_DATA_FILE.with_suffix(".tmp")
    tmp.write_text(
        _card_json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(_CARD_DATA_FILE)
    return data


def _card_load_state():
    if not _CARD_DATA_FILE.exists():
        return _card_save_state(_card_default_state())
    try:
        data = _card_json.loads(_CARD_DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        broken = _CARD_DATA_FILE.with_name(
            f"point_card_system.broken.{int(_card_time.time())}.json"
        )
        try:
            _CARD_DATA_FILE.replace(broken)
        except Exception:
            pass
        data = _card_default_state()

    data.setdefault("version", 2)
    data.setdefault("wallet", {})
    data["wallet"].setdefault("available_inf", 100000)
    data["wallet"].setdefault("reserved_inf", 0)
    data["wallet"].setdefault("redeemed_inf", 0)
    data["wallet"].setdefault("system_fee_inf", 0)
    data.setdefault("templates", [])
    data.setdefault("campaigns", [])
    data.setdefault("copies", [])

    # การ์ดเก่าที่ยังไม่มีสื่อ ให้ใช้ลาย ACTIVITY POINT เดิม
    for campaign in data["campaigns"]:
        campaign.setdefault("template_id", "builtin-activity")
        campaign.setdefault("media_url", "/tower-card-assets/card_live.mp4")
        campaign.setdefault("media_type", "video")
        campaign.setdefault(
            "total_inf",
            int(campaign.get("value_inf", 0)) * int(campaign.get("quantity", 0)),
        )
    for copy in data["copies"]:
        copy.setdefault("template_id", "builtin-activity")
        copy.setdefault("media_url", "/tower-card-assets/card_live.mp4")
        copy.setdefault("media_type", "video")
    return data


def _card_templates(data):
    result = []
    seen = set()
    for item in _card_builtin_templates() + list(data.get("templates", [])):
        tid = str(item.get("id", ""))
        if not tid or tid in seen:
            continue
        seen.add(tid)
        result.append(item)
    return result


def _card_find_template(data, template_id: str):
    return next(
        (t for t in _card_templates(data) if t.get("id") == template_id),
        None,
    )


def _card_secret():
    if not _CARD_SECRET_FILE.exists():
        _CARD_SECRET_FILE.write_text(_card_secrets.token_hex(32), encoding="utf-8")
    return _CARD_SECRET_FILE.read_text(encoding="utf-8").strip().encode("utf-8")


def _card_live_code(token: str, slot=None):
    if slot is None:
        slot = int(_card_time.time()) // 15
    raw = f"{token}:{slot}".encode("utf-8")
    digest = _card_hmac.new(_card_secret(), raw, _card_hashlib.sha256).hexdigest()
    return digest[:8].upper()


def _card_verify_live_code(token: str, code: str):
    clean = (code or "").strip().upper()
    current_slot = int(_card_time.time()) // 15
    return any(
        _card_hmac.compare_digest(clean, _card_live_code(token, current_slot - offset))
        for offset in (0, 1)
    )


def _card_find_by_token(data, token: str):
    return next((c for c in data.get("copies", []) if c.get("token") == token), None)


def _card_find_by_serial(data, serial: str):
    target = (serial or "").strip().upper()
    return next(
        (c for c in data.get("copies", []) if str(c.get("serial", "")).upper() == target),
        None,
    )


def _card_find_campaign(data, campaign_id: str):
    return next(
        (c for c in data.get("campaigns", []) if c.get("id") == campaign_id),
        None,
    )


def _card_status_text(status: str):
    return {
        "active": "พร้อมแลก",
        "redeemed": "ใช้แล้ว",
        "cancelled": "ยกเลิก",
    }.get(status, "ไม่ทราบสถานะ")


def _card_safe(value):
    return _card_html.escape(str(value or ""), quote=True)


def _card_media_html(obj, css_class="templateMedia", controls=False):
    url = _card_safe(obj.get("media_url", "/tower-card-assets/card_live.mp4"))
    media_type = obj.get("media_type", "video")
    if media_type == "video":
        attrs = "controls" if controls else "muted autoplay loop playsinline"
        return f'<video class="{css_class}" src="{url}" {attrs} preload="metadata"></video>'
    return f'<img class="{css_class}" src="{url}" alt="ลายการ์ด">'


def _card_shell(title: str, body: str):
    return _CardHTMLResponse(f"""
    <!doctype html>
    <html lang="th">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
      <title>{_card_safe(title)}</title>
      <style>
        *{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
        body{{margin:0;background:radial-gradient(circle at top,#2b0b59,#070713 56%,#020205);color:#fff;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}}
        .cw{{max-width:920px;margin:auto;padding:16px 16px 90px}}
        .ctop{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}}
        .ctop a{{color:#d9b9ff;text-decoration:none;font-weight:900}}
        .panel{{border:1px solid rgba(159,79,255,.7);border-radius:26px;background:linear-gradient(145deg,rgba(14,16,40,.96),rgba(40,14,78,.9));padding:18px;margin-bottom:16px;box-shadow:0 0 26px rgba(128,43,255,.18)}}
        h1,h2,h3{{margin-top:0}} p{{color:#c8bdd9;line-height:1.55}}
        .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
        .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
        .choice{{display:block;text-decoration:none;color:white;min-height:170px}}
        .choice b{{font-size:25px;color:#e5c9ff}}
        .choice span{{display:block;color:#c7b8d8;margin-top:10px;line-height:1.45}}
        .btn{{display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(190,120,255,.75);border-radius:16px;background:linear-gradient(135deg,#742ce7,#a64cff);color:#fff;padding:12px 16px;font-weight:900;text-decoration:none;font:inherit;cursor:pointer;margin:4px}}
        .btn.alt{{background:#0b1020;color:#ddc9ff}}
        input{{width:100%;padding:13px;border-radius:14px;border:1px solid rgba(170,90,255,.6);background:#080b18;color:white;font:inherit;margin:6px 0 13px}}
        input[type=file]{{padding:12px}}
        label{{display:block;color:#eadcff;font-weight:900;margin-top:5px}}
        .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
        .stat{{padding:14px;border-radius:18px;background:#080b18;border:1px solid rgba(157,78,255,.42)}}
        .stat small{{display:block;color:#a99dbb}} .stat b{{display:block;font-size:20px;margin-top:5px}}
        .templateGrid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
        .templateCard{{display:block;color:white;text-decoration:none;border:1px solid rgba(160,83,255,.62);border-radius:24px;overflow:hidden;background:#080b18;box-shadow:0 0 22px rgba(125,44,255,.17)}}
        .templateFrame{{position:relative;aspect-ratio:3/4;background:#020205;overflow:hidden}}
        .templateMedia{{width:100%;height:100%;object-fit:cover;display:block}}
        .templateText{{padding:14px}}
        .templateText b{{display:block;font-size:20px;color:#e5c9ff}}
        .templateText span{{display:block;color:#7dffd0;margin-top:5px;font-weight:900}}
        .detailFrame{{position:relative;overflow:hidden;border-radius:28px;background:#020205;border:1px solid rgba(147,76,255,.75);aspect-ratio:3/4;box-shadow:0 0 32px rgba(105,40,255,.35)}}
        .detailMedia{{width:100%;height:100%;object-fit:contain;background:#000;display:block}}
        .priceBox{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}}
        .priceBox div{{padding:14px;border:1px solid rgba(160,90,255,.45);border-radius:17px;background:#080b18}}
        .priceBox small{{display:block;color:#a99dbb}}
        .priceBox b{{display:block;font-size:22px;color:#7dffd0;margin-top:4px}}
        .cardVisual{{position:relative;overflow:hidden;border-radius:28px;background:#020205;border:1px solid rgba(147,76,255,.75);aspect-ratio:3/4;box-shadow:0 0 32px rgba(105,40,255,.35)}}
        .cardVisual img,.cardVisual video{{width:100%;height:100%;object-fit:cover;display:block}}
        .shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.03),rgba(0,0,0,.1) 48%,rgba(0,0,0,.9));pointer-events:none}}
        .cardInfo{{position:absolute;left:14px;right:14px;bottom:14px;z-index:2}}
        .serial{{font-size:12px;letter-spacing:.08em;color:#cdb4ff}}
        .cardName{{font-size:24px;font-weight:1000;line-height:1.05;margin:4px 0}}
        .live{{display:inline-flex;align-items:center;gap:7px;margin-top:8px;padding:8px 11px;border-radius:999px;background:rgba(0,0,0,.68);border:1px solid rgba(89,255,194,.72);font-weight:1000;color:#7dffd0}}
        .dot{{width:8px;height:8px;border-radius:50%;background:#62ffbd;box-shadow:0 0 12px #62ffbd;animation:pulse 1s infinite alternate}}
        @keyframes pulse{{to{{opacity:.35}}}}
        .status{{display:inline-block;padding:7px 10px;border-radius:999px;font-weight:900;font-size:12px}}
        .status.active{{background:rgba(38,255,168,.14);color:#79ffd0;border:1px solid rgba(38,255,168,.5)}}
        .status.redeemed{{background:rgba(255,92,118,.14);color:#ff9aac;border:1px solid rgba(255,92,118,.5)}}
        .bookHero{{overflow:hidden;padding:0}}
        .bookHero video{{width:100%;max-height:420px;object-fit:cover;display:block}}
        .bookText{{padding:18px}}
        .copyrow{{display:grid;grid-template-columns:92px 1fr;gap:12px;align-items:center;border:1px solid rgba(160,90,255,.45);border-radius:18px;padding:13px;margin:10px 0;background:#080b18}}
        .copyrow img{{width:92px;height:92px;background:white;border-radius:12px;padding:5px}}
        .copyrow code{{display:block;overflow-wrap:anywhere;color:#7be6ff;margin:7px 0}}
        .resultOk{{border-color:rgba(70,255,178,.65);background:linear-gradient(145deg,rgba(8,56,40,.88),rgba(7,15,28,.95))}}
        .resultBad{{border-color:rgba(255,90,110,.65);background:linear-gradient(145deg,rgba(75,15,28,.88),rgba(7,15,28,.95))}}
        .qrPanel{{display:grid;grid-template-columns:150px 1fr;gap:16px;align-items:center}}
        .qrPanel img{{width:150px;height:150px;background:white;padding:7px;border-radius:16px}}
        @media(max-width:680px){{.grid2,.grid,.templateGrid{{grid-template-columns:1fr 1fr}}.stats{{grid-template-columns:1fr 1fr}}.copyrow{{grid-template-columns:78px 1fr}}.copyrow img{{width:78px;height:78px}}.qrPanel{{grid-template-columns:1fr;text-align:center}}.qrPanel img{{margin:auto}}}}
      </style>
    </head>
    <body><div class="cw">{body}</div></body>
    </html>
    """)


def _card_public_url(request: _CardRequest, token: str):
    return str(request.base_url).rstrip("/") + f"/tower/card/{token}"


def _card_qr_svg_bytes(text: str):
    qr = _card_qrcode.QRCode(
        version=None,
        error_correction=_card_qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    image = qr.make_image(image_factory=_CardSvgPathImage)
    output = _card_io.BytesIO()
    image.save(output)
    return output.getvalue()


@app.get("/tower/cards", response_class=_CardHTMLResponse)
def tower_card_hub():
    data = _card_load_state()
    wallet = data["wallet"]
    body = f"""
      <div class="ctop"><a href="/tower/dashboard">← POINT TOWER</a><b>CARD SYSTEM</b></div>
      <div class="panel">
        <h1>ระบบสำเนาการ์ด INFINI</h1>
        <p>เลือกลายการ์ด ใส่จำนวน ระบบคำนวณราคา ออก QR และดาวน์โหลดชุดสำเนาให้ทันที</p>
        <div class="stats">
          <div class="stat"><small>พร้อมออกสำเนา</small><b>{wallet['available_inf']:,} INF</b></div>
          <div class="stat"><small>สำรองในการ์ด</small><b>{wallet['reserved_inf']:,} INF</b></div>
          <div class="stat"><small>ปิดรายการแล้ว</small><b>{wallet['redeemed_inf']:,} INF</b></div>
        </div>
      </div>
      <div class="grid2">
        <a class="panel choice" href="/tower/cards/issue"><b>เลือกลายและซื้อสำเนา</b><span>อัปโหลดลายเต็มใบหรือเลือกลายที่มี แล้วระบุจำนวนอย่างเดียว</span></a>
        <a class="panel choice" href="/tower/card-book"><b>สมุดการ์ดที่ได้รับ</b><span>เปิดลิงก์การ์ดบนเครื่องนี้แล้ว การ์ดเข้าเล่มอัตโนมัติ</span></a>
        <a class="panel choice" href="/tower/card-check"><b>ตรวจการ์ด</b><span>วางรหัสหรือ URL เพื่อตรวจสถานะจากเซิร์ฟเวอร์</span></a>
        <a class="panel choice" href="/tower/basic"><b>รางวัลเบสิก / ร้านค้า</b><span>ร้านค้าที่ผ่านระบบนำการ์ดมาให้ระบบตรวจและรวมยอด</span></a>
        <a class="panel choice" href="/tower/cards/campaigns"><b>สำเนาที่ออกแล้ว</b><span>ดู QR ลิงก์ส่งต่อ และดาวน์โหลดชุดเดิมซ้ำได้</span></a>
      </div>
    """
    return _card_shell("INFINI Card System", body)


@app.get("/tower/cards/issue", response_class=_CardHTMLResponse)
def tower_card_issue_form():
    data = _card_load_state()
    available = data["wallet"]["available_inf"]
    blocks = []
    for template in _card_templates(data):
        blocks.append(f"""
          <a class="templateCard" href="/tower/cards/template/{_card_safe(template['id'])}">
            <div class="templateFrame">{_card_media_html(template)}</div>
            <div class="templateText">
              <b>{_card_safe(template['name'])}</b>
              <span>{int(template.get('value_inf', 0)):,} INF / สำเนา</span>
            </div>
          </a>
        """)

    body = f"""
      <div class="ctop"><a href="/tower/cards">← CARD SYSTEM</a><b>เลือกลายการ์ด</b></div>
      <div class="panel">
        <h1>อัปโหลดลายการ์ดเต็มใบ</h1>
        <p>รูปหรือวิดีโอหนึ่งไฟล์จะเป็นแม่แบบของสำเนาทุกใบ แต่เลขและ QR ของแต่ละใบไม่ซ้ำกัน</p>
        <form method="post" action="/tower/cards/templates/upload" enctype="multipart/form-data">
          <label>ชื่อบนการ์ด</label>
          <input name="template_name" placeholder="เช่น ACTIVITY POINT" required>
          <label>มูลค่าต่อสำเนา (INF)</label>
          <input name="value_inf" type="number" min="1" max="100000" value="50" required>
          <label>รูปหรือวิดีโอเต็มใบ</label>
          <input name="media" type="file" accept="image/*,video/*" required>
          <button class="btn" type="submit">อัปโหลดลายการ์ด</button>
        </form>
        <p>ยอดพร้อมใช้: <b style="color:#78ffd0">{available:,} INF</b></p>
      </div>
      <h2>แตะเลือกลายการ์ด</h2>
      <div class="templateGrid">{''.join(blocks)}</div>
    """
    return _card_shell("เลือกลายการ์ด", body)


@app.post("/tower/cards/templates/upload")
async def tower_card_template_upload(
    template_name: str = _CardForm(...),
    value_inf: int = _CardForm(...),
    media: _CardUploadFile = _CardFile(...),
):
    name = (template_name or "").strip()[:100]
    if not name or value_inf < 1 or value_inf > 100000:
        return _card_shell("ข้อมูลไม่ถูกต้อง", '<div class="panel resultBad"><h1>ชื่อหรือมูลค่าไม่ถูกต้อง</h1><a class="btn" href="/tower/cards/issue">กลับ</a></div>')

    original = media.filename or "card.bin"
    ext = _CardPath(original).suffix.lower()
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    video_exts = {".mp4", ".mov", ".webm"}
    if ext not in image_exts | video_exts:
        return _card_shell("ไฟล์ไม่รองรับ", '<div class="panel resultBad"><h1>รองรับ JPG, PNG, WEBP, GIF, MP4, MOV และ WEBM</h1><a class="btn" href="/tower/cards/issue">กลับ</a></div>')

    raw = await media.read()
    if not raw or len(raw) > 40 * 1024 * 1024:
        return _card_shell("ไฟล์ไม่ถูกต้อง", '<div class="panel resultBad"><h1>ไฟล์ว่างหรือใหญ่เกิน 40 MB</h1><a class="btn" href="/tower/cards/issue">กลับ</a></div>')

    template_id = "TPL-" + _card_secrets.token_hex(6).upper()
    filename = template_id.lower() + ext
    target = _CARD_TEMPLATE_DIR / filename
    target.write_bytes(raw)

    data = _card_load_state()
    data["templates"].append({
        "id": template_id,
        "name": name,
        "value_inf": int(value_inf),
        "media_url": f"/tower-card-assets/templates/{filename}",
        "media_type": "video" if ext in video_exts else "image",
        "builtin": False,
        "created_at": _card_now_iso(),
    })
    _card_save_state(data)
    return _CardRedirectResponse(f"/tower/cards/template/{template_id}", status_code=303)


@app.get("/tower/cards/template/{template_id}", response_class=_CardHTMLResponse)
def tower_card_template_detail(template_id: str):
    data = _card_load_state()
    template = _card_find_template(data, template_id)
    if not template:
        return _card_shell("ไม่พบลาย", '<div class="panel resultBad"><h1>ไม่พบลายการ์ด</h1><a class="btn" href="/tower/cards/issue">กลับ</a></div>')

    unit = int(template.get("value_inf", 0))
    available = int(data["wallet"].get("available_inf", 0))
    body = f"""
      <div class="ctop"><a href="/tower/cards/issue">← กลับ</a><b>{_card_safe(template['name'])}</b></div>
      <div class="panel" style="padding:12px">
        <div class="detailFrame">{_card_media_html(template, 'detailMedia', controls=template.get('media_type') == 'video')}</div>
      </div>
      <div class="panel">
        <h1>{_card_safe(template['name'])}</h1>
        <p>ระบบจะออกสำเนาเป็นลายนี้ พร้อมเลขเฉพาะและ QR คนละตัวทุกใบ</p>
        <form method="post" action="/tower/cards/issue">
          <input type="hidden" name="template_id" value="{_card_safe(template_id)}">
          <label>จำนวนสำเนา</label>
          <input id="quantity" name="quantity" type="number" min="1" max="100" value="1" required>
          <div class="priceBox">
            <div><small>มูลค่าต่อสำเนา</small><b>{unit:,} INF</b></div>
            <div><small>มูลค่าการ์ดรวม</small><b id="faceTotal">{unit:,} INF</b></div>
            <div><small>ค่าระบบ 5%</small><b id="systemFee">{max(1, (unit * 5 + 99) // 100):,} INF</b></div>
            <div><small>จ่ายรวม</small><b id="totalPrice">{unit + max(1, (unit * 5 + 99) // 100):,} INF</b></div>
          </div>
          <p>ยอดพร้อมใช้: <b style="color:#78ffd0">{available:,} INF</b></p>
          <button class="btn" type="submit" style="width:100%;font-size:18px">ซื้อและออกสำเนา</button>
        </form>
      </div>
      <script>
        const unit = {unit};
        const quantity = document.getElementById('quantity');
        const faceTotal = document.getElementById('faceTotal');
        const systemFee = document.getElementById('systemFee');
        const total = document.getElementById('totalPrice');
        function updateTotal() {{
          const q = Math.max(1, Number(quantity.value || 1));
          const face = unit * q;
          const fee = Math.max(1, Math.ceil(face * 0.05));
          faceTotal.textContent = face.toLocaleString() + ' INF';
          systemFee.textContent = fee.toLocaleString() + ' INF';
          total.textContent = (face + fee).toLocaleString() + ' INF';
        }}
        quantity.addEventListener('input', updateTotal);
        updateTotal();
      </script>
    """
    return _card_shell(template["name"], body)


@app.post("/tower/cards/issue")
def tower_card_issue_submit(
    template_id: str = _CardForm("builtin-activity"),
    quantity: int = _CardForm(...),
    campaign_name: str = _CardForm(""),
    card_name: str = _CardForm(""),
    value_inf: int = _CardForm(0),
):
    data = _card_load_state()
    template = _card_find_template(data, template_id)

    # รองรับฟอร์มเวอร์ชันเก่า หากเคยเปิดค้างไว้
    if template:
        final_card_name = str(template.get("name", "ACTIVITY POINT"))[:100]
        final_value = int(template.get("value_inf", 50))
        final_media_url = str(template.get("media_url", "/tower-card-assets/card_live.mp4"))
        final_media_type = str(template.get("media_type", "video"))
    else:
        final_card_name = (card_name or "ACTIVITY POINT").strip()[:100]
        final_value = int(value_inf or 50)
        final_media_url = "/tower-card-assets/card_live.mp4"
        final_media_type = "video"
        template_id = "builtin-activity"

    if quantity < 1 or quantity > 100 or final_value < 1 or final_value > 100000:
        return _card_shell("ข้อมูลไม่ถูกต้อง", '<div class="panel resultBad"><h1>จำนวนหรือมูลค่าไม่ถูกต้อง</h1><a class="btn" href="/tower/cards/issue">กลับ</a></div>')

    face_total = final_value * quantity
    system_fee = max(1, (face_total * 5 + 99) // 100)
    purchase_total = face_total + system_fee
    wallet = data["wallet"]
    if purchase_total > int(wallet.get("available_inf", 0)):
        body = f'<div class="panel resultBad"><h1>INF ไม่พอ</h1><p>มูลค่าการ์ด {face_total:,} INF + ค่าระบบ {system_fee:,} INF = ต้องใช้ {purchase_total:,} INF</p><a class="btn" href="/tower/cards/template/{_card_safe(template_id)}">กลับ</a></div>'
        return _card_shell("INF ไม่พอ", body)

    campaign_id = "CMP-" + _card_secrets.token_hex(6).upper()
    created = _card_now_iso()
    final_campaign_name = (campaign_name or "").strip()[:100] or final_card_name
    data["campaigns"].append({
        "id": campaign_id,
        "name": final_campaign_name,
        "card_name": final_card_name,
        "template_id": template_id,
        "media_url": final_media_url,
        "media_type": final_media_type,
        "value_inf": final_value,
        "quantity": quantity,
        "total_inf": face_total,
        "system_fee_inf": system_fee,
        "purchase_total_inf": purchase_total,
        "created_at": created,
    })

    start_index = len(data["copies"]) + 1
    stamp = int(_card_time.time()) % 100000000
    for offset in range(quantity):
        token = _card_secrets.token_urlsafe(24)
        serial = f"INF-{stamp:08d}-{start_index + offset:04d}"
        data["copies"].append({
            "token": token,
            "serial": serial,
            "campaign_id": campaign_id,
            "campaign_name": final_campaign_name,
            "card_name": final_card_name,
            "template_id": template_id,
            "media_url": final_media_url,
            "media_type": final_media_type,
            "value_inf": final_value,
            "status": "active",
            "created_at": created,
            "redeemed_at": "",
        })

    wallet["available_inf"] -= purchase_total
    wallet["reserved_inf"] += face_total
    wallet["system_fee_inf"] = int(wallet.get("system_fee_inf", 0)) + system_fee
    _card_save_state(data)
    return _CardRedirectResponse(f"/tower/cards/issued/{campaign_id}?new=1", status_code=303)


@app.get("/tower/card-qr/{token}.svg")
def tower_card_qr(token: str, request: _CardRequest):
    data = _card_load_state()
    card = _card_find_by_token(data, token)
    if not card:
        return _CardResponse(status_code=404)
    svg = _card_qr_svg_bytes(_card_public_url(request, token))
    return _CardResponse(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/tower/cards/issued/{campaign_id}", response_class=_CardHTMLResponse)
def tower_cards_issued(campaign_id: str, request: _CardRequest, new: int = 0):
    data = _card_load_state()
    campaign = _card_find_campaign(data, campaign_id)
    if not campaign:
        return _card_shell("ไม่พบแคมเปญ", '<div class="panel resultBad"><h1>ไม่พบแคมเปญ</h1><a class="btn" href="/tower/cards">กลับ</a></div>')

    copies = [c for c in data["copies"] if c.get("campaign_id") == campaign_id]
    rows = []
    for card in copies:
        rows.append(
            '<div class="copyrow">'
            f'<img src="/tower/card-qr/{_card_safe(card["token"])}.svg" alt="QR">'
            '<div>'
            f'<b>{_card_safe(card["serial"])}</b> '
            f'<span class="status {card["status"]}">{_card_status_text(card["status"])}</span>'
            f'<code class="sharePath">/tower/card/{_card_safe(card["token"])}</code>'
            f'<a class="btn alt" href="/tower/card/{_card_safe(card["token"])}">เปิดการ์ด</a>'
            '</div></div>'
        )

    auto_script = """
      <script>
        setTimeout(() => { window.location.href = '/tower/cards/download/%s'; }, 900);
      </script>
    """ % _card_safe(campaign_id) if new else ""

    body = f"""
      <div class="ctop"><a href="/tower/cards">← CARD SYSTEM</a><b>สำเนาที่ออก</b></div>
      <div class="panel resultOk">
        <h1>ออกสำเนาสำเร็จ</h1>
        <p>{_card_safe(campaign['card_name'])} · {campaign['value_inf']:,} INF ต่อใบ · {len(copies)} ใบ</p>
        <h2 style="color:#78ffd0">รวม {int(campaign.get('total_inf', campaign['value_inf'] * len(copies))):,} INF</h2>
        <a class="btn" href="/tower/cards/download/{_card_safe(campaign_id)}">ดาวน์โหลด ZIP พร้อม QR</a>
        <button class="btn alt" id="copyAll">คัดลอกลิงก์ทั้งหมด</button>
        <p>หลังซื้อใหม่ ระบบจะเริ่มดาวน์โหลด ZIP ให้อัตโนมัติ และปุ่มด้านบนใช้โหลดซ้ำได้</p>
      </div>
      <div class="panel">{''.join(rows) or '<p>ยังไม่มีสำเนา</p>'}</div>
      <script>
        document.getElementById('copyAll').addEventListener('click', async () => {{
          const links = [...document.querySelectorAll('.sharePath')]
            .map(x => location.origin + x.textContent.trim()).join('\n');
          try {{ await navigator.clipboard.writeText(links); alert('คัดลอกลิงก์แล้ว'); }}
          catch(e) {{ prompt('คัดลอกลิงก์', links); }}
        }});
      </script>
      {auto_script}
    """
    return _card_shell("สำเนาที่ออก", body)


@app.get("/tower/cards/download/{campaign_id}")
def tower_cards_download(campaign_id: str, request: _CardRequest):
    data = _card_load_state()
    campaign = _card_find_campaign(data, campaign_id)
    if not campaign:
        return _CardResponse(content="campaign not found", status_code=404)
    copies = [c for c in data["copies"] if c.get("campaign_id") == campaign_id]

    links = []
    manifest_cards = []
    csv_buffer = _card_io.StringIO()
    writer = _card_csv.writer(csv_buffer)
    writer.writerow(["serial", "value_inf", "status", "url"])

    index_blocks = []
    zip_buffer = _card_io.BytesIO()
    with _card_zipfile.ZipFile(zip_buffer, "w", _card_zipfile.ZIP_DEFLATED) as zf:
        for card in copies:
            url = _card_public_url(request, card["token"])
            serial = str(card["serial"])
            qr_name = f"qr/{serial}.svg"
            zf.writestr(qr_name, _card_qr_svg_bytes(url))
            links.append(f"{serial}\t{url}")
            writer.writerow([serial, card["value_inf"], card["status"], url])
            manifest_cards.append({
                "serial": serial,
                "value_inf": card["value_inf"],
                "status": card["status"],
                "url": url,
                "qr_file": qr_name,
            })
            index_blocks.append(f"""
              <article><img src="{_card_safe(qr_name)}"><h2>{_card_safe(serial)}</h2>
              <p>{int(card['value_inf']):,} INF</p><a href="{_card_safe(url)}">เปิดการ์ดจากระบบ</a></article>
            """)

        zf.writestr("links.txt", "\n".join(links) + "\n")
        zf.writestr("cards.csv", csv_buffer.getvalue())
        zf.writestr(
            "manifest.json",
            _card_json.dumps({
                "campaign": campaign,
                "cards": manifest_cards,
            }, ensure_ascii=False, indent=2),
        )
        zf.writestr(
            "README.txt",
            "INFINI CARD COPY PACKAGE\n\n"
            "ไฟล์ QR และลิงก์เป็นทางเข้าสู่การ์ดจริงบนเซิร์ฟเวอร์\n"
            "ภาพหรือวิดีโอที่คัดลอกอย่างเดียวใช้ยืนยันหรือแลกไม่ได้\n"
            "เปิด index.html เพื่อดู QR ทุกใบในชุดนี้\n",
        )
        zf.writestr(
            "index.html",
            """<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:system-ui;background:#080612;color:white;padding:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}article{background:#17102c;border:1px solid #8d4dff;border-radius:20px;padding:16px}img{width:100%;background:white;border-radius:12px}a{color:#74eaff}</style></head><body><h1>INFINI CARD COPIES</h1><div class="grid">"""
            + "".join(index_blocks)
            + "</div></body></html>",
        )

        media_url = str(campaign.get("media_url", ""))
        prefix = "/tower-card-assets/"
        if media_url.startswith(prefix):
            rel = media_url[len(prefix):]
            source = (_CARD_ASSET_DIR / rel).resolve()
            try:
                source.relative_to(_CARD_ASSET_DIR.resolve())
                if source.exists() and source.is_file():
                    zf.write(source, f"template/{source.name}")
            except Exception:
                pass

    filename = f"infini_cards_{campaign_id}.zip"
    return _CardResponse(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/tower/cards/campaigns", response_class=_CardHTMLResponse)
def tower_card_campaigns():
    data = _card_load_state()
    blocks = []
    for campaign in reversed(data["campaigns"]):
        copies = [c for c in data["copies"] if c.get("campaign_id") == campaign.get("id")]
        active = sum(1 for c in copies if c.get("status") == "active")
        redeemed = sum(1 for c in copies if c.get("status") == "redeemed")
        blocks.append(f"""
          <a class="panel choice" href="/tower/cards/issued/{_card_safe(campaign['id'])}">
            <b>{_card_safe(campaign['name'])}</b>
            <span>{_card_safe(campaign['card_name'])} · พร้อมแลก {active} · ใช้แล้ว {redeemed}</span>
          </a>
        """)
    empty = '<div class="panel"><p>ยังไม่มีแคมเปญ</p><a class="btn" href="/tower/cards/issue">เลือกการ์ดใบแรก</a></div>'
    body = f"""
      <div class="ctop"><a href="/tower/cards">← CARD SYSTEM</a><b>แคมเปญ</b></div>
      <div class="grid2">{''.join(blocks) or empty}</div>
    """
    return _card_shell("แคมเปญการ์ด", body)


@app.get("/api/tower/cards/{token}")
def tower_card_status_api(token: str):
    data = _card_load_state()
    card = _card_find_by_token(data, token)
    if not card:
        return _CardJSONResponse({"ok": False, "error": "card_not_found"}, status_code=404)
    return _CardJSONResponse({
        "ok": True,
        "token": card["token"],
        "serial": card["serial"],
        "campaign_name": card["campaign_name"],
        "card_name": card["card_name"],
        "template_id": card.get("template_id", "builtin-activity"),
        "media_url": card.get("media_url", "/tower-card-assets/card_live.mp4"),
        "media_type": card.get("media_type", "video"),
        "value_inf": card["value_inf"],
        "status": card["status"],
        "status_text": _card_status_text(card["status"]),
        "live_code": _card_live_code(token) if card["status"] == "active" else "USED",
        "server_slot": int(_card_time.time()) // 15,
        "redeemed_at": card.get("redeemed_at", ""),
    }, headers={"Cache-Control": "no-store"})


@app.get("/tower/card/{token}", response_class=_CardHTMLResponse)
def tower_card_view(token: str):
    data = _card_load_state()
    card = _card_find_by_token(data, token)
    if not card:
        return _card_shell("ไม่พบการ์ด", '<div class="panel resultBad"><h1>ไม่พบการ์ดในระบบ</h1><p>ภาพหรือวิดีโออย่างเดียวไม่ถือว่าเป็นการ์ดจริง</p><a class="btn" href="/tower/card-check">ตรวจใบอื่น</a></div>')

    serial = _card_safe(card["serial"])
    card_name = _card_safe(card["card_name"])
    campaign_name = _card_safe(card["campaign_name"])
    status = card["status"]
    live_code = _card_live_code(token) if status == "active" else "USED"
    share_text = f"{card['serial']} · {card['value_inf']} INF"

    if status == "active":
        redeem_area = """
          <div class="panel resultOk">
            <b>การ์ดพร้อมใช้กับร้านค้าที่ผ่านระบบ</b>
            <p>แสดง QR หรือส่งลิงก์ใบนี้ให้ร้าน ร้านค้าจะนำรหัสเข้าระบบและระบบจะปิดการ์ดให้อัตโนมัติ</p>
          </div>
        """
    else:
        redeem_area = '<div class="panel resultBad"><b>การ์ดใบนี้ถูกใช้แล้ว</b><p>ระบบไม่อนุญาตให้แลกซ้ำ</p></div>'

    token_json = _card_json.dumps(token)
    title_json = _card_json.dumps(card["card_name"])
    share_json = _card_json.dumps(share_text)
    body = f"""
      <div class="ctop"><a href="/tower/cards">∞ INFINI VERIFY</a><a href="/tower/card-book">สมุดของฉัน</a></div>
      <div class="panel" style="padding:12px">
        <div class="cardVisual">
          {_card_media_html(card, 'detailMedia')}
          <div class="shade"></div>
          <div class="cardInfo">
            <div class="serial">{serial}</div>
            <div class="cardName">{card_name}</div>
            <div>{campaign_name} · {card['value_inf']:,} INF</div>
            <div class="live"><span class="dot"></span><span id="liveCode">{live_code}</span></div>
          </div>
        </div>
      </div>
      <div class="panel qrPanel">
        <img src="/tower/card-qr/{_card_safe(token)}.svg" alt="QR การ์ด">
        <div>
          <span id="statusBadge" class="status {status}">{_card_status_text(status)}</span>
          <h2 style="margin-top:14px">ระบบรับรองการ์ดใบนี้</h2>
          <p>เป็นสำเนาที่ออกจริง มี INF สำรอง และตรวจสถานะจากเซิร์ฟเวอร์ทุกครั้ง</p>
          <button class="btn alt" id="shareBtn" type="button">ส่งต่อการ์ด</button>
          <a class="btn alt" href="/tower/card-check?code={serial}">ตรวจสถานะ</a>
        </div>
      </div>
      {redeem_area}
      <script>
        const token = {token_json};
        const bookKey = 'infini_received_card_tokens_v1';
        let book = [];
        try {{ book = JSON.parse(localStorage.getItem(bookKey) || '[]'); }} catch(e) {{ book = []; }}
        if (!book.includes(token)) {{
          book.unshift(token);
          localStorage.setItem(bookKey, JSON.stringify(book));
        }}

        async function refreshCard() {{
          try {{
            const r = await fetch('/api/tower/cards/' + encodeURIComponent(token), {{cache:'no-store'}});
            const d = await r.json();
            if (!d.ok) return;
            document.getElementById('liveCode').textContent = d.live_code;
            const hidden = document.getElementById('liveCodeInput');
            if (hidden) hidden.value = d.live_code;
            const badge = document.getElementById('statusBadge');
            badge.textContent = d.status_text;
            badge.className = 'status ' + d.status;
            if (d.status !== 'active') location.reload();
          }} catch(e) {{}}
        }}
        setInterval(refreshCard, 5000);

        document.getElementById('shareBtn').addEventListener('click', async () => {{
          const shareData = {{title: {title_json}, text: {share_json}, url: location.href}};
          try {{
            if (navigator.share) await navigator.share(shareData);
            else {{ await navigator.clipboard.writeText(location.href); alert('คัดลอกลิงก์แล้ว'); }}
          }} catch(e) {{}}
        }});
      </script>
    """
    return _card_shell(card_name, body)


@app.post("/tower/card/{token}/redeem", response_class=_CardHTMLResponse)
def tower_card_redeem(token: str, live_code: str = _CardForm(...)):
    return _card_shell(
        "ใช้กับร้านค้า",
        '<div class="panel"><h1>นำการ์ดไปใช้กับร้านค้าที่ผ่านระบบ</h1><p>ผู้ถือการ์ดไม่ต้องปิดการ์ดเอง ร้านค้าจะส่งรหัสเข้าระบบ Basic Reward</p><a class="btn" href="/tower/basic">เปิด Basic Reward</a></div>'
    )
    data = _card_load_state()
    card = _card_find_by_token(data, token)
    if not card:
        return _card_shell("แลกไม่สำเร็จ", '<div class="panel resultBad"><h1>ไม่พบการ์ด</h1></div>')
    if card.get("status") != "active":
        body = f'<div class="panel resultBad"><h1>การ์ด {_card_safe(card["serial"])} ถูกใช้แล้ว</h1><a class="btn" href="/tower/card/{_card_safe(token)}">ดูสถานะ</a></div>'
        return _card_shell("ใช้แล้ว", body)
    if not _card_verify_live_code(token, live_code):
        body = f'<div class="panel resultBad"><h1>รหัสสดไม่ตรง</h1><p>เปิดการ์ดจากระบบใหม่ ภาพหรือวิดีโอที่บันทึกไว้ใช้แลกไม่ได้</p><a class="btn" href="/tower/card/{_card_safe(token)}">เปิดใหม่</a></div>'
        return _card_shell("รหัสหมดอายุ", body)

    value = int(card.get("value_inf", 0))
    wallet = data["wallet"]
    if int(wallet.get("reserved_inf", 0)) < value:
        return _card_shell("ยอดสำรองผิดพลาด", '<div class="panel resultBad"><h1>INF สำรองไม่ครบ</h1><p>ระบบจึงยังไม่ปิดการ์ด</p></div>')

    card["status"] = "redeemed"
    card["redeemed_at"] = _card_now_iso()
    wallet["reserved_inf"] -= value
    wallet["redeemed_inf"] += value
    _card_save_state(data)

    body = f"""
      <div class="panel resultOk" style="text-align:center;padding:34px 20px">
        <h1>แลกสำเร็จ</h1>
        <p>การ์ด <b>{_card_safe(card['serial'])}</b></p>
        <h2 style="color:#78ffd0">{value:,} INF</h2>
        <p>ระบบหักยอดสำรองและปิดสำเนานี้แล้ว จึงใช้ซ้ำไม่ได้</p>
        <a class="btn" href="/tower/card/{_card_safe(token)}">ดูการ์ดที่ใช้แล้ว</a>
        <a class="btn alt" href="/tower/card-book">กลับสมุดการ์ด</a>
      </div>
    """
    return _card_shell("แลกสำเร็จ", body)


@app.get("/tower/card-book", response_class=_CardHTMLResponse)
def tower_card_book():
    body = """
      <div class="ctop"><a href="/tower/cards">← CARD SYSTEM</a><b>สมุดการ์ดที่ได้รับ</b></div>
      <div class="panel bookHero">
        <video src="/tower-card-assets/card_book.mp4" muted autoplay loop playsinline></video>
        <div class="bookText"><h1>MY RECEIVED CARD BOOK</h1><p>เปิดลิงก์การ์ดบนเครื่องนี้แล้ว สำเนาจะถูกเก็บเข้าหน้านี้อัตโนมัติ</p></div>
      </div>
      <div id="bookGrid" class="grid"><div class="panel"><p>กำลังเปิดสมุด...</p></div></div>
      <script>
        const key = 'infini_received_card_tokens_v1';
        let tokens = [];
        try { tokens = JSON.parse(localStorage.getItem(key) || '[]'); } catch(e) { tokens = []; }
        const grid = document.getElementById('bookGrid');
        function esc(s) { const d=document.createElement('div'); d.textContent=String(s||''); return d.innerHTML; }

        async function loadBook() {
          if (!tokens.length) {
            grid.innerHTML = '<div class="panel"><h2>สมุดยังว่าง</h2><p>เมื่อได้รับลิงก์สำเนาการ์ด ให้เปิดหนึ่งครั้ง การ์ดจะเข้ามาที่นี่</p><a class="btn" href="/tower/cards/issue">เลือกการ์ดทดลอง</a></div>';
            return;
          }
          const cards = [];
          const validTokens = [];
          for (const token of tokens) {
            try {
              const r = await fetch('/api/tower/cards/' + encodeURIComponent(token), {cache:'no-store'});
              if (!r.ok) continue;
              const d = await r.json();
              if (!d.ok) continue;
              validTokens.push(token);
              const media = d.media_type === 'video'
                ? `<video src="${esc(d.media_url)}" muted autoplay loop playsinline></video>`
                : `<img src="${esc(d.media_url)}" alt="การ์ด">`;
              cards.push(`<a class="panel choice" href="/tower/card/${encodeURIComponent(token)}">
                <div class="cardVisual">${media}<div class="shade"></div><div class="cardInfo"><div class="serial">${esc(d.serial)}</div><div class="cardName">${esc(d.card_name)}</div><div>${Number(d.value_inf).toLocaleString()} INF</div><span class="status ${esc(d.status)}">${esc(d.status_text)}</span></div></div>
              </a>`);
            } catch(e) {}
          }
          localStorage.setItem(key, JSON.stringify(validTokens));
          grid.innerHTML = cards.join('') || '<div class="panel"><h2>ไม่พบการ์ดที่ยังอยู่ในระบบ</h2></div>';
        }
        loadBook();
      </script>
    """
    return _card_shell("สมุดการ์ด", body)


@app.get("/tower/card-check", response_class=_CardHTMLResponse)
def tower_card_check(code: str = ""):
    data = _card_load_state()
    raw = (code or "").strip()
    if not raw:
        body = """
          <div class="ctop"><a href="/tower/cards">← CARD SYSTEM</a><b>ตรวจการ์ด</b></div>
          <div class="panel">
            <h1>ตรวจจากระบบ</h1>
            <form method="get" action="/tower/card-check">
              <label>รหัสการ์ด หรือ URL</label>
              <input name="code" placeholder="INF-... หรือ /tower/card/..." required>
              <button class="btn" type="submit">ตรวจสถานะ</button>
            </form>
          </div>
        """
        return _card_shell("ตรวจการ์ด", body)

    token = raw
    if "/tower/card/" in raw:
        token = raw.split("/tower/card/", 1)[1].split("?", 1)[0].split("#", 1)[0].strip("/")
    card = _card_find_by_token(data, token) or _card_find_by_serial(data, raw)
    if not card:
        return _card_shell("ไม่พบการ์ด", '<div class="panel resultBad"><h1>ไม่พบในระบบ</h1><p>ภาพ วิดีโอ หรือรหัสนี้ไม่ใช่หลักฐานว่าการ์ดเป็นของจริง</p><a class="btn" href="/tower/card-check">ตรวจอีกครั้ง</a></div>')

    status = card["status"]
    result_class = "resultOk" if status == "active" else "resultBad"
    body = f"""
      <div class="ctop"><a href="/tower/card-check">← ตรวจใบอื่น</a><b>ผลตรวจ</b></div>
      <div class="panel {result_class}">
        <span class="status {status}">{_card_status_text(status)}</span>
        <h1>{_card_safe(card['serial'])}</h1>
        <p>{_card_safe(card['card_name'])} · {card['value_inf']:,} INF</p>
        <p>แคมเปญ: {_card_safe(card['campaign_name'])}</p>
        <a class="btn" href="/tower/card/{_card_safe(card['token'])}">เปิดการ์ดจากระบบ</a>
      </div>
    """
    return _card_shell("ผลตรวจการ์ด", body)

# === END INFINI CARD COPY SYSTEM ===




# === INFINI BASIC MERCHANT MVP ===
from basic_merchant_system import setup_basic_merchant_system
setup_basic_merchant_system(app)
# === END INFINI BASIC MERCHANT MVP ===
