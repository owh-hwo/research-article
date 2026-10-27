# research-article (สกิลสาธารณะ)

โฟลเดอร์นี้คือ repo ของสกิล `research-article` (https://github.com/owh-hwo/research-article) สำหรับเขียนบทความวิจัย/วิชาการภาษาไทยส่งวารสาร TCI ทุกอย่างในนี้เผยแพร่สาธารณะ งานเขียนบทความจริงอยู่ที่ `../บทความ/` ไม่ใช่ที่นี่

## โครงสร้าง

- `skills/research-article/SKILL.md`: ขั้นตอน 0-10 (เลือกโหมด → หัวข้อ → สัมภาษณ์ → เกณฑ์วารสาร → ค้นอ้างอิง → หลักธรรม → โครง → ร่าง → ภาพ → ปรับภาษา → ตรวจ → จำลองผู้ทรงฯ → .docx)
- `skills/research-article/references/`: คู่มือประกอบแต่ละขั้น (`review-lessons.md` คือรายการบทเรียนจากการตรวจ เพิ่มได้บ่อยที่สุด)
- `skills/research-article/scripts/`: `tci_search.py`, `academic_search.py`, `topic_scan.py`, `check_citations.py`, `build_docx.py` (Python 3.9+, `python-docx`; `pythainlp`, `pypdfium2` เสริม)
- `.claude-plugin/`: plugin.json + marketplace.json ติดตั้งด้วย `/plugin marketplace add owh-hwo/research-article`

## สกิลคู่หูที่แยกพัฒนา

- **`thai-humanizer`** (https://github.com/owh-hwo/thai-humanizer, โฟลเดอร์ `../thai-humanizer/`): แม่แบบย่อหน้าภาษาไทย ร่องรอยภาษา AI/สำนวนแปล และ `thai_style_check.py` สกิลนี้**อ้างอิงเท่านั้น** ห้ามคัดลอกไฟล์ของ thai-humanizer กลับมาไว้ที่นี่ ใน SKILL.md เรียกโฟลเดอร์ของมันว่า `<thai-humanizer-dir>` บทเรียนเรื่องสำนวนภาษาให้ไปเพิ่มที่ repo นั้น ส่วนบทเรียนเรื่องหลักฐาน การอ้างอิง กฎหมาย รูปแบบวารสาร เพิ่มที่นี่ (`review-lessons.md`)
- `grill-me`, `diagram-design`, `docx`: ใช้ถ้ามี ไม่บังคับ

## กติกาเมื่อแก้

1. **ข้อมูลเฉพาะห้ามเข้า repo**: ชื่อบทความ ชื่อวารสารเป้าหมาย ชื่อผู้วิจัยที่อ้างในงานจริง เลขกฎหมาย path ส่วนตัว อีเมล ตัวอย่างในไฟล์ต้องแต่งขึ้นหรือทำให้ทั่วไป ก่อนคอมมิตให้ grep หาคำเหล่านี้ (เคยหลุด: เลขกฎกระทรวง, ชื่อผู้วิจัย)
2. บทเรียนจากการตรวจบทความจริงให้เขียนเป็นข้อทั่วไปใน `review-lessons.md` ตามหมวด (ก-ญ) ไม่ใส่ประวัติการแก้ของบทความใด
3. คำสั่งตัวอย่าง `build_docx.py` ใน SKILL.md เป็นตัวอย่างทั่วไป อย่าใส่ค่าที่เป็นของวารสารใดวารสารหนึ่งโดยไม่บอกว่าเป็นตัวอย่าง
4. แก้สคริปต์แล้วรัน `--help` ทุกตัว และทดลอง `check_citations.py` กับ draft จริงใน `../บทความ/articles/*/` ก่อน push
5. รัน `claude plugin validate .` ให้ผ่าน
6. เพิ่ม version ใน `.claude-plugin/*.json` เมื่อเปลี่ยนพฤติกรรม แล้ว commit และ push ที่ `main`
7. เครื่องนี้ติดตั้งสกิลไว้ที่ `~/.claude/skills/research-article/` (สำเนา) **แก้ใน repo นี้แล้วคัดลอกทับ**: `cp -r skills/research-article ~/.claude/skills/` เครื่องอื่นใช้ `/plugin marketplace update research-article`
8. โฟลเดอร์นี้อยู่ใน Google Drive พร้อม `.git` ให้แก้จากเครื่องเดียว เครื่องอื่น clone แยก
