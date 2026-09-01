from pathlib import Path
from datetime import datetime
import shutil
import sys

p = Path("main.py")
if not p.exists():
    print("❌ ไม่พบ main.py กรุณา cd เข้า ~/downloads/infini_remote_pro_v1 ก่อน")
    sys.exit(1)

s = p.read_text(encoding="utf-8")
marker = "COMMUNITY THAI TEXT + CREATIVE NAV ALIGN FIX V1"
if marker in s:
    print("✅ ติดตั้งตัวแก้ภาษาไทยและเมนูครีเอทีฟแล้ว ไม่ต้องทำซ้ำ")
    sys.exit(0)

anchor = '\n</style>\n    </head>\n    <body class="zone-{zone_key}">' 
if anchor not in s:
    print("❌ ไม่พบตำแหน่ง CSS ของหน้า Zone หยุดเพื่อไม่ให้ไฟล์พัง")
    sys.exit(1)

old_label = '<span>Creative Room</span>'
if old_label not in s:
    print("❌ ไม่พบข้อความ Creative Room ในเมนูล่าง หยุดเพื่อไม่ให้แก้ผิดจุด")
    sys.exit(1)

css = r'''

/* COMMUNITY THAI TEXT + CREATIVE NAV ALIGN FIX V1 */
.zone-portfolio .hero{{
  aspect-ratio:auto!important;
  height:auto!important;
  min-height:clamp(350px,88vw,430px)!important;
  padding:24px 18px 88px!important;
  align-items:flex-start!important;
}}

.zone-portfolio .hero > div{{
  width:100%!important;
  max-width:100%!important;
}}

.zone-portfolio .hero h1{{
  margin:0 0 12px!important;
}}

.zone-portfolio .hero p{{
  width:100%!important;
  max-width:100%!important;
  margin:0!important;
  overflow:visible!important;
  font-family:system-ui,-apple-system,"Noto Sans Thai",Tahoma,sans-serif!important;
  font-size:clamp(15px,4.1vw,18px)!important;
  line-height:1.55!important;
  letter-spacing:0!important;
}}

.zone-portfolio .az-bottom-nav span{{
  min-height:14px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  text-align:center!important;
  line-height:1.05!important;
}}

.zone-portfolio .az-bottom-nav a[href="/creative-gate"] span{{
  white-space:nowrap!important;
}}

@media(max-width:540px){{
  .zone-portfolio .hero{{
    min-height:350px!important;
    padding:23px 18px 86px!important;
  }}

  .zone-portfolio .hero p{{
    font-size:15px!important;
    line-height:1.52!important;
  }}
}}
'''

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = p.with_name(f"main.py.safe_before_community_thai_fix_{stamp}")
shutil.copy2(p, backup)

# เปลี่ยนชื่อเมนูล่างให้เป็นภาษาไทยบรรทัดเดียว
s = s.replace(old_label, '<span>ครีเอทีฟ</span>', 1)
# เพิ่ม CSS เฉพาะหน้า Community
s = s.replace(anchor, css + anchor, 1)
p.write_text(s, encoding="utf-8")

print("✅ ขยายพื้นที่ข้อความภาษาไทยใน Community ไม่ให้ชนแถบสถิติแล้ว")
print("✅ เปลี่ยน Creative Room ในเมนูล่างเป็น ครีเอทีฟ และจัดให้อยู่แนวเดียวกันแล้ว")
print(f"✅ สำรองไฟล์เดิมไว้: {backup.name}")
