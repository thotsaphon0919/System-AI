from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil
import sys

p = Path("main.py")
if not p.exists():
    raise SystemExit("ไม่พบ main.py — ให้รันจากโฟลเดอร์ infini_point_tower")

s = p.read_text(encoding="utf-8")
start_marker = '@app.get("/tower")'
end_marker = '# หน้า 2'
start = s.find(start_marker)
end = s.find(end_marker, start)

if start < 0 or end < 0:
    raise SystemExit("ไม่พบขอบเขตหน้า /tower")

new_block = r'''@app.get("/tower")
def tower():
    return page("INFINI POINT TOWER", f"""
    <style>
      .wrap > header{{display:none}}
      body{{background:#03040a!important}}
      .wrap{{max-width:760px!important;padding:14px 14px 110px!important}}
      .p8046,.p8046 *{{box-sizing:border-box}}
      .p8046{{color:#fff}}
      .p8046-top{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:2px 2px 14px}}
      .p8046-brand small{{display:block;color:#8f8ca0;font-size:10px;letter-spacing:1.7px}}
      .p8046-brand strong{{display:block;margin-top:3px;font-size:20px;letter-spacing:1.2px}}
      .p8046-brand b{{color:#b34dff;font-size:28px;vertical-align:-2px}}
      .p8046-point{{padding:10px 13px;border:1px solid rgba(83,216,255,.28);border-radius:16px;background:#0a0d1a;color:#66ddff;text-align:right}}
      .p8046-point small{{display:block;color:#8f8ca0;font-size:9px;font-weight:800;letter-spacing:1px}}
      .p8046-point strong{{font-size:18px}}
      .p8046-search{{display:flex;align-items:center;gap:10px;height:50px;padding:0 15px;border:1px solid rgba(155,72,255,.25);border-radius:17px;background:#0a0b14}}
      .p8046-search span{{color:#68e3ff;font-size:20px}}
      .p8046-search input{{width:100%;border:0;outline:0;background:transparent;color:#fff;font:inherit}}
      .p8046-search input::placeholder{{color:#716e80}}
      .p8046-hero{{position:relative;overflow:hidden;min-height:246px;margin-top:14px;border:1px solid rgba(157,75,255,.52);border-radius:25px;background:linear-gradient(145deg,#15102c,#080912 70%);box-shadow:0 18px 44px rgba(0,0,0,.42)}}
      .p8046-hero img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.72}}
      .p8046-hero::after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(4,5,13,.93) 0%,rgba(4,5,13,.55) 55%,rgba(4,5,13,.18)),linear-gradient(0deg,rgba(6,3,18,.9),transparent 58%)}}
      .p8046-hero-copy{{position:relative;z-index:2;max-width:66%;padding:25px 21px}}
      .p8046-hero-copy small{{color:#78e6ff;font-size:10px;font-weight:900;letter-spacing:1.5px}}
      .p8046-hero-copy h1{{margin:10px 0 9px;font-size:clamp(31px,9vw,47px);line-height:.96;letter-spacing:-1.8px}}
      .p8046-hero-copy p{{margin:0;color:#c2bfd0;font-size:13px;line-height:1.55}}
      .p8046-hero-copy a{{display:inline-flex;margin-top:18px;padding:11px 16px;border:1px solid rgba(202,103,255,.55);border-radius:14px;background:linear-gradient(135deg,#7c2dff,#b946ff);color:#fff;text-decoration:none;font-weight:900}}
      .p8046-upload{{margin-top:14px;padding:14px;border:1px solid rgba(156,75,255,.25);border-radius:21px;background:#090a14}}
      .p8046-upload-title{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}}
      .p8046-upload-title strong{{font-size:15px}}
      .p8046-upload-title span{{color:#8c8998;font-size:11px}}
      .p8046-upload form{{display:flex;gap:9px}}
      .p8046-upload input{{min-width:0;flex:1;padding:11px;border:1px solid rgba(160,85,255,.24);border-radius:13px;background:#050610;color:#aaa;font-size:11px}}
      .p8046-upload button{{flex:0 0 auto;padding:0 15px;border:0;border-radius:13px;background:linear-gradient(135deg,#7d2eff,#bd48ff);color:#fff;font-weight:900}}
      .p8046-section-head{{display:flex;align-items:end;justify-content:space-between;gap:12px;margin:22px 2px 12px}}
      .p8046-section-head h2{{margin:0;font-size:17px}}
      .p8046-section-head span{{color:#8c8998;font-size:11px}}
      .p8046-quick{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}}
      .p8046-quick a{{min-width:0;padding:13px 6px;border:1px solid rgba(151,75,255,.28);border-radius:17px;background:linear-gradient(160deg,#111127,#080914);color:#fff;text-align:center;text-decoration:none}}
      .p8046-quick b{{display:flex;width:38px;height:38px;margin:0 auto 8px;align-items:center;justify-content:center;border-radius:13px;background:rgba(137,53,255,.18);color:#c879ff;font-size:19px}}
      .p8046-quick span{{display:block;overflow:hidden;text-overflow:ellipsis;font-size:10px;font-weight:800;white-space:nowrap}}
      .p8046-stats{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
      .p8046-stat{{padding:14px;border:1px solid rgba(151,75,255,.25);border-radius:18px;background:#0a0b15}}
      .p8046-stat small{{display:block;color:#8f8c9d;font-size:9px;letter-spacing:1px}}
      .p8046-stat strong{{display:block;margin-top:5px;font-size:18px}}
      .p8046-stat span{{display:block;margin-top:3px;color:#6fddff;font-size:10px}}
      .p8046-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}}
      .p8046-card{{position:relative;min-height:184px;display:flex;flex-direction:column;overflow:hidden;padding:14px;border:1px solid rgba(151,75,255,.32);border-radius:21px;background:radial-gradient(circle at 80% 16%,rgba(171,62,255,.27),transparent 26%),linear-gradient(155deg,#15122c,#080914 74%);color:#fff;text-decoration:none}}
      .p8046-card em{{display:flex;width:48px;height:48px;align-items:center;justify-content:center;border:1px solid rgba(184,99,255,.34);border-radius:15px;background:rgba(114,42,214,.14);color:#ca78ff;font-size:22px;font-style:normal}}
      .p8046-card h3{{margin:18px 0 7px;font-size:18px;line-height:1.1}}
      .p8046-card p{{margin:0;color:#9d9aaa;font-size:11px;line-height:1.45}}
      .p8046-card footer{{display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:15px;color:#70e2ff;font-size:11px;font-weight:900}}
      .p8046-card footer b{{display:flex;width:31px;height:31px;align-items:center;justify-content:center;border:1px solid rgba(88,222,255,.28);border-radius:50%;color:#fff}}
      .p8046-note{{margin-top:11px;padding:15px;border:1px solid rgba(67,234,170,.25);border-radius:18px;background:rgba(8,25,21,.72);color:#bdeeda;font-size:12px;line-height:1.55}}
      .p8046-nav{{position:sticky;bottom:8px;z-index:20;display:grid;grid-template-columns:repeat(5,1fr);gap:3px;margin-top:24px;padding:9px;border:1px solid rgba(148,75,255,.30);border-radius:23px;background:rgba(6,7,14,.94);backdrop-filter:blur(14px);box-shadow:0 16px 35px rgba(0,0,0,.45)}}
      .p8046-nav a{{padding:7px 2px;color:#777485;text-align:center;text-decoration:none;font-size:9px}}
      .p8046-nav b{{display:block;margin-bottom:3px;color:#a974ff;font-size:19px}}
      .p8046-nav .active{{color:#fff}}
      .p8046-nav .active b{{color:#fff;text-shadow:0 0 14px #b84cff}}
      @media(max-width:380px){{.p8046-hero-copy{{max-width:72%}}.p8046-quick{{gap:7px}}.p8046-quick span{{font-size:9px}}.p8046-card{{min-height:174px;padding:12px}}.p8046-card h3{{font-size:16px}}}}
    </style>

    <main class="p8046">
      <section class="p8046-top">
        <div class="p8046-brand">
          <small>INFINI ID HOME</small>
          <strong>POINT TOWER <b>∞</b></strong>
        </div>
        <div class="p8046-point">
          <small>MY POINT</small>
          <strong>{USER_POINTS:,} INF</strong>
        </div>
      </section>

      <label class="p8046-search">
        <span>⌕</span>
        <input id="p8046Search" type="search" placeholder="ค้นหาเมนู กิจกรรม หรือรางวัล">
      </label>

      <section class="p8046-hero">
        <img src="/tower/header-image" alt="INFINI POINT TOWER" onerror="this.style.display='none'">
        <div class="p8046-hero-copy">
          <small>INFINI ACTIVITY POINT</small>
          <h1>INFINI<br>POINT TOWER</h1>
          <p>สะสมแต้ม สร้างแคมเปญ ชมโฆษณา แลกรางวัล และใช้การ์ดสิทธิ์กับร้านค้าพาร์ทเนอร์</p>
          <a href="/tower/dashboard">เข้าหน้าหลักตึก →</a>
        </div>
      </section>

      <section class="p8046-upload">
        <div class="p8046-upload-title">
          <strong>อัปโหลดภาพช่องหัวข้อใหม่</strong>
          <span>รูปภาพของชุด 8046</span>
        </div>
        <form method="post" action="/tower/header-upload" enctype="multipart/form-data">
          <input type="file" name="file" accept="image/*" required>
          <button type="submit">อัปโหลด +</button>
        </form>
      </section>

      <div class="p8046-section-head"><h2>QUICK ACCESS</h2><span>เมนูเดิมของ 8046</span></div>
      <section class="p8046-quick">
        <a href="/tower/dashboard"><b>▣</b><span>หน้าหลักตึก</span></a>
        <a href="/tower/ad-market"><b>▶</b><span>ชมโฆษณา</span></a>
        <a href="/tower/rewards"><b>★</b><span>รางวัล</span></a>
        <a href="/tower/cards"><b>▤</b><span>การ์ด</span></a>
      </section>

      <div class="p8046-section-head"><h2>POINT TOWER STATUS</h2><span>ข้อมูลเดิม</span></div>
      <section class="p8046-stats">
        <div class="p8046-stat"><small>MY POINT</small><strong>12,450 INF</strong><span>พร้อมใช้ในระบบ</span></div>
        <div class="p8046-stat"><small>CAMPAIGN</small><strong>6 ACTIVE</strong><span>แคมเปญเปิดอยู่</span></div>
        <div class="p8046-stat"><small>REWARD CARD</small><strong>120+</strong><span>การ์ด/ของรางวัล</span></div>
        <div class="p8046-stat"><small>PARTNER</small><strong>28 SHOP</strong><span>ร้านค้าพาร์ทเนอร์</span></div>
      </section>

      <div class="p8046-section-head"><h2>MY CONTENT</h2><span>เลือกใช้งาน</span></div>
      <section class="p8046-grid" id="p8046Grid">
        <a class="p8046-card" data-search="enter tower dashboard wallet" href="/tower/dashboard"><em>∞</em><h3>ENTER TOWER</h3><p>ดูยอดแต้ม สถานะ Wallet Campaign และกิจกรรมในระบบ</p><footer><span>เข้าสู่ตึก</span><b>→</b></footer></a>
        <a class="p8046-card" data-search="how to earn ad market mission" href="/tower/ad-market"><em>▶</em><h3>HOW TO EARN</h3><p>เลือกชมโฆษณาและทำกิจกรรมเพื่อรับ INF</p><footer><span>เริ่มรับแต้ม</span><b>→</b></footer></a>
        <a class="p8046-card" data-search="redeem rewards partner shop" href="/tower/rewards"><em>★</em><h3>REDEEM REWARDS</h3><p>เลือกและแลกของรางวัลจากระบบและร้านค้าพาร์ทเนอร์</p><footer><span>ดูของรางวัล</span><b>→</b></footer></a>
        <a class="p8046-card" data-search="card system card book" href="/tower/cards"><em>▤</em><h3>CARD SYSTEM</h3><p>ออกสำเนา สมุดการ์ด ตรวจและแลกสิทธิ์</p><footer><span>เปิดระบบการ์ด</span><b>→</b></footer></a>
        <a class="p8046-card" data-search="history transaction" href="/tower/transaction?type=history"><em>◷</em><h3>ประวัติ</h3><p>ดูรายการย้อนหลังและความเคลื่อนไหวในระบบ</p><footer><span>ดูประวัติ</span><b>→</b></footer></a>
        <a class="p8046-card" data-search="my point wallet" href="/tower/transaction?type=wallet"><em>◆</em><h3>MY POINT</h3><p>ดูกระเป๋าแต้มและยอดคงเหลือของสมาชิก</p><footer><span>เปิดกระเป๋า</span><b>→</b></footer></a>
      </section>

      <section class="p8046-note"><strong>POINT ECONOMY SYSTEM</strong><br>ดูแคมเปญ รับ INF แปลงเป็นการ์ด เก็บไว้ในกระเป๋า และนำไปแลกของจริงตามเงื่อนไขของระบบ</section>

      <nav class="p8046-nav">
        <a class="active" href="/tower"><b>⌂</b>HOME</a>
        <a href="/tower/dashboard"><b>▣</b>TOWER</a>
        <a href="/tower/ad-market"><b>▶</b>EARN</a>
        <a href="/tower/rewards"><b>★</b>REWARD</a>
        <a href="/tower/cards"><b>▤</b>CARD</a>
      </nav>
    </main>

    <script>
      (() => {{
        const input = document.getElementById("p8046Search");
        const cards = Array.from(document.querySelectorAll(".p8046-card"));
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


'''

backup = p.with_name(f"main.py.before_8046_home_form_{datetime.now():%Y%m%d_%H%M%S}")
shutil.copy2(p, backup)

patched = s[:start] + new_block + s[end:]
p.write_text(patched, encoding="utf-8")

try:
    py_compile.compile(str(p), doraise=True)
except Exception as exc:
    shutil.copy2(backup, p)
    raise SystemExit(f"ตรวจโค้ดไม่ผ่าน จึงกู้ไฟล์เดิมแล้ว: {exc}")

print("8046_HOME_FORM_V1_OK")
print(f"backup: {backup.name}")
