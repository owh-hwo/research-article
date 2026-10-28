# research-article (สกิลสาธารณะ)

repo ของสกิล `research-article` (https://github.com/owh-hwo/research-article) เขียนบทความวิจัย/วิชาการภาษาไทยส่งวารสาร TCI ตั้งแต่เลือกหัวข้อจนได้ .docx และจำลองผู้ทรงคุณวุฒิด้วย subagent ทุกไฟล์ในนี้เผยแพร่สาธารณะ บทความจริงอยู่ที่ `../บทความ/` ไม่ใช่ที่นี่

## โครงสร้าง

| ส่วน | ไฟล์ | หมายเหตุ |
|---|---|---|
| ขั้นตอน | `skills/research-article/SKILL.md` | ขั้น 0-10 (โหมด → หัวข้อ → สัมภาษณ์ → เกณฑ์วารสาร → อ้างอิง → หลักธรรม → โครง → ร่าง → ภาพ → ปรับภาษา → ตรวจ → 9.5 จำลองผู้ทรงฯ → 10 .docx) |
| คู่มือ | `skills/research-article/references/` | `review-lessons.md` บทเรียนจากการตรวจ หมวด ก-ญ (แก้บ่อยที่สุด); `peer-review.md` ขั้น 9.5 ฉบับเต็ม: บทบาท ไฟล์ร่วมของรอบ คำสั่งรอบ 1/N การเรียกขนานหลายบทความ ตารางตอบ เกณฑ์หยุด |
| ผู้ตรวจ | `agents/article-reviewer.md`, `agents/article-editor.md` | subagent ของ Claude Code (หนึ่งผู้ทรงฯ ต่อ subagent; editor = ด่านแรก/ตรวจ PDF/รวมผล) tools: Read, Grep, Glob, Bash (`python -I` อ่าน PDF), Write (เฉพาะรายงานของตน) ปลั๊กอินค้นพบ `agents/` ที่รากอัตโนมัติ |
| สคริปต์ | `skills/research-article/scripts/` | `tci_search.py`, `academic_search.py`, `topic_scan.py`, `check_citations.py`, `build_docx.py`, `check_linebreaks.py` (Python 3.9+, `python-docx`; `pythainlp` + `pypdfium2` สำหรับตัดคำ/ตรวจ PDF) |
| ปลั๊กอิน | `.claude-plugin/plugin.json`, `marketplace.json` | version ปัจจุบัน **1.3.1**; `"dependencies": ["thai-humanizer"]`; marketplace มีสองปลั๊กอิน research-article (`./`) และ thai-humanizer (source `url` HTTPS) |

พฤติกรรมสคริปต์ที่ต้องรักษา:
- `build_docx.py --thai-wordbreak` แทรก zero-width space ระหว่างคำไทย **ยกเว้นหลัง "(" และ "["** (ไม่ให้วงเล็บเปิดค้างท้ายบรรทัด)
- `check_linebreaks.py` รายงานคำไทยที่ถูกตัดกลางคำ (เทียบขอบคำจากร่าง รวมกรณีท้ายคำเป็นคำอื่น เช่น "เส / นอก") และวงเล็บเปิดค้างท้ายบรรทัด; exit 0/1/2
- `check_citations.py` จับคู่ "และคณะ" ในเนื้อหากับรายการท้ายเรื่องที่ลงชื่อผู้แต่งครบไม่ได้ (ERROR เท็จ) ยังไม่ได้แก้

## thai-humanizer (สกิลคู่หู แยก repo)

- repo https://github.com/owh-hwo/thai-humanizer โฟลเดอร์ `../thai-humanizer/` มีแม่แบบย่อหน้าไทย ร่องรอยภาษา AI/สำนวนแปล และ `thai_style_check.py`
- **อ้างอิงเท่านั้น ห้ามคัดลอกไฟล์มาไว้ที่นี่** ใน SKILL.md/agent เรียกโฟลเดอร์ว่า `<thai-humanizer-dir>`
- ติดตั้งอัตโนมัติผ่าน `dependencies` เมื่อติดตั้งแบบ plugin source ต้องเป็น `url` + HTTPS (ห้าม `"source": "github"` เครื่องที่มี SSH key จะล้มที่ host key verification) ยังไม่ล็อกเวอร์ชัน (ต้องมี tag `thai-humanizer--v<x.y.z>` ก่อน)
- บทเรียนสำนวนภาษา → repo นั้น; หลักฐาน อ้างอิง กฎหมาย รูปแบบวารสาร การตรวจ → `review-lessons.md`/`peer-review.md` ที่นี่

สกิลอื่น (`grill-me`, `diagram-design`, `docx`) ใช้ถ้ามี ไม่ต้องประกาศเป็น dependency

## กติกาเมื่อแก้

1. **ข้อมูลเฉพาะห้ามเข้า repo**: ชื่อบทความ หัวข้อ วารสารเป้าหมาย ชื่อผู้วิจัยในงานจริง เลขกฎหมาย path ส่วนตัว อีเมล ตัวอย่างต้องแต่งขึ้นหรือทำให้ทั่วไป (เคยหลุด: เลขกฎกระทรวง ชื่อผู้วิจัย ตัวอย่างภาษีเฉพาะเรื่อง)
2. บทเรียนจากบทความจริงเขียนเป็นข้อทั่วไปตามหมวด ไม่ใส่ประวัติการแก้ของบทความใด
3. ตัวอย่าง `build_docx.py` ใน SKILL.md ต้องเป็นค่าทั่วไป ถ้าเป็นค่าของวารสารใดต้องบอกว่าเป็นตัวอย่าง
4. ขั้น 9.5 ใช้ **Claude subagent เท่านั้น** (ไม่แนะนำ CLI ภายนอกเป็นผู้ตรวจ) แก้กติกาผู้ตรวจที่ agent และ `peer-review.md` ให้สอดคล้องกัน
5. เปลี่ยนพฤติกรรมแล้วเพิ่ม `version` ให้ตรงกันทั้ง `plugin.json` และรายการ research-article ใน `marketplace.json`
6. แก้สคริปต์ที่สร้าง/ตรวจ .docx ให้ทดสอบกับบทความจริงใน `../บทความ/articles/` (Word COM นับหน้าเทียบก่อน-หลัง) เพราะการเปลี่ยนจุดตัดบรรทัดเปลี่ยนจำนวนหน้าได้หลายหน้า

## ตรวจก่อน push

```bash
for s in skills/research-article/scripts/*.py; do python -I "$s" --help >/dev/null || echo "FAIL $s"; done
python -I skills/research-article/scripts/check_citations.py ../บทความ/articles/<ชื่อ>/draft.md        # ลองกับ draft จริง
python -I skills/research-article/scripts/check_linebreaks.py ../บทความ/articles/<ชื่อ>/draft.md <pdf>  # ลองกับ PDF จริง
git diff -U0 | grep -E "^\+" | grep -nE "<คำเฉพาะของบทความที่เพิ่งทำ>|Google Drive|@gmail"             # ต้องไม่พบ
claude plugin validate .
```

`validate` ต้องได้ `Validation passed` (warning เรื่อง CLAUDE.md ที่ root และไม่มีไอคอนเป็นเรื่องปกติ)

ถ้าแก้ `.claude-plugin/*.json` ให้ทดสอบติดตั้งใน config ชั่วคราว (ไม่แตะการตั้งค่าจริง):

```bash
export CLAUDE_CONFIG_DIR=<scratchpad>/cfg
claude plugin marketplace add "$(pwd)"
claude plugin install research-article@research-article   # ต้องเห็น "+ 1 dependency: thai-humanizer"
rm -rf "$CLAUDE_CONFIG_DIR"
```

จากนั้น commit และ push ที่ `main` (ท้าย commit ใส่ `Co-Authored-By` ตามที่ระบบกำหนด)

## การติดตั้งบนเครื่องนี้

- ติดตั้งแบบสำเนา: `cp -r skills/research-article ~/.claude/skills/` และ `cp agents/article-*.md ~/.claude/agents/` (แบบนี้ไม่ได้ dependency อัตโนมัติ thai-humanizer อยู่ที่ `~/.claude/skills/thai-humanizer/`) SKILL.md อ้าง agent ผ่าน `../../agents/` ซึ่งชี้ไป `~/.claude/agents/` พอดี
- เทียบสำเนากับ repo: `diff -rq --strip-trailing-cr -x __pycache__ skills/research-article ~/.claude/skills/research-article`
- agent ที่คัดลอกใหม่ใช้ได้เมื่อ session โหลดรายการ agent ใหม่ (เริ่ม session ใหม่ถ้ายังไม่เห็น)
- เครื่องอื่นใช้ `/plugin marketplace update research-article` แล้ว `/reload-plugins`
- โฟลเดอร์นี้อยู่ใน Google Drive พร้อม `.git` แก้จากเครื่องเดียว เครื่องอื่น clone แยก
