# แหล่งค้นเอกสารวิชาการสาธารณะ

แหล่งหลักคือ **TCI** (`tci_search.py`) ใช้ทุกครั้ง แหล่งอื่นเป็นตัวเลือกที่ผู้ใช้เลือกในขั้นสัมภาษณ์ (คำถาม C12a) และบันทึกไว้ใน `brief.md` ช่อง "แหล่งค้นเพิ่มเติม"

## แหล่งที่ค้นผ่านสคริปต์ `academic_search.py` (API สาธารณะ ไม่ต้องล็อกอิน)

| รหัส | ฐานข้อมูล | ครอบคลุม | จุดเด่น / ข้อควรระวัง |
|---|---|---|---|
| `openalex` | OpenAlex | ทุกสาขา งานวิชาการทั่วโลก | ฐานเปิดที่ใหญ่ที่สุด มีจำนวนการอ้างอิง ค้นภาษาอังกฤษดีที่สุด; ไม่มี key ใช้โควตาร่วมรายวัน |
| `crossref` | Crossref | ทุกสาขา (ทะเบียน DOI) | ข้อมูลบรรณานุกรมถูกต้องที่สุด ใช้ **ยืนยัน DOI** (`--doi`) ได้ |
| `semantic` | Semantic Scholar | ทุกสาขา | มีจำนวนอ้างอิงและบทคัดย่อ; ไม่มี key มักโดนจำกัด (HTTP 429) |
| `doaj` | DOAJ | วารสาร open access ที่ผ่าน peer review | ทุกรายการเป็นวารสารที่ผ่านการคัดกรอง ปลอดวารสารล่าเหยื่อมากกว่า |
| `europepmc` | Europe PMC (รวม PubMed) | สุขภาพ การแพทย์ จิตวิทยา พฤติกรรมศาสตร์ | เหมาะกับหัวข้อสุขภาวะ ผู้สูงอายุ สมาธิ/สติ; source=PPR คือ preprint |
| `eric` | ERIC | การศึกษา | มีธง peer-reviewed ชัดเจน เหมาะกับบทความด้านการบริหารการศึกษา |
| `arxiv` | arXiv | CS, AI, เศรษฐศาสตร์, สถิติ | **preprint ไม่ผ่าน peer review** ใช้เมื่อจำเป็น (เช่นเทคโนโลยีใหม่มาก) และระบุว่าเป็น preprint |
| `core` | CORE | งาน open access ฉบับเต็มจากคลังสถาบัน | ต้องมี `CORE_API_KEY` (ขอฟรี) |

ชุดแนะนำตามสาขา:
| สาขา | `--sources` |
|---|---|
| รัฐศาสตร์ รัฐประศาสนศาสตร์ การจัดการ (ค่าเริ่มต้น) | `openalex,crossref,doaj` |
| การศึกษา | `openalex,eric,doaj` |
| สุขภาพ ผู้สูงอายุ จิตวิทยา สมาธิ | `openalex,europepmc,doaj` |
| เทคโนโลยี AI ดิจิทัล | `openalex,crossref,arxiv` |
| ค้นกว้างที่สุด | `all` |

```bash
python -I <skill-dir>/scripts/academic_search.py "digital leadership Buddhist" --sources openalex,eric --size 8 --years 2021-2026 --abstract --json <workdir>/intl_raw.json
python -I <skill-dir>/scripts/academic_search.py --doi 10.xxxx/xxxxx     # ยืนยันรายการเดียว
```
ค้นเป็นภาษาอังกฤษ (ฐานต่างประเทศค้นภาษาไทยได้ผลน้อย) ใช้ศัพท์ทางวิชาการ เช่น พรหมวิหาร → "Brahmavihara" OR "four sublime states", ธรรมาภิบาล → "good governance"
ตั้ง `CONTACT_EMAIL` เพื่อใช้ API แบบสุภาพ (polite pool) ได้

## แหล่งที่ค้นผ่าน WebSearch / WebFetch (ไม่มี API ที่สคริปต์ใช้)

| แหล่ง | ใช้ทำอะไร | วิธีค้น |
|---|---|---|
| ThaiJO (tci-thaijo.org) | บทความวารสารไทยฉบับเต็ม | WebSearch `site:tci-thaijo.org <คำค้น>` |
| Google Scholar (scholar.google.com) | ค้นกว้าง ดูจำนวนอ้างอิง | WebSearch; ไม่มี API ทางการ ห้าม scrape จำนวนมาก |
| ThaiLIS / ฐานวิทยานิพนธ์ไทย (tdc.thailis.or.th) | วิทยานิพนธ์และงานวิจัยไทย | WebSearch `site:tdc.thailis.or.th <คำค้น>` |
| คลังปัญญาของมหาวิทยาลัย (เช่น คลังวิทยานิพนธ์ มจร, CUIR, TU Digital Collections) | วิทยานิพนธ์ รายงานวิจัย | WebSearch ชื่อคลัง + คำค้น |
| พระไตรปิฎกออนไลน์ (84000.org) | ยืนยันเลขพระไตรปิฎก | ดู `dhamma-guide.md` |
| PhilPapers (philpapers.org) | ปรัชญา จริยศาสตร์ พุทธปรัชญา | WebSearch `site:philpapers.org` |
| JSTOR / ScienceDirect / SpringerLink / Taylor & Francis | ดูข้อมูลบรรณานุกรมจากหน้าเว็บผู้พิมพ์ | เปิดหน้าบทความ ยืนยันด้วย Crossref `--doi` |

## หลักคัดกรองคุณภาพ (ใช้กับทุกแหล่ง)

- ต้องมีข้อมูลครบสำหรับอ้างอิง: ผู้แต่ง ปี ชื่อเรื่อง แหล่งตีพิมพ์ ปีที่/ฉบับที่/หน้า หรือ DOI ถ้าขาดและหาไม่ได้ ไม่ใช้
- ให้ความสำคัญกับงานที่ผ่าน peer review; preprint (arXiv, PsyArXiv, SSRN) ใช้ได้น้อยและบอกผู้ใช้
- ระวังวารสารล่าเหยื่อ: ชื่อวารสารไม่อยู่ใน TCI/DOAJ/Scopus/Web of Science, รับตีพิมพ์เร็วผิดปกติ, ไม่มีระบบ peer review ชัดเจน ถ้าสงสัย ให้แจ้งผู้ใช้แทนการใช้
- ยืนยันทุกรายการจากต่างประเทศด้วย DOI (`--doi`) หรือหน้าเว็บผู้พิมพ์ แล้วบันทึก `verified_via` ใน refs.json
- สัดส่วนที่เหมาะกับวารสารไทย: งานไทย (TCI) เป็นแกนอย่างน้อยครึ่งหนึ่ง เสริมด้วยงานต่างประเทศ 20-40% เพื่อแสดงความเป็นสากล (ปรับตามที่ผู้ใช้กำหนด)
- รายการต่างประเทศเขียนอ้างอิงตามรูปแบบใน `citation-style.md` (ภาษาอังกฤษ) โดยใช้ข้อมูลจาก Crossref เป็นหลัก
