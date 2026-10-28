# research-article (สกิลสาธารณะ)

repo ของสกิล `research-article` (https://github.com/owh-hwo/research-article) เขียนบทความวิจัย/วิชาการภาษาไทยส่งวารสาร TCI ตั้งแต่เลือกหัวข้อจนได้ .docx และจำลองผู้ทรงคุณวุฒิด้วย subagent ทุกไฟล์ในนี้เผยแพร่สาธารณะ บทความจริงอยู่ที่ `../บทความ/` ไม่ใช่ที่นี่

## หลักออกแบบ (ตั้งแต่ v1.4)

บทความสองเรื่องแรกต้องตรวจ 7-10 รอบ จาก 194 ข้อที่แก้ ราวหนึ่งในสามคือข้อความแรงกว่าโน้ตแหล่ง รองลงมาคือศัพท์ไม่ตรงกันระหว่างส่วน ความยาวเกินแล้วตัดทีหลัง และงานบันทึก สกิลจึงยึดสามข้อ:

1. **ข้อบังคับอยู่ตอนเขียน ไม่ใช่รายการไล่ตรวจหลังเขียน**: `refs.json` ต้องมี `read`/`fulltext`/`key_point`/`cite_scope` ก่อนร่าง และประโยคที่อ้างแหล่งเขียนได้จากโน้ตเท่านั้น; งบความยาวเป็นอักขระอยู่ใน `outline.md` พร้อมย่อหน้าห้ามตัด; ตัวบทกฎหมายต้องอยู่ใน `fulltext/` ก่อนขั้น 6; สร้าง .docx นับหน้าทันทีหลังร่างแรก
2. **สคริปต์จับก่อนคน**: `check_claims` (หลักฐาน/กฎหมาย/บทคัดย่อสองภาษา/ความยาว), `check_terms` (ศัพท์ทุกส่วนรวมภาพ), `check_reflist` (รายการอ้างอิง), `check_response` (ตารางตอบ), `check_linebreaks` (PDF) บทเรียนใหม่ที่สคริปต์ตรวจได้ให้เพิ่มลงสคริปต์ ไม่เพิ่มข้อความใน `review-lessons.md`
3. **ผู้ทรงฯ 2 รอบ**: ด่านสคริปต์ → editor คนเดียว → รอบเต็ม 1 → รอบยืนยัน 1 ถ้ายังพบข้อบังคับใหม่ถือว่าต้นทางผิด กลับไปแก้ขั้น 3/5/6 ไม่วนรอบ 3+ (`peer-review.md` หัวข้อ "ด่านกรองก่อนเรียกผู้ทรงฯ")

## โครงสร้าง

| ส่วน | ไฟล์ | หมายเหตุ |
|---|---|---|
| ขั้นตอน | `skills/research-article/SKILL.md` | ขั้น 0-10 (โหมด → หัวข้อ → สัมภาษณ์ → เกณฑ์วารสาร → อ้างอิง → หลักธรรม → โครง+งบความยาว → ร่างจากโน้ต → ภาพ → ปรับภาษา → ตรวจ → 9.5 จำลองผู้ทรงฯ 2 รอบ → 10 .docx) |
| คู่มือ | `skills/research-article/references/` | `review-lessons.md` บทเรียนจากการตรวจ หมวด ก-ญ (+ "บทเรียนของบทเรียน" ท้ายบทนำ); `peer-review.md` ขั้น 9.5 ฉบับเต็ม: ด่านกรองและจำนวนรอบ บทบาท ไฟล์ร่วมของรอบ คำสั่งรอบ 1/N การเรียกขนานหลายบทความ ตารางตอบ cross-review เกณฑ์หยุด |
| ผู้ตรวจ | `agents/article-reviewer.md`, `agents/article-editor.md` | subagent ของ Claude Code (หนึ่งผู้ทรงฯ ต่อ subagent; editor = ด่านแรก/ตรวจ PDF/รวมผล/รวมผล cross-review) tools: Read, Grep, Glob, Bash (`python -I` อ่าน PDF), Write (เฉพาะรายงานของตน) reviewer เสนอสำนวนเฉพาะที่ความหมาย/ขอบเขตผิด พร้อมหลักฐานแหล่งและจุดตัดคู่ ปลั๊กอินค้นพบ `agents/` ที่รากอัตโนมัติ |
| สคริปต์ค้น | `tci_search.py`, `academic_search.py`, `topic_scan.py` | ผลค้นเขียนเป็น JSON ชื่อไฟล์บอกคำค้น (`tci_<คำ>_<คำ>.json`, `tci_abs_…` = ค้นบทคัดย่อ) เพราะ `make_refs_log.py` อนุมานคำค้นจากชื่อไฟล์ |
| สคริปต์สร้าง | `make_refs_log.py`, `make_reflist.py`, `build_docx.py` | refs-log จากไฟล์ผลค้น; รายการอ้างอิงจาก refs.json (`th-apa`/`en-apa`); .docx รวมตัวเลือกที่เคยเป็นสคริปต์แก้ไฟล์ต่อบทความ |
| สคริปต์ตรวจ | `check_citations.py`, `check_claims.py`, `check_terms.py`, `check_reflist.py`, `check_response.py`, `check_linebreaks.py` | ทุกตัวเป็นตัวชี้จุด (WARN/INFO, exit 0/1/2) ไม่ใช่คำตัดสิน ผลว่างไม่รับรองว่าถูก |
| ปลั๊กอิน | `.claude-plugin/plugin.json`, `marketplace.json` | version ปัจจุบัน **1.5.2**; `"dependencies": ["thai-humanizer"]`; marketplace มีสองปลั๊กอิน research-article (`./`) และ thai-humanizer (source `url` HTTPS) |

สคริปต์ใช้ Python 3.9+ กับ `python-docx`; `pythainlp` สำหรับตัดคำ/เรียงไทย; `pypdfium2` สำหรับอ่าน PDF

## พฤติกรรมสคริปต์ที่ต้องรักษา

**build_docx.py**
- `--thai-wordbreak` แทรก zero-width space **เฉพาะระหว่างโทเค็นที่ท้ายตัวหน้าและต้นตัวหลังเป็นอักษรไทยทั้งคู่** (ไม่ตัดใน URL คำละติน ตัวเลข ไม่ติดช่องว่าง/word joiner/NBSP และไม่ให้ "(" ค้างท้ายบรรทัด)
- `--keep-together`: แทนสตริงด้วยอักขระ private-use ก่อนตัดคำ แล้วคืนเป็น NBSP แทนช่องว่าง + word joiner หน้า "." เท่านั้น **ห้ามแทรก joiner ระหว่างทุกอักขระ** เพราะทำให้เครื่องหมายผสม (พินทุ สระบน/ล่าง) หลุดจากพยัญชนะ
- `--fit-tables`: แก้เฉพาะ `tblGrid`/`tcW` ไม่แตะรัน (รันที่มีภาพจะหายถ้าตั้ง `run.text`) ผลกริดต้องเท่า `fit_tables.py` รุ่นต่อบทความเดิม
- frontmatter `email_line:` พิมพ์บรรทัดอีเมลตามตัวอักษร (แทน `email:` ที่พิมพ์ "*Corresponding Author E-mail:") เพราะแม่แบบแต่ละวารสารเขียนบรรทัดนี้ต่างกัน
- ตัวเลือกส่วนหัว/ภาพ (`--author-size/--author-bold/--received/--figure-width-in/--source-align`) มีไว้แทนสคริปต์ postfix ต่อบทความ **ถ้าตัวเลือกไม่พอให้เพิ่มที่นี่** ไม่เขียนสคริปต์แก้ .docx ในโฟลเดอร์บทความ
- ย่อหน้าที่ขึ้นต้นด้วย "ตารางที่ N"/"Table N" ถือเป็นชื่อตาราง (ประโยคนำตารางในเนื้อหาจึงกลายเป็นป้ายซ้อน) ยังไม่ได้แก้ บันทึกใน `review-lessons.md` ฌ ถ้าแก้ ให้นับเป็นชื่อตารางเฉพาะบรรทัดที่ติดก่อนตาราง

**check_claims.py**
- ย่อหน้า = หนึ่งบรรทัดของ draft.md (เลข บ. ตรงกับที่ผู้ตรวจใช้) ตัวเลขผูกกับการอ้างที่ใกล้ที่สุดในบรรทัด แล้วเทียบกับ `key_point`/`cite_scope` ของแหล่งนั้น (บอกด้วยถ้าพบในโน้ตของแหล่งอื่นในบรรทัดเดียวกัน)
- ค่าประมาณความยาวสอบเทียบจากบทความจริงสองเรื่อง: 2,100 อักขระร้อยแก้ว/หน้า, แถวตาราง 0.06, ภาพ 0.4, อ้างอิง 9/หน้า × `--ref-lists` คลาดเคลื่อนราว ±0.5 หน้า นับจริงจาก .docx เสมอ
- กฎหมายดูจาก `type` (law/code/act/regulation/decree) หรือชื่อเรื่อง ต้องมีไฟล์ใน `fulltext` ที่เปิดได้จริง

**make_reflist.py**
- ผู้แต่งนิติบุคคลตัดสินด้วย `is_corporate` (มีคำบอกองค์กร/คำตัวพิมพ์ใหญ่ทั้งคำ/มากกว่า 3 คำ) ผิดให้ตั้ง `cite_en_override` ใน refs.json; ปิดหน่วยผู้แต่งด้วย "." เสมอ (APA 7 รวมผู้แต่งกลุ่ม)
- ลำดับไทยใช้ `pythainlp.util.collate` (พยัญชนะมาก่อนสระ เช่น พฤ ก่อน พิ) รายการไทยที่ผู้แต่งแรกเป็นอักษรละตินไว้ท้ายกลุ่มไทย
- บทความวารสารใส่ URL เฉพาะเมื่อ `url_in_ref: true` (ลิงก์ระเบียนฐานข้อมูลไม่ใช่ URL อ้างอิง) ไม่มีเล่ม/ฉบับ → "Advance online publication." วันที่เว็บ/ราชกิจจาฯ ตัดปีซ้ำออก
- ข้อมูลที่รายการต้องการอยู่ใน refs.json (`publisher_th/en`, `date_th/en`, `gazette_th/en`, `url2`, `title_italic`) ห้ามแก้ที่ไฟล์ผล และห้ามใส่ title_fix/ชื่อเฉพาะในสคริปต์

**make_refs_log.py** อนุมานคำค้นจากชื่อไฟล์และบอกให้ตรวจ นับระเบียน/ไม่ซ้ำจากไฟล์ (TCI ตาม id, นานาชาติตาม DOI หรือชื่อเรื่อง) ไม่เขียนทับ `refs-log.md` ที่มีอยู่ (เขียน `.generated.md` เว้นแต่ `--force`)

**check_terms.py** อ่านข้อความภาพจาก `figures/*.html` (ตัด style/script/comment) ไม่มี `terms.json` ก็ตรวจคำย่อและพิมพ์โครงไฟล์ให้

**check_reflist.py** รองรับรายการสองชุด (อังกฤษ + ไทยแยก) R6 ลำดับไทยใช้ collate เมื่อมี pythainlp; R9 เทียบชื่อเรื่องกับ refs.json (ไม่ใช่ผู้แต่ง-ปี ซึ่งเป็นงานของ `check_citations.py`)

**check_response.py** รหัสจากคอลัมน์แรกของตาราง (S1, E3, W12) และรหัส `บทบาท:ข้อ`; สถานะต้องอยู่ในชุดคำที่ `peer-review.md` กำหนด

**check_linebreaks.py** รายงานคำไทยที่ถูกตัดกลางคำ (เทียบขอบคำจากร่าง รวมกรณีท้ายคำเป็นคำอื่น เช่น "เส / นอก") และวงเล็บเปิดค้างท้ายบรรทัด พลาดคำที่ตัวตัดคำแยกเองทั้งในร่างและ PDF จึงต้องดูภาพหน้าเสมอ

**check_citations.py** จับคู่ "และคณะ" ในเนื้อหากับรายการท้ายเรื่องที่ลงชื่อผู้แต่งครบไม่ได้ (ERROR เท็จ) ยังไม่ได้แก้

## thai-humanizer (สกิลคู่หู แยก repo)

- repo https://github.com/owh-hwo/thai-humanizer โฟลเดอร์ `../thai-humanizer/` มีแม่แบบย่อหน้าไทย ร่องรอยภาษา AI/สำนวนแปล และ `thai_style_check.py`
- **อ้างอิงเท่านั้น ห้ามคัดลอกไฟล์มาไว้ที่นี่** ใน SKILL.md/agent เรียกโฟลเดอร์ว่า `<thai-humanizer-dir>`
- ติดตั้งอัตโนมัติผ่าน `dependencies` เมื่อติดตั้งแบบ plugin source ต้องเป็น `url` + HTTPS (ห้าม `"source": "github"` เครื่องที่มี SSH key จะล้มที่ host key verification) ยังไม่ล็อกเวอร์ชัน (ต้องมี tag `thai-humanizer--v<x.y.z>` ก่อน)
- บทเรียนสำนวนภาษา → repo นั้น; หลักฐาน อ้างอิง กฎหมาย รูปแบบวารสาร การตรวจ → `review-lessons.md`/`peer-review.md` ที่นี่

สกิลอื่น (`grill-me`, `diagram-design`, `docx`) ใช้ถ้ามี ไม่ต้องประกาศเป็น dependency

## กติกาเมื่อแก้

1. **ข้อมูลเฉพาะห้ามเข้า repo**: ชื่อบทความ หัวข้อ วารสารเป้าหมาย ชื่อผู้วิจัยในงานจริง เลขกฎหมาย path ส่วนตัว อีเมล ตัวอย่างต้องแต่งขึ้นหรือทำให้ทั่วไป (เคยหลุด: เลขกฎกระทรวง ชื่อผู้วิจัย ตัวอย่างภาษีเฉพาะเรื่อง) grep ก่อน commit ตามบล็อกด้านล่าง
2. บทเรียนจากบทความจริงเขียนเป็นข้อทั่วไปตามหมวด ไม่ใส่ประวัติการแก้ของบทความใด **ถ้าสคริปต์ตรวจบทเรียนนั้นได้ ให้เพิ่มลงสคริปต์ที่เกี่ยวข้องแทน (หรือควบคู่)** แล้วทดสอบกับ draft จริงทั้งสองเรื่องว่าไม่เกิดการเตือนเท็จจำนวนมาก
3. ตัวอย่าง `build_docx.py` ใน SKILL.md ต้องเป็นค่าทั่วไป ถ้าเป็นค่าของวารสารใดต้องบอกว่าเป็นตัวอย่าง
4. ขั้น 9.5 ใช้ **Claude subagent เป็นผู้ตรวจหลัก** (สกิลไม่สั่งให้เรียก CLI ภายนอก) ถ้าผู้ใช้มีรายงานจากผู้ตรวจระบบอื่นอยู่แล้ว ใช้เป็นข้อมูลเข้าของ cross-review ได้ แก้กติกาผู้ตรวจที่ agent และ `peer-review.md` ให้สอดคล้องกัน
5. เปลี่ยนพฤติกรรมแล้วเพิ่ม `version` ให้ตรงกันทั้ง `plugin.json` และรายการ research-article ใน `marketplace.json` (แก้เอกสารอย่างเดียวไม่ต้องเพิ่ม) อัปเดตตารางโครงสร้างและ "พฤติกรรมสคริปต์" ในไฟล์นี้ด้วย
6. แก้สคริปต์ที่สร้าง/ตรวจ .docx ให้ทดสอบกับบทความจริงใน `../บทความ/articles/` (Word COM นับหน้าเทียบก่อน-หลัง) เพราะการเปลี่ยนจุดตัดบรรทัดเปลี่ยนจำนวนหน้าได้หลายหน้า แก้ `make_reflist.py` ให้ diff ผลกับรายการที่ส่งจริงของบทความเดิม
7. สคริปต์ที่ต้องการต่อบทความ (จัดตาราง แก้ส่วนหัว สร้างรายการอ้างอิง) ให้มาเป็นตัวเลือกหรือสคริปต์ทั่วไปที่นี่ ไม่ปล่อยให้อยู่ใน `tools/` ของบทความแล้วเขียนใหม่เรื่องถัดไป
8. เขียน/แก้สคริปต์ด้วยเครื่องมือ Write/Edit ไม่ใช่ heredoc ผ่าน shell: backslash ในสตริง regex (`\b`, `\s`) เคยถูกแปลงเป็นอักขระควบคุมโดยไม่เห็นในผลลัพธ์

## ตรวจก่อน push

```bash
A=../บทความ/articles; S=skills/research-article/scripts
for s in $S/*.py; do python -I "$s" --help >/dev/null || echo "FAIL $s"; done
for d in $A/<ชื่อ1> $A/<ชื่อ2>; do (cd $d && python -I "$OLDPWD/$S/check_claims.py" draft.md refs.json && python -I "$OLDPWD/$S/check_reflist.py" draft.md refs.json && python -I "$OLDPWD/$S/check_terms.py" draft.md); done   # จำนวน WARN ต้องอธิบายได้ ไม่พุ่ง
python -I $S/check_linebreaks.py $A/<ชื่อ>/draft.md <pdf>                      # ลองกับ PDF จริง
python -I $S/make_reflist.py $A/<ชื่อ>/refs.json --style <th-apa|en-apa> --out <scratch>  # diff กับรายการที่ส่งจริง
python -I $S/make_refs_log.py $A/<ชื่อ> --out <scratch>.md                     # ยอดต้องเท่ากับ refs-log.md ที่นับมือ
# แก้ build_docx.py: สร้างทั้งสองบทความด้วยคำสั่งใน ../บทความ/CLAUDE.md ไป scratchpad แล้วนับหน้าด้วย Word COM เทียบไฟล์ส่ง
git add -A && git diff --cached -U0 | grep -E "^\+" | grep -nE "<คำเฉพาะของบทความที่เพิ่งทำ>|Google Drive|@gmail"   # ต้องไม่พบ
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

จากนั้น commit และ push ที่ `main` (ท้าย commit ใส่ `Co-Authored-By` ตามที่ระบบกำหนด) repo ใช้ `core.autocrlf` คำเตือน LF/CRLF ตอน add เป็นเรื่องปกติ

## การติดตั้งบนเครื่องนี้

- ติดตั้งแบบสำเนา: `cp -r skills/research-article ~/.claude/skills/` และ `cp agents/article-*.md ~/.claude/agents/` (แบบนี้ไม่ได้ dependency อัตโนมัติ thai-humanizer อยู่ที่ `~/.claude/skills/thai-humanizer/`) SKILL.md อ้าง agent ผ่าน `../../agents/` ซึ่งชี้ไป `~/.claude/agents/` พอดี
- เทียบสำเนากับ repo: `diff -rq --strip-trailing-cr -x __pycache__ skills/research-article ~/.claude/skills/research-article`
- agent ที่คัดลอกใหม่ใช้ได้เมื่อ session โหลดรายการ agent ใหม่ (เริ่ม session ใหม่ถ้ายังไม่เห็น)
- เครื่องนี้ติดตั้งแบบปลั๊กอินด้วย จึงมีสองชุดชื่อซ้ำ (`research-article` กับ `research-article:research-article`, agent `article-*` กับ `research-article:article-*`) หลัง push ต้องอัปเดตทั้งสองชุด: คัดลอกตามข้อแรก แล้ว `claude plugin marketplace update research-article` + `claude plugin update research-article@research-article` และ `/reload-plugins` ตรวจปลั๊กอินด้วย `diff -rq --strip-trailing-cr -x __pycache__ skills/research-article ~/.claude/plugins/cache/research-article/research-article/<version>/skills/research-article`
- เครื่องอื่นใช้ `/plugin marketplace update research-article` แล้ว `/reload-plugins`
- โฟลเดอร์นี้อยู่ใน Google Drive พร้อม `.git` แก้จากเครื่องเดียว เครื่องอื่น clone แยก

## งานที่ยังไม่ทำ

- `build_docx.py`: ชื่อตารางซ้อนจากประโยคนำ "ตารางที่ N"; `check_citations.py`: "และคณะ" กับรายการที่ลงชื่อครบ
- `check_terms.py` ยังไม่เทียบตัวเลข/ป้ายในภาพกับเนื้อหา (เช่น จำนวนระดับ ชื่อองค์ประกอบ) นอกจากคำที่อยู่ใน `terms.json`
- ยังไม่มีสคริปต์สร้าง `reviews/roundN/common.md` และภาพหน้า PDF (ตอนนี้ Claude หลักเตรียมเองตาม `peer-review.md`)
