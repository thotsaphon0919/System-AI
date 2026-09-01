from pathlib import Path
from datetime import datetime
import shutil
import sys

p = Path("main.py")
if not p.exists():
    print("❌ ไม่พบ main.py กรุณา cd เข้า ~/downloads/infini_remote_pro_v1 ก่อน")
    sys.exit(1)

s = p.read_text(encoding="utf-8")
marker = "COMMUNITY HERO TITLE CLIP FIX V1"
if marker in s:
    print("✅ ติดตั้งตัวแก้หัว COMMUNITY แล้ว ไม่ต้องทำซ้ำ")
    sys.exit(0)

anchor = '\n</style>\n    </head>\n    <body class="zone-{zone_key}">'
if anchor not in s:
    print("❌ ไม่พบตำแหน่งหน้า Zone ใน main.py หยุดเพื่อไม่ให้ไฟล์พัง")
    sys.exit(1)

css = r'''

/* COMMUNITY HERO TITLE CLIP FIX V1 */
.zone-portfolio .hero{{
  align-items:flex-start!important;
  padding-top:clamp(24px,5vw,34px)!important;
  padding-bottom:88px!important;
}}

.zone-portfolio .hero > div{{
  max-width:90%!important;
}}

.zone-portfolio .hero h1{{
  margin:0 0 10px!important;
  font-size:clamp(32px,8.6vw,44px)!important;
  line-height:.92!important;
  letter-spacing:-1.2px!important;
}}

.zone-portfolio .hero p{{
  max-width:100%!important;
  margin:0!important;
  font-size:clamp(14px,3.8vw,18px)!important;
  line-height:1.38!important;
}}

@media(max-width:540px){{
  .zone-portfolio .hero{{
    padding:24px 18px 82px!important;
  }}

  .zone-portfolio .hero > div{{
    max-width:94%!important;
  }}
}}
'''

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = p.with_name(f"main.py.safe_before_community_title_fix_{stamp}")
shutil.copy2(p, backup)

s = s.replace(anchor, css + anchor, 1)
p.write_text(s, encoding="utf-8")

print(f"✅ แก้หัว COMMUNITY ZONE ไม่ให้ถูกตัดแล้ว")
print(f"✅ สำรองไฟล์เดิมไว้: {backup.name}")
