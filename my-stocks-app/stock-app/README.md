# หุ้นของฉัน: เว็บแอปติดตามพอร์ตส่วนตัว

เว็บแอปของคุณเอง เปิดได้จากมือถือโดยไม่ต้องล็อกอิน Claude ทำงานบน GitHub แบบฟรี และใช้ Claude ผ่าน API key ของคุณ

- **ราคาปิด และแนวรับแนวต้านรายสัปดาห์ (Pivot Point):** คำนวณจากข้อมูล Yahoo Finance ส่วนนี้ฟรี
- **ข่าว มุมมอง และสิ่งที่ควรทำของแต่ละตัว:** Claude ค้นเว็บแล้วเขียนเป็นภาษาไทย ใช้ API key ของคุณ
- **อัปเดตอัตโนมัติ:** ทุกวันจันทร์ถึงศุกร์ เวลาประมาณ 05:17 น. ตามเวลาไทย ซึ่งเป็นช่วงหลังตลาดสหรัฐฯ ปิด
- **ปุ่ม 🔄 อัปเดตตอนนี้:** กดสั่งอัปเดตเองได้ทุกเมื่อจากในเว็บ

## โครงสร้างไฟล์
```
config.json                    ← รายชื่อหุ้น แผน และโปรไฟล์ (แก้ไฟล์นี้เมื่อซื้อหรือขายหุ้น)
scripts/update.py              ← สคริปต์ดึงราคา คำนวณแนวรับแนวต้าน และเรียก Claude
.github/workflows/update.yml   ← ตารางเวลาอัปเดตอัตโนมัติ และงานที่ปุ่มสั่ง
docs/index.html                ← หน้าเว็บ
docs/data.json                 ← ข้อมูลล่าสุด (สคริปต์เขียนทับให้เอง)
```

## ติดตั้ง (ทำครั้งเดียว ใช้เวลาประมาณ 15 นาที)

### 1. สร้าง repo บน GitHub
1. สมัครหรือล็อกอิน https://github.com แล้วกด **New repository** ตั้งชื่อ เช่น `my-stocks` เลือก **Public** แล้วกด Create
   - ถ้าใช้บัญชีฟรี repo ต้องเป็น Public ถึงจะเปิดเป็นเว็บด้วย GitHub Pages ได้ ทุกคนที่รู้ลิงก์จะเห็นรายชื่อหุ้นและแผน แต่ไม่เห็นจำนวนเงิน ถ้าไม่อยากให้ใครเห็นแผน ให้ลบข้อความใน `"plan"` ของ `config.json` ออก
2. ในหน้า repo กด **Add file → Upload files** แล้วลากไฟล์ทั้งหมดในโฟลเดอร์นี้ไปวาง
   - ⚠️ โฟลเดอร์ `.github` เป็นโฟลเดอร์ซ่อน บน Mac กด `Cmd+Shift+.` เพื่อให้มองเห็น ถ้าอัปโหลดไม่ขึ้น ให้กด **Add file → Create new file** ตั้งชื่อ `.github/workflows/update.yml` แล้วคัดลอกเนื้อหาจากไฟล์นั้นไปวาง

### 2. ใส่ Claude API key
1. ไปที่ https://platform.claude.com สร้าง API key และเติมเครดิต แนะนำให้ตั้ง **spend limit** ไว้ด้วย เช่น $10 ต่อเดือน
2. ใน repo ไปที่ **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Secret: วาง key (ขึ้นต้นด้วย `sk-ant-`)

### 3. เปิดเว็บ (GitHub Pages)
**Settings → Pages → Source: Deploy from a branch → Branch: `main` / โฟลเดอร์ `/docs` → Save**
รอประมาณ 1–2 นาที จะได้ลิงก์ เช่น `https://<ชื่อคุณ>.github.io/my-stocks/`

### 4. ทำ token สำหรับปุ่มอัปเดต
1. https://github.com/settings/personal-access-tokens/new (Fine-grained token)
2. Repository access: **Only select repositories** แล้วเลือก `my-stocks`
3. Permissions → Repository permissions → **Actions: Read and write** (ถ้า repo เป็น Private ให้เพิ่ม **Contents: Read** ด้วย)
4. กด Generate แล้วคัดลอก token ไว้
5. เปิดเว็บบนมือถือ กด **⚙︎** ใส่ชื่อ repo (`ชื่อคุณ/my-stocks`) กับ token แล้วกดบันทึก
   - token จะเก็บไว้ในเบราว์เซอร์ของเครื่องนั้นเท่านั้น และใช้สั่งงานได้แค่ repo นี้

### 5. ใช้งานครั้งแรก
กด **🔄 อัปเดตตอนนี้** รอประมาณ 2–5 นาที ข้อมูลจะขึ้นเอง
ถ้าอยากให้เปิดเหมือนแอป บน iPhone ให้กด Share แล้วเลือก **Add to Home Screen**

## ใช้งานประจำ
- **ซื้อหรือขายหุ้น:** แก้ `config.json` บน GitHub (กดไอคอนดินสอ) เพิ่มหรือลบบรรทัดในส่วน `holdings` แล้ว Commit
- **เปลี่ยนแผน:** แก้ข้อความ `"plan"` ใน `config.json` ข้อความนี้จะถูกส่งให้ Claude ด้วย เพื่อให้คำแนะนำ "ควรทำ" สอดคล้องกับแผน
- **เปลี่ยนเวลาอัปเดตอัตโนมัติ:** แก้บรรทัด `cron` ใน `.github/workflows/update.yml` (เวลาเป็น UTC ซึ่งช้ากว่าเวลาไทย 7 ชั่วโมง)

## ค่าใช้จ่าย
- GitHub Actions และ Pages: ฟรีสำหรับ repo แบบ Public
- Claude API: คิดตามการใช้งานจริง ค่าค้นเว็บอยู่ที่ $10 ต่อ 1,000 ครั้ง ตั้งไว้สูงสุด 8 ครั้งต่อรอบ บวกค่า token ต่างหาก ค่าใช้จ่ายจริงต่อรอบดูได้ที่ platform.claude.com → Usage
  - ถ้าอยากประหยัด ให้ลด `max_searches` ใน `config.json` หรือเปลี่ยน `model` เป็น `claude-haiku-5-5`

## แก้ปัญหา
| อาการ | วิธีแก้ |
|---|---|
| ปุ่มขึ้นว่า token ใช้ไม่ได้ | สร้าง token ใหม่ตามขั้นที่ 4 แล้วใส่ใหม่ใน ⚙︎ |
| อัปเดตไม่สำเร็จ | ดูแท็บ **Actions** ใน repo กดรอบที่ล้มเหลวเพื่อดู error |
| push ไม่ได้ (permission denied) | Settings → Actions → General → Workflow permissions → **Read and write** |
| ไม่มีข่าวหรือมุมมอง มีแต่ราคา | ยังไม่ได้ใส่ `ANTHROPIC_API_KEY` หรือเครดิตหมด |

ข้อมูลในแอปใช้ประกอบการตัดสินใจเท่านั้น ไม่ใช่คำแนะนำการลงทุน
