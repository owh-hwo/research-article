#!/usr/bin/env python3
"""Check that what the draft claims about each source stays inside what refs.json says was read.

Usage:
  python -I check_claims.py draft.md refs.json [--pages 16] [--ref-lists 2] [--chars-per-page 2100] [--refs-per-page 9]

Reads the Thai draft (frontmatter and reference list are ignored) and refs.json, locates every
in-text citation, and flags, per citation window:

  A  verb level vs. reading level: "พบว่า/ชี้ว่า/..." near a source whose `read` is abstract or
     bibliographic (write "บทคัดย่อของ … รายงานว่า" instead), or a cited source with no `read` at all
  B  numbers near a citation that do not appear in that source's `key_point`/`cite_scope`
  C  `cite_scope` restrictions not reflected in the sentence (perception vs. actual use,
     interpretation vs. tested result)
  D  law/regulation sources without a verbatim text file in fulltext/, and every "มาตรา N" mentioned
     so each can be checked against the text
  E  wording checks: "มีนัยสำคัญ" without "ทางสถิติ", R² without the variable it explains,
     "ไม่พบงาน" claims (must be tied to the search scope)
  F  Thai abstract vs. English Abstract: numbers and "untested/hypothesis" hedges must match
  G  rough length estimate against --pages (calibrated on two articles: ~2,100 Thai characters of prose per A4 page at 16 pt
     with one figure and two tables; ~9 reference entries per page)

The script is a flagger. Every WARN must be read against the draft and the source before acting;
a quiet run does not prove the claims are right. Exit 0 = no WARN, 1 = WARN found, 2 = error.
"""
import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

THAI = re.compile(r"[฀-๿]")
REF_HEAD = re.compile(r"^#\s*(เอกสารอ้างอิง|บรรณานุกรม|References?)\s*$", re.M)
YEAR = r"(\d{4}[a-zก-ฮ]?)"
WINDOW = 260

STRONG = re.compile(r"พบว่า|ชี้ว่า|ชี้ให้เห็นว่า|แสดงว่า|แสดงให้เห็นว่า|ยืนยันว่า|สรุปว่า|พิสูจน์|ผลการวิจัย|ผลการศึกษา|ผลการสำรวจ|found that|shows? that|demonstrat")
ABSTRACT_HEDGE = re.compile(r"บทคัดย่อ|abstract", re.I)
INTERP_HEDGE = re.compile(r"ตีความ|อนุมาน|ข้อสันนิษฐาน|สันนิษฐาน|เสนอว่า|อาจ|ยังไม่ได้ทดสอบ|ยังไม่ผ่านการทดสอบ|ความเห็น|อภิปราย")
PERCEPTION_SCOPE = re.compile(r"ความตั้งใจ|การรับรู้|รับรู้|ประเมินตนเอง|รายงานเอง|self-report|perceived|intention")
PERCEPTION_HEDGE = re.compile(r"ความตั้งใจ|ตั้งใจ|รับรู้|ประเมินตนเอง|รายงานเอง|ที่รายงาน|มองว่า|เห็นว่า|คาดว่า|ความเห็น")
ACTUAL_WORDS = re.compile(r"ใช้จริง|ผลลัพธ์จริง|ทำให้(?!เห็น)|ส่งผลให้|ลดได้จริง|เพิ่มขึ้นจริง|ประสิทธิภาพเพิ่มขึ้น|ประสิทธิภาพสูงขึ้น")
INTERP_SCOPE = re.compile(r"ตีความ|ไม่ได้ทดสอบ|ไม่มีข้อมูลเชิงประจักษ์|เชิงแนวคิด|ความเห็น|ข้อเสนอเชิง")
RESTRICT_SCOPE = re.compile(r"ห้ามอ้าง|อ้างเฉพาะ|อ้างได้เพียง|ใช้ได้เพียง|อ้างทิศทางเท่านั้น|เท่านั้น|อย่าอ้าง")
LAW_TYPES = {"law", "code", "act", "regulation", "decree", "royal_decree", "ministerial_regulation", "notification"}
LAW_TITLE = re.compile(r"พระราชบัญญัติ|พระราชกฤษฎีกา|กฎกระทรวง|ประกาศ|ประมวล|Act\b|Decree|Regulation|Code\b|Notification", re.I)
SECTION = re.compile(r"มาตรา\s*\d+(?:/\d+)?(?:\s*(?:ทวิ|ตรี|จตุ|เบญจ))?|ข้อ\s*\d+(?:\s*\(\d+\))?(?=\s*(?:แห่ง|ของ|กฎกระทรวง|ประกาศ))")
NUM = re.compile(r"(?<![\d.])(?:ร้อยละ\s*)?\d+(?:[.,]\d+)*(?:\s*%|\s*เท่า)?|(?<![\d.])\.\d+")
NUM_CONTEXT_SKIP = re.compile(
    r"(มาตรา|ฉบับที่|ระดับที่|ตารางที่|ภาพที่|ข้อ|ชุด|ขั้นที่|ลำดับที่|No\.|Table|Figure|พ\.ศ\.|ค\.ศ\.|B\.E\.|ปี|เล่ม|หน้า|p\.|pp\.|วันที่|เดือน|ค\.ศ|ตั้งแต่|ถึง|[/\-–])\s*$")
NUM_AFTER_SKIP = re.compile(r"^\s*(เรื่อง|รายการ|ระเบียน|คำค้น|ชุด|แหล่ง|ฐาน|ระดับ|ขั้น|หัวข้อ|ประเภท|กลุ่มคำ|[/\-–]\d)")
EN_NUM_WORDS = {"two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
                "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20", "thirty": "30", "fifty": "50", "hundred": "100"}


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def section(text, name):
    m = re.search(r"^#\s*" + name + r"\s*$(.*?)(?=^#\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def digits(s):
    return re.sub(r"[^\d]", "", s)


def load_refs(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        for k in ("refs", "references", "items"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list):
        raise SystemExit("refs.json must be a list (or an object with a list under refs/references/items)")
    return data


def name_forms(ref):
    """Strings that identify this entry in the text, each paired with the years it may carry."""
    forms = set()
    for key in ("key_th", "key_en", "cite_en", "key"):
        k = ref.get(key)
        if not k:
            continue
        name = k.rsplit(",", 1)[0].strip() if "," in k else k.strip()
        if THAI.search(name):
            forms.add(re.split(r"\s+และ|,", name)[0].strip())
        else:
            base = re.sub(r"\s*(et al\.?|&.*|and .*)$", "", name).strip().rstrip(",")
            if base:
                forms.add(base)
            words = base.split()
            if len(words) > 4:
                forms.add(" ".join(words[:4]))
            m = re.search(r"\[([^\]]+)\]", name)
            if m:
                forms.add(m.group(1))
    for key in ("authors_th", "authors_en", "authors"):
        a = ref.get(key)
        if isinstance(a, list) and a:
            a = a[0]
        if isinstance(a, str) and a.strip():
            if THAI.search(a):
                forms.add(a.strip())
            else:
                surname = a.split(",")[0].strip()
                if " " in surname and "," not in a:
                    surname = surname.split()[-1]
                if len(surname) > 2:
                    forms.add(surname)
    years = set()
    for key in ("year_be", "year_ce", "year"):
        y = ref.get(key)
        if y:
            years.add(str(y))
    for key in ("key_th", "key_en", "cite_en", "key"):
        k = ref.get(key) or ""
        m = re.search(r"(\d{4})[a-zก-ฮ]?\s*$", k)
        if m:
            years.add(m.group(1))
    return {f for f in forms if f}, years


def label(ref):
    return ref.get("key_th") or ref.get("key_en") or ref.get("cite_en") or ref.get("key") or ref.get("title_en") or ref.get("title_th") or "?"


def locate_citations(body, refs):
    """Return list of (ref_index, start, end) for every in-text citation that matches a ref."""
    hits = []
    forms = [name_forms(r) for r in refs]
    for i, (fs, years) in enumerate(forms):
        for form in fs:
            for m in re.finditer(re.escape(form), body):
                window = body[m.end(): m.end() + 140]
                ym = None
                for y in years:
                    ym = re.search(r"(?<!\d)" + re.escape(y) + r"(?!\d)", window)
                    if ym:
                        break
                if ym:
                    hits.append((i, m.start(), m.end() + ym.end()))
    # drop a hit that lies inside a longer hit of another ref (e.g. "Oliveira" inside "Oliveira & Martins")
    hits.sort(key=lambda h: (h[1], -(h[2] - h[1])))
    out = []
    for h in hits:
        if out and h[1] >= out[-1][1] and h[2] <= out[-1][2] and h[0] != out[-1][0]:
            continue
        if out and (h[0], h[1]) == (out[-1][0], out[-1][1]):
            continue
        out.append(h)
    return out


def paragraphs(body):
    """Yield (start, end, text) of prose paragraphs: one non-blank line each (drafts keep a paragraph on
    one line, and reviewers cite them by line number); tables, images, headings and captions skipped."""
    pos = 0
    for line in body.split("\n"):
        start, end = pos, pos + len(line)
        pos = end + 1
        t = line.strip()
        if not t or t.startswith("|") or t.startswith("![") or t.startswith("#") or re.match(r"^(ตารางที่|Table|ที่มา|หมายเหตุ)\s*[\d:]", t):
            continue
        yield start, end, line


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("draft")
    p.add_argument("refs")
    p.add_argument("--pages", type=int, help="page cap of the journal (whole file); enables the length estimate")
    p.add_argument("--chars-per-page", type=int, default=2100, help="Thai characters of prose per page at 16 pt with headings (default 2100)")
    p.add_argument("--refs-per-page", type=float, default=9, help="reference entries per page (default 9)")
    p.add_argument("--ref-lists", type=int, default=1, help="number of reference lists in the file (2 when a Thai list is appended for checking)")
    p.add_argument("--window", type=int, default=WINDOW, help="characters around a citation treated as its claim")
    a = p.parse_args()

    try:
        raw = open(a.draft, encoding="utf-8").read()
        refs = load_refs(a.refs)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR cannot read inputs: {e}")
        return 2
    text = strip_frontmatter(raw)
    m = REF_HEAD.search(text)
    body = text[: m.start()] if m else text
    base = os.path.dirname(os.path.abspath(a.draft))
    law_marked = re.sub(r"\[/?ตัวบท\]", "", body)
    has_verbatim = "[ตัวบท]" in body
    body_clean = law_marked
    lines_before = lambda pos: body_clean.count("\n", 0, pos) + 1  # noqa: E731

    warns = 0
    infos = 0

    def out(level, code, msg):
        nonlocal warns, infos
        if level == "WARN":
            warns += 1
        else:
            infos += 1
        print(f"{level} {code}: {msg}")

    cites = locate_citations(body_clean, refs)
    cited_idx = {c[0] for c in cites}
    paras = list(paragraphs(body_clean))

    def para_of(pos):
        for s, e, t in paras:
            if s <= pos <= e:
                return s, e, t
        return None

    # ---- A/B/C per citation ----
    seen_b = set()
    for ri, s, e in cites:
        ref = refs[ri]
        pr = para_of(s)
        if not pr:
            continue
        ps, pe, _ = pr
        ws, we = max(ps, s - a.window), min(pe, e + a.window)
        win = body_clean[ws:we]
        ln = lines_before(s)
        lab = label(ref)
        read = (ref.get("read") or "").lower()
        rtype = (ref.get("type") or "").lower()
        is_law = rtype in LAW_TYPES or bool(LAW_TITLE.search(ref.get("title_en") or ref.get("title_th") or ref.get("title") or ""))
        notes = " ".join(str(ref.get(k) or "") for k in ("key_point", "cite_scope", "use_for"))

        # A: reading level vs verb
        if not read and not is_law:
            out("WARN", "A3", f"บ.{ln} อ้าง {lab} แต่ refs.json ไม่มี `read` (fulltext/abstract/bibliographic)")
        elif read in ("abstract", "bibliographic") and STRONG.search(win) and not ABSTRACT_HEDGE.search(win):
            out("WARN", "A1", f"บ.{ln} อ้าง {lab} (read={read}) ด้วยคำระดับ \"พบว่า\" โดยไม่บอกว่ามาจากบทคัดย่อ → ใช้ \"บทคัดย่อของ … รายงานว่า\" หรืออ่านฉบับเต็ม")
        if read == "bibliographic":
            out("WARN", "A2", f"บ.{ln} อ้าง {lab} ที่อ่านเพียงบรรณานุกรม ห้ามบรรยายเนื้อหาของงานนี้")

        # B: numbers whose nearest citation is this one must exist in its key_point/cite_scope
        if not is_law:
            note_digits = digits(notes)
            para_cites = [c for c in cites if ps <= c[1] <= pe]
            para_notes = digits(" ".join(str(refs[c[0]].get(k) or "") for c in para_cites for k in ("key_point", "cite_scope", "use_for")))
            for nm in NUM.finditer(win):
                apos = ws + nm.start()
                nearest = min(para_cites, key=lambda c: min(abs(apos - c[1]), abs(apos - c[2])))
                if (nearest[0], nearest[1]) != (ri, s):
                    continue
                tok = nm.group(0)
                before = win[max(0, nm.start() - 14): nm.start()]
                after = win[nm.end(): nm.end() + 12]
                if NUM_CONTEXT_SKIP.search(before) or NUM_AFTER_SKIP.match(after):
                    continue
                d = digits(tok)
                if not d or len(d) == 4 and 1900 <= int(d) <= 2700:  # years
                    continue
                if len(d) < 2 and "%" not in tok and "ร้อยละ" not in tok and "." not in tok:
                    continue
                if d in note_digits:
                    continue
                key = (ri, d)
                if key in seen_b:
                    continue
                seen_b.add(key)
                where = "ของแหล่งนั้น" if d not in para_notes else "ของแหล่งนั้น (แต่พบใน key_point ของแหล่งอื่นในย่อหน้าเดียวกัน ตรวจว่าอ้างถูกแหล่ง)"
                out("WARN", "B1", f"บ.{ln} ตัวเลข \"{tok.strip()}\" ใกล้การอ้าง {lab} ไม่อยู่ใน key_point/cite_scope {where} (เทียบกับฉบับเต็ม หรือเติมลง key_point)")

        # C: cite_scope restrictions
        scope = str(ref.get("cite_scope") or "")
        if PERCEPTION_SCOPE.search(scope) and ACTUAL_WORDS.search(win) and not PERCEPTION_HEDGE.search(win):
            out("WARN", "C1", f"บ.{ln} อ้าง {lab} ซึ่ง cite_scope บอกว่าวัดความตั้งใจ/การรับรู้ แต่ประโยคเขียนเป็นผลจริง (\"{ACTUAL_WORDS.search(win).group(0)}\")")
        if INTERP_SCOPE.search(scope) and STRONG.search(win) and not INTERP_HEDGE.search(win):
            out("WARN", "C2", f"บ.{ln} อ้าง {lab} ซึ่ง cite_scope บอกว่าเป็นการตีความ/ไม่ได้ทดสอบ แต่ประโยคใช้คำระดับผลวิจัยโดยไม่มีคำบอกระดับ")

    # C3: list restrictions for manual check
    restricted = [(label(r), r.get("cite_scope"), sum(1 for c in cites if c[0] == i)) for i, r in enumerate(refs) if RESTRICT_SCOPE.search(str(r.get("cite_scope") or ""))]
    if restricted:
        print("INFO C3: แหล่งที่ cite_scope จำกัดการอ้าง (ตรวจทุกจุดที่อ้างด้วยตา):")
        for lab, sc, n in restricted:
            print(f"      - {lab} [อ้าง {n} จุด]: {sc}")
        infos += 1

    # D: laws
    for i, r in enumerate(refs):
        rtype = (r.get("type") or "").lower()
        title = r.get("title_en") or r.get("title_th") or r.get("title") or ""
        if rtype in LAW_TYPES or (rtype in ("", "report", "web") and LAW_TITLE.search(title)):
            if i not in cited_idx:
                continue
            ft = str(r.get("fulltext") or "").split(" ")[0]
            ok = bool(ft) and os.path.exists(os.path.join(base, ft))
            if not ok:
                out("WARN", "D1", f"กฎหมาย {label(r)} ไม่มีไฟล์ตัวบทที่ตรวจได้ใน fulltext/ (ช่อง `fulltext`={r.get('fulltext')!r}) ต้องมีตัวบทก่อนเขียน/ย่อข้อความกฎหมาย")
    secs = {}
    for m2 in SECTION.finditer(body_clean):
        secs.setdefault(re.sub(r"\s+", " ", m2.group(0)), []).append(lines_before(m2.start()))
    if secs:
        print("INFO D2: มาตรา/ข้อที่อ้างในเนื้อหา (เทียบถ้อยคำกับตัวบททุกจุด โดยเฉพาะหลังย่อความยาว):")
        for k, v in secs.items():
            print(f"      - {k}: บ.{', '.join(str(x) for x in sorted(set(v)))}")
        infos += 1
        if not has_verbatim:
            out("INFO", "D3", "ไม่มีข้อความใน [ตัวบท]...[/ตัวบท] ถ้ามีประโยคที่ยกถ้อยคำกฎหมายตรงตัว ควรครอบไว้เพื่อให้ขั้นปรับภาษาและการย่อไม่แตะ")

    # E: wording
    for m3 in re.finditer(r"มีนัยสำคัญ(?!ทางสถิติ)", body_clean):
        out("WARN", "E1", f"บ.{lines_before(m3.start())} \"มีนัยสำคัญ\" ไม่มี \"ทางสถิติ\"")
    for m3 in re.finditer(r"R²|R2\b|R-squared|อาร์สแควร์", body_clean):
        pr = para_of(m3.start())
        if not pr:  # inside a table or caption: no room for the clause, check by eye
            continue
        win = body_clean[max(pr[0], m3.start() - 120): min(pr[1], m3.end() + 160)]
        if not re.search(r"อธิบาย|explain|ความแปรปรวน|variance", win):
            out("WARN", "E3", f"บ.{lines_before(m3.start())} R² ไม่ได้ระบุว่าอธิบายความแปรปรวนของตัวแปรใด")
    for m3 in re.finditer(r"ไม่พบ(งาน|การศึกษา|บทความ|งานวิจัย)|ยังไม่มี(งาน|การศึกษา|งานวิจัย)|no (retrieved |Thai )?(study|studies|research)", body_clean, re.I):
        pr = para_of(m3.start())
        win = pr[2] if pr else ""
        tied = re.search(r"สืบค้น|ขอบเขต|ฐานข้อมูล|คำค้น|retrieved|search", win, re.I)
        out("INFO" if tied else "WARN", "E2", f"บ.{lines_before(m3.start())} ข้ออ้าง \"{m3.group(0)}\" {'ผูกกับขอบเขตการค้นในย่อหน้าเดียวกัน' if tied else 'ไม่ได้ผูกกับขอบเขตการค้นในย่อหน้าเดียวกัน (เติม \"จากการสืบค้นตามขอบเขต…\" หรืออ้างย่อหน้าวิธีการ)'}")

    # F: abstracts
    th = section(text, "บทคัดย่อ")
    en = section(text, "Abstract")
    if th and en:
        en_digits = re.sub(r"\b(" + "|".join(EN_NUM_WORDS) + r")\b", lambda m: " " + EN_NUM_WORDS[m.group(1).lower()] + " ", en, flags=re.I)
        th_n = {digits(x) for x in NUM.findall(th) if digits(x)}
        en_n = {digits(x) for x in NUM.findall(en_digits) if digits(x)}
        th_n = {x for x in th_n if not (len(x) == 4 and 1900 <= int(x) <= 2700)}
        en_n = {x for x in en_n if not (len(x) == 4 and 1900 <= int(x) <= 2700)}
        if th_n != en_n:
            out("WARN", "F1", f"ตัวเลขในบทคัดย่อกับ Abstract ไม่ตรงกัน: ไทยมี {sorted(th_n - en_n) or '-'} ที่อังกฤษไม่มี; อังกฤษมี {sorted(en_n - th_n) or '-'} ที่ไทยไม่มี (ปีถูกข้าม)")
        th_h = bool(re.search(r"ยังไม่ได้ทดสอบ|ยังไม่ผ่านการทดสอบ|ข้อสันนิษฐาน|สมมติฐาน|เชิงแนวคิด|ข้อเสนอ", th))
        en_h = bool(re.search(r"untested|not (yet )?(been )?tested|hypothes|proposition|conceptual|propos", en, re.I))
        if th_h != en_h:
            out("WARN", "F2", f"สถานะ \"ยังไม่ทดสอบ/ข้อเสนอ\" ปรากฏใน{'บทคัดย่อไทยแต่ไม่ปรากฏใน Abstract' if th_h else ' Abstract แต่ไม่ปรากฏในบทคัดย่อไทย'}")
    elif a.pages:
        out("INFO", "F0", "ไม่พบหัวข้อ # บทคัดย่อ หรือ # Abstract จึงไม่ได้เทียบสองภาษา")

    # G: length
    prose_chars = sum(len(re.sub(r"\s", "", t)) for _, _, t in paras)
    table_rows = sum(1 for l in body_clean.splitlines() if l.strip().startswith("|") and not re.match(r"^\|\s*-", l.strip()))
    figures = len(re.findall(r"^!\[", body_clean, re.M))
    est_body = prose_chars / a.chars_per_page + table_rows * 0.06 + figures * 0.4
    est_refs = len(refs) * a.ref_lists / a.refs_per_page
    est = est_body + est_refs
    print(f"INFO G0: ร้อยแก้ว {prose_chars:,} อักขระ, แถวตาราง {table_rows}, ภาพ {figures}, อ้างอิง {len(refs)} → ประมาณ {est_body:.1f} หน้าเนื้อหา + {est_refs:.1f} หน้าอ้างอิง ≈ {est:.1f} หน้า (ค่าประมาณ นับจริงจาก .docx เท่านั้น)")
    infos += 1
    if a.pages and est > a.pages:
        out("WARN", "G1", f"ประมาณ {est:.1f} หน้า เกินเพดาน {a.pages} หน้า: ตัดตอนนี้ก่อนเกลาภาษาและก่อนเรียกผู้ตรวจ (ห้ามตัดเงื่อนไขกฎหมายและย่อหน้าที่เป็นฐานของบทคัดย่อ)")

    uncited = [label(r) for i, r in enumerate(refs) if i not in cited_idx]
    if uncited:
        out("INFO", "H1", f"แหล่งใน refs.json ที่สคริปต์จับการอ้างในเนื้อหาไม่ได้ ({len(uncited)}): {', '.join(uncited)} (อาจเป็นข้อจำกัดการจับคู่ ตรวจด้วย check_citations.py)")

    print(f"\nสรุป: WARN {warns}, INFO {infos}, การอ้างที่จับได้ {len(cites)} จุดจาก {len(refs)} แหล่ง  — ผลว่างไม่ได้แปลว่าถูก ต้องเทียบแหล่งเองตามข้อ INFO")
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
