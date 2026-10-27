# research-article (สกิลสาธารณะ)

repo ของสกิล `research-article` (https://github.com/owh-hwo/research-article) เขียนบทความวิจัย/วิชาการภาษาไทยส่งวารสาร TCI ทุกไฟล์ในนี้เผยแพร่สาธารณะ บทความจริงอยู่ที่ `../บทความ/` ไม่ใช่ที่นี่

## โครงสร้าง

- `skills/research-article/SKILL.md`: ขั้น 0-10 (โหมด → หัวข้อ → สัมภาษณ์ → เกณฑ์วารสาร → อ้างอิง → หลักธรรม → โครง → ร่าง → ภาพ → ปรับภาษา → ตรวจ → จำลองผู้ทรงฯ → .docx)
- `skills/research-article/references/`: คู่มือแต่ละขั้น `review-lessons.md` (บทเรียนจากการตรวจ หมวด ก-ญ) แก้บ่อยที่สุด
- `skills/research-article/scripts/`: `tci_search.py`, `academic_search.py`, `topic_scan.py`, `check_citations.py`, `build_docx.py` (Python 3.9+, `python-docx`; `pythainlp`, `pypdfium2` เสริม)
- `.claude-plugin/plugin.json`: ประกาศ `"dependencies": ["thai-humanizer"]`
- `.claude-plugin/marketplace.json`: มีสองปลั๊กอิน คือ research-article (`./`) และ thai-humanizer (source แบบ `url` ชี้ `https://github.com/owh-hwo/thai-humanizer.git`)

## thai-humanizer (สกิลคู่หู แยก repo)

- repo https://github.com/owh-hwo/thai-humanizer โฟลเดอร์ `../thai-humanizer/` มีแม่แบบย่อหน้าไทย ร่องรอยภาษา AI/สำนวนแปล และ `thai_style_check.py`
- **อ้างอิงเท่านั้น ห้ามคัดลอกไฟล์มาไว้ที่นี่** ใน SKILL.md เรียกโฟลเดอร์ว่า `<thai-humanizer-dir>`
- ติดตั้งอัตโนมัติผ่าน `dependencies` เมื่อติดตั้ง research-article แบบ plugin (ไม่ต้อง add marketplace ที่สอง)
- source ต้องเป็น `url` + HTTPS ห้ามเปลี่ยนเป็น `"source": "github"` เพราะเครื่องที่มี SSH key จะ clone ผ่าน SSH แล้วล้มที่ host key verification
- ยังไม่ล็อกเวอร์ชัน ถ้าจะใส่ `version` range ต้องสร้าง tag `thai-humanizer--v<x.y.z>` ใน repo นั้นก่อน
- บทเรียนเรื่องสำนวนภาษาไปเพิ่มที่ repo นั้น บทเรียนเรื่องหลักฐาน อ้างอิง กฎหมาย รูปแบบวารสาร เพิ่มที่ `review-lessons.md` ที่นี่

สกิลอื่น (`grill-me`, `diagram-design`, `docx`) ใช้ถ้ามี ไม่บังคับ ไม่ต้องประกาศเป็น dependency

## กติกาเมื่อแก้

1. **ข้อมูลเฉพาะห้ามเข้า repo**: ชื่อบทความ วารสารเป้าหมาย ชื่อผู้วิจัยในงานจริง เลขกฎหมาย path ส่วนตัว อีเมล ตัวอย่างต้องแต่งขึ้นหรือทำให้ทั่วไป grep ก่อนคอมมิตทุกครั้ง (เคยหลุด: เลขกฎกระทรวง, ชื่อผู้วิจัย)
2. บทเรียนจากบทความจริงเขียนเป็นข้อทั่วไปตามหมวดใน `review-lessons.md` ไม่ใส่ประวัติการแก้ของบทความใด
3. ตัวอย่าง `build_docx.py` ใน SKILL.md ต้องเป็นค่าทั่วไป ถ้าเป็นค่าของวารสารใดต้องบอกว่าเป็นตัวอย่าง
4. เปลี่ยนพฤติกรรมแล้วเพิ่ม `version` ให้ตรงกันทั้งใน `plugin.json` และรายการ research-article ใน `marketplace.json`

## ตรวจก่อน push

```bash
for s in skills/research-article/scripts/*.py; do python "$s" --help >/dev/null || echo "FAIL $s"; done
python skills/research-article/scripts/check_citations.py ../บทความ/articles/<ชื่อ>/draft.md   # ลองกับ draft จริง
claude plugin validate .
```

`validate` ต้องได้ `Validation passed` warning เรื่อง CLAUDE.md ที่ root และไม่มีไอคอนเป็นเรื่องปกติ

ถ้าแก้ `.claude-plugin/*.json` ให้ทดสอบติดตั้งใน config ชั่วคราว (ไม่แตะการตั้งค่าจริง):

```bash
export CLAUDE_CONFIG_DIR=<scratchpad>/cfg
claude plugin marketplace add "$(pwd)"
claude plugin install research-article@research-article   # ต้องเห็น "+ 1 dependency: thai-humanizer"
rm -rf "$CLAUDE_CONFIG_DIR"
```

จากนั้น commit และ push ที่ `main`

## การติดตั้งบนเครื่องนี้

- สกิลติดตั้งแบบสำเนาที่ `~/.claude/skills/research-article/` แก้ใน repo แล้วคัดลอกทับ: `cp -r skills/research-article ~/.claude/skills/` (แบบนี้ไม่ได้ dependency อัตโนมัติ thai-humanizer อยู่ที่ `~/.claude/skills/thai-humanizer/`)
- เทียบสำเนากับ repo ด้วย `diff -rq --strip-trailing-cr -x __pycache__` (ไฟล์ต่างกันแค่ CRLF/LF)
- เครื่องอื่นใช้ `/plugin marketplace update research-article` แล้ว `/reload-plugins`
- โฟลเดอร์นี้อยู่ใน Google Drive พร้อม `.git` แก้จากเครื่องเดียว เครื่องอื่น clone แยก
