# research-article

สกิลสำหรับ [Claude Code](https://claude.com/claude-code) ช่วยเขียนบทความวิจัยและบทความวิชาการภาษาไทยเพื่อส่งวารสารในฐาน TCI/ThaiJO ตั้งแต่เลือกหัวข้อจนได้ไฟล์ .docx ตามรูปแบบวารสาร

A Claude Code skill for writing Thai research and academic articles for TCI/ThaiJO journals, from topic selection to a journal-formatted .docx.

## ความสามารถ

- **เลือกหัวข้อ** สแกนจำนวนงานใน TCI แนวโน้ม และงานนานาชาติ เพื่อหาช่องว่างงานวิจัย
- **สัมภาษณ์ผู้เขียน** เก็บประเภทบทความ วารสารเป้าหมาย ข้อมูลวิจัย และข้อกำหนดของวารสาร
- **ค้นแหล่งอ้างอิงจริง** อย่างน้อย 10 แหล่ง จาก TCI, OpenAlex, Crossref, DOAJ, ERIC, Europe PMC, Semantic Scholar, CORE, arXiv พร้อมยืนยัน DOI และบันทึกระดับการอ่าน (ฉบับเต็ม / บทคัดย่อ / บรรณานุกรม)
- **2 โหมด** (1) วารสารสาย มจร ที่ต้องบูรณาการหลักพุทธธรรม (2) วารสารทั่วไป
- **ภาษาไทยเชิงวิชาการ** ร่างจากโน้ตภาษาไทย (ไม่แปลจากประโยคอังกฤษ) และเกลาสำนวนผ่านสกิล [thai-humanizer](https://github.com/owh-hwo/thai-humanizer) (ติดตั้งมาพร้อมกันเมื่อติดตั้งแบบ plugin) โดยไม่ให้ข้อเท็จจริง ตัวเลข หรือระดับความมั่นใจเปลี่ยน
- **จำลองผู้ทรงคุณวุฒิ** ให้ผู้ตรวจอิสระตรวจหลายรอบตามรายการบทเรียน (`references/review-lessons.md`) และทำตารางตอบผู้ทรงฯ
- **สร้าง .docx** ตามรูปแบบวารสาร (ฟอนต์ ขนาด ส่วนหัว เลขหน้า ตาราง ภาพ ตัดคำไทย) และตรวจการอ้างอิงในเนื้อหากับรายการท้ายเรื่อง

หลักที่สกิลไม่ละเมิด: อ้างอิงต้องมีจริงและตรวจได้, ไม่สร้างข้อมูลวิจัยขึ้นเอง, ข้อความในบทความต้องไม่แรงกว่าหลักฐานที่อ่าน

## ติดตั้ง

### วิธีที่ 1: ติดตั้งเป็น plugin ใน Claude Code (แนะนำ)

พิมพ์ใน Claude Code

```
/plugin marketplace add owh-hwo/research-article
/plugin install research-article@research-article
```

อัปเดตภายหลังด้วย `/plugin marketplace update research-article`

### วิธีที่ 2: คัดลอกเป็น personal skill

macOS / Linux

```bash
git clone https://github.com/owh-hwo/research-article.git
mkdir -p ~/.claude/skills
cp -r research-article/skills/research-article ~/.claude/skills/
```

Windows (PowerShell)

```powershell
git clone https://github.com/owh-hwo/research-article.git
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse research-article\skills\research-article "$HOME\.claude\skills\"
```

ถ้าต้องการใช้เฉพาะโปรเจกต์ ให้คัดลอกไปที่ `<โปรเจกต์>/.claude/skills/research-article/` แทน

### ติดตั้งไลบรารี Python

สคริปต์ใช้ Python 3.9+

```bash
pip install -r requirements.txt
```

- `python-docx` จำเป็นสำหรับสร้าง .docx
- `pythainlp` ใช้ตัดคำไทยในไฟล์ .docx และนับคำบทคัดย่อภาษาไทย
- `pypdfium2` ใช้เรนเดอร์หน้า PDF เป็นภาพเพื่อตรวจการจัดหน้า

ตัวเลือกเสริม (ตัวแปรสภาพแวดล้อม): `CONTACT_EMAIL` หรือ `OPENALEX_MAILTO` สำหรับ polite pool ของ OpenAlex/Crossref, `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `CORE_API_KEY`

## สกิลที่ต้องติดตั้งคู่กัน

[thai-humanizer](https://github.com/owh-hwo/thai-humanizer) ติดตั้งให้อัตโนมัติเมื่อติดตั้ง research-article แบบ plugin (ประกาศเป็น `dependencies` ไว้แล้ว) ถ้าคัดลอกสกิลไปไว้ที่ `~/.claude/skills/` เอง ต้องติดตั้ง thai-humanizer แยก:

```
/plugin marketplace add owh-hwo/thai-humanizer
/plugin install thai-humanizer@thai-humanizer
```

ใช้ในขั้นร่าง ขั้นปรับภาษา และขั้นตรวจก่อนส่ง (แม่แบบย่อหน้าภาษาไทย ตัวนับร่องรอยภาษา AI และ Humanizer ภาษาอังกฤษ)

## การใช้งาน

พิมพ์คำขอเป็นภาษาไทยได้เลย สกิลจะทำงานเมื่อพูดถึงการเขียนบทความหรือส่งวารสาร เช่น

- "ช่วยหาหัวข้อบทความวิชาการเรื่องภาษีกับ SME ที่ยังมีช่องว่างใน TCI"
- "เขียนบทความวิจัยส่งวารสารสาย มจร จากผลวิจัยนี้ อ้างหลักพรหมวิหาร 4"
- "ตรวจบทความนี้แบบผู้ทรงคุณวุฒิ แล้วทำตารางตอบ"

หรือเรียกตรงด้วย `/research-article` (ติดตั้งแบบ plugin จะเป็น `/research-article:research-article`)

แนะนำให้วางเอกสารของวารสารเป้าหมาย (คำแนะนำผู้เขียน แม่แบบ บทความตัวอย่าง) ไว้ในโฟลเดอร์งาน สกิลจะยึดแม่แบบของวารสารเป้าหมายเป็นกติกาหลัก

## โครงสร้าง

```
.claude-plugin/          plugin.json, marketplace.json
skills/research-article/
  SKILL.md               ขั้นตอนหลัก
  references/            คู่มืออ้างอิง APA, หลักธรรม, วารสาร, การค้น, สำนวนไทย, บทเรียนจากการตรวจ
  scripts/               tci_search, academic_search, topic_scan, check_citations, build_docx
```

## ข้อจำกัด

- การจำลองผู้ทรงคุณวุฒิไม่รับประกันผลการพิจารณาของวารสารจริง
- จำนวนหน้าที่ถูกต้องต้องใช้ฟอนต์ที่วารสารกำหนด (เช่น TH Sarabun New) ติดตั้งในเครื่อง
- ผู้เขียนยังต้องตรวจความคล้ายคลึง (CopyCat / อักขราวิสุทธิ์ / Turnitin) และเตรียมแบบฟอร์มของวารสารเอง

## License

MIT
