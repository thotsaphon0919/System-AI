INFINI ID HUB PATCH

สิ่งที่เพิ่ม
- ช่อง "รวมไอดี" อยู่ถัดจาก Point ในหน้า INFINI ID
- หน้า /id-hub แสดงสมาชิก 2 ช่องต่อแถวบนมือถือ
- สมาชิกใหม่จาก data/users.json ของ 8032 ต่อท้ายอัตโนมัติ
- ค้นหาได้จากชื่อ Username และเลข INF-
- แตะสมาชิกแล้วเปิดหน้า Public ID ของคนนั้น
- Public ID ไม่แสดง Private / Office และไม่มีเครื่องมือแก้ไขของเจ้าของ

ไฟล์สำคัญ
- id_hub_7000.py
- install_id_hub_patch.py
- user_scope_7000.py (ใช้กู้คืนเฉพาะกรณีไฟล์เดิมหาย)

การติดตั้ง
1) cd ~/downloads/infini_remote_pro_v1
2) unzip ZIP ไปยังโฟลเดอร์ patch_id_hub
3) python patch_id_hub/install_id_hub_patch.py
4) ตรวจโค้ดและรัน 7000 ใหม่

ระบบ 8032 ไม่ต้องแก้ เพราะหน้า Hub อ่านทะเบียนสมาชิกจาก 8032 แบบสดทุกครั้งที่เปิดหน้า
