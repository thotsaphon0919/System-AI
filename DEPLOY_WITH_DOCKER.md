# Deploy ด้วย Docker Image (ไม่ต้องพึ่ง Git LFS อีกต่อไป)

วิธีนี้ทำให้ Render **ดึง Docker image จาก registry แทนการ clone GitHub**
ดังนั้นต่อให้ Git LFS quota ของบัญชี GitHub เต็ม ก็ deploy โปรเจคนี้ได้ปกติ

---

## สิ่งที่ต้องมีก่อนเริ่ม

1. ติดตั้ง **Docker Desktop** สำหรับ Windows: https://www.docker.com/products/docker-desktop/
   (ติดตั้งเสร็จ เปิดโปรแกรมทิ้งไว้ ต้องเห็นไอคอน Docker วิ่งอยู่ที่ system tray)
2. สมัครบัญชี **Docker Hub** (ฟรี): https://hub.docker.com/signup
   จำ username ไว้ เดี๋ยวต้องใช้แทนที่ `YOUR_DOCKERHUB_USERNAME` ด้านล่าง

---

## ขั้นตอนที่ 1 — Build image บนเครื่องตัวเอง

เปิด PowerShell ไปที่โฟลเดอร์โปรเจค (โฟลเดอร์ที่มี `Dockerfile` อยู่) แล้วรัน:

```powershell
docker build -t YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest .
```

ครั้งแรกจะใช้เวลาสักพัก (โหลด Python base image + ติดตั้ง dependencies)
ถ้าจบแล้วไม่มี error สีแดง แปลว่าสำเร็จ

---

## ขั้นตอนที่ 2 — ทดสอบรันในเครื่องก่อน (แนะนำ ไม่บังคับ)

```powershell
docker run --rm -p 10000:10000 `
  -e PORT=10000 `
  -e NEON_DATABASE_URL="ค่าจริงของพี่" `
  -e CLOUDINARY_URL="ค่าจริงของพี่" `
  YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest
```

เปิดเบราว์เซอร์ไปที่ `http://localhost:10000` ถ้าเห็นหน้า login ของ INFINI แปลว่าใช้ได้
กด `Ctrl+C` เพื่อหยุด

---

## ขั้นตอนที่ 3 — Login เข้า Docker Hub แล้ว push

```powershell
docker login
docker push YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest
```

---

## ขั้นตอนที่ 4 — เปลี่ยน Render service ให้ใช้ Image แทน Git

มี 2 วิธี เลือกอันใดอันหนึ่ง:

### วิธี A — ผ่าน Dashboard (ง่ายกว่า)

1. เข้า Render Dashboard → เลือกเซอร์วิส `infini-system-ai`
2. ไปที่ **Settings**
3. หา **"Source"** หรือ **"Deploy"** section → เปลี่ยนจาก "Git repository" เป็น
   **"Existing image"** → ใส่ `YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest`
4. ตรวจ **Environment Variables** ว่า `NEON_DATABASE_URL` และ `CLOUDINARY_URL`
   ยังอยู่ครบ (ค่าพวกนี้ไม่หายไปไหนตอนสลับ source)
5. กด **Save** → Render จะดึง image ใหม่มา deploy ทันที (ไม่แตะ GitHub เลย)

> ถ้า Render รุ่นที่ใช้อยู่ไม่มีตัวเลือกสลับ source ในหน้า Settings
> (บาง service type ล็อกไว้ตอนสร้าง) ให้ใช้วิธี B แทน — สร้างเซอร์วิสใหม่จาก image
> แล้วค่อยย้าย environment variables ไปใส่ใหม่ จากนั้นลบเซอร์วิสเก่า

### วิธี B — ผ่าน Render CLI (สร้างเซอร์วิสใหม่จาก image)

```powershell
render services create `
  --name infini-system-ai `
  --image YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest `
  --env NEON_DATABASE_URL="ค่าจริงของพี่" `
  --env CLOUDINARY_URL="ค่าจริงของพี่"
```

จากนั้นตั้ง custom domain / ลบเซอร์วิสเก่าทีหลังเมื่อของใหม่ทำงานเรียบร้อยแล้ว

---

## ทุกครั้งที่แก้โค้ดใหม่ในอนาคต

ต้องทำ 3 คำสั่งนี้ซ้ำ (build → push → Render จะ auto-deploy image tag ล่าสุดถ้าตั้ง auto-deploy ไว้
หรือกด Manual Deploy ในหน้า Render ถ้าไม่ auto):

```powershell
docker build -t YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest .
docker push YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest
render deploys create <SERVICE_ID>
```

ไม่ต้อง `git push` อีกแล้วสำหรับ production deploy — จะ push ขึ้น GitHub เก็บโค้ดไว้ตามปกติก็ได้
(เพื่อ backup โค้ด) แต่ Render จะไม่ไปยุ่งกับมันอีก
