"""Check a draft.md article for citation integrity and journal basics.

Usage:
  python -I check_citations.py draft.md [--min 10] [--year-be 2569]

Checks
  ERROR  fewer than --min reference entries
  ERROR  reference entry never cited in the text
  ERROR  in-text citation with no matching reference entry
  ERROR  Tipitaka cited in text but no มหาจุฬาลงกรณราชวิทยาลัย entry
  WARN   Thai entries not before English entries / not alphabetical
  WARN   "( 2569)" spacing, unfilled [รอข้อมูล ...] placeholders
  WARN   keyword count outside 3-5, abstract length outside 300-400 words (needs pythainlp for Thai)
  INFO   counts by language, share of references from the last 5 years
Exit code 1 when any ERROR is found.
"""
import argparse, datetime, re, sys

THAI = re.compile(r"[฀-๿]")
REF_HEAD = re.compile(r"^#\s*(เอกสารอ้างอิง|บรรณานุกรม|References?)\s*$", re.M)
YEAR = r"(\d{4}[a-zก-ฮ]?)"
LEAD_VOWELS = "เแโใไ"


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def parse_entries(block):
    entries, prev_author = [], None
    for para in re.split(r"\n\s*\n", block.strip()):
        para = norm(re.sub(r"^[-*]\s+", "", para.strip()))
        if not para:
            continue
        m = re.match(r"^(.*?)\.?\s*\(\s*" + YEAR, para)
        if not m:
            entries.append({"raw": para, "author": None, "year": None})
            continue
        author, year = m.group(1).strip().rstrip("."), m.group(2)
        if re.fullmatch(r"_+", author):
            author = prev_author
        prev_author = author
        entries.append({"raw": para, "author": author, "year": year, "thai": bool(THAI.search(para[:40]))})
    return entries


def first_author_forms(author):
    """Strings that should appear in the text when this entry is cited."""
    if THAI.search(author):
        first = re.split(r"\s+และ", author)[0].strip()
        return [first]
    a = re.sub(r"\bet al\.?", "", author).strip().rstrip(",")
    surname = a.split(",")[0].strip()
    forms = [surname]
    words = surname.split()
    if "," not in a and len(words) > 4:
        # corporate author or titled entry (law, report): in-text usually shortens it,
        # e.g. "Ministerial Regulation No. 123 (B.E. 2565) issued ..." -> "Ministerial Regulation No. 123"
        forms.append(" ".join(words[:4]))
    return forms


def cited(entry, body):
    for form in first_author_forms(entry["author"]):
        for m in re.finditer(re.escape(form), body):
            window = body[m.end(): m.end() + 120]
            if re.search(re.escape(entry["year"]) + r"(?!\d)", window):
                return True
    return False


def in_text_citations(body):
    found = []
    for m in re.finditer(r"\(([^()]*?\d{4}[a-zก-ฮ]?)\)", body):
        inner = m.group(1)
        for piece in inner.split(";"):
            pm = re.match(r"\s*(.+?),\s*" + YEAR + r"\s*$", piece)
            if pm:
                found.append((norm(pm.group(1)), pm.group(2), m.start(), "paren"))
            elif re.fullmatch(r"\s*" + YEAR + r"\s*", piece):
                before = norm(body[max(0, m.start() - 80): m.start()])
                if re.search(r"(ผู้เขียน|ผู้วิจัย|the authors?|พ\.ศ\.|ค\.ศ\.)\s*$", before, re.I):
                    continue  # "ที่มา: ผู้เขียน (2569)" and bare era years are not citations
                found.append((before, piece.strip(), m.start(), "narrative"))
    return found


def matches(name, year, entries, narrative):
    for e in entries:
        if not e["author"] or e["year"] != year:
            continue
        for form in first_author_forms(e["author"]):
            if (form in name) if narrative else name.startswith(form) or form.startswith(name.split(" et al")[0].split(" และ")[0]):
                return True
    return False


def thai_sort_key(s):
    s = s.replace("_", "")
    if s and s[0] in LEAD_VOWELS and len(s) > 1:
        s = s[1] + s[0] + s[2:]
    return s


def word_count(text):
    if THAI.search(text):
        try:
            from pythainlp.tokenize import word_tokenize
            return len([w for w in word_tokenize(text, keep_whitespace=False) if w.strip()])
        except Exception:
            return None
    return len(text.split())


def section(text, name):
    m = re.search(r"^#\s*" + name + r"\s*$(.*?)(?=^#\s)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("draft")
    p.add_argument("--min", type=int, default=10)
    p.add_argument("--year-be", type=int, default=datetime.date.today().year + 543)
    a = p.parse_args()

    text = strip_frontmatter(open(a.draft, encoding="utf-8").read())
    hm = REF_HEAD.search(text)
    if not hm:
        print("ERROR  ไม่พบหัวข้อ '# เอกสารอ้างอิง'")
        sys.exit(1)
    body = text[: hm.start()]
    nxt = re.search(r"^#\s", text[hm.end():], re.M)
    ref_block = text[hm.end(): hm.end() + nxt.start()] if nxt else text[hm.end():]
    entries = parse_entries(ref_block)
    errors = warns = 0

    def out(level, msg):
        nonlocal errors, warns
        errors += level == "ERROR"
        warns += level == "WARN"
        print(f"{level:5}  {msg}")

    n = len(entries)
    th = sum(1 for e in entries if e.get("thai"))
    out("INFO", f"เอกสารอ้างอิง {n} รายการ (ไทย {th}, อังกฤษ {n - th})")
    if n < a.min:
        out("ERROR", f"อ้างอิงน้อยกว่าขั้นต่ำ {a.min} รายการ")

    for e in entries:
        if not e["author"]:
            out("ERROR", f"อ่านผู้แต่ง/ปีไม่ได้: {e['raw'][:90]}")
        elif not cited(e, body):
            out("ERROR", f"ไม่ถูกอ้างในเนื้อหา: {e['author']} ({e['year']})")

    seen = set()
    for name, year, pos, kind in in_text_citations(body):
        if not matches(name, year, entries, kind == "narrative"):
            label = name if kind == "paren" else "…" + name[-40:]
            if (label, year) in seen:
                continue
            seen.add((label, year))
            if kind == "paren":
                out("ERROR", f"อ้างในเนื้อหาแต่ไม่มีท้ายเรื่อง: ({name}, {year})")
            else:
                out("WARN", f"อาจเป็นการอ้างที่ไม่มีท้ายเรื่อง: {label} ({year})")

    if re.search(r"\(\s*[ก-ฮ][^()\s]*\.[^()]*\(ไทย\)\s*\d+/\d+", body) and not any(
            (e["author"] or "").startswith("มหาจุฬาลงกรณราชวิทยาลัย") for e in entries):
        out("ERROR", "มีการอ้างพระไตรปิฎกในเนื้อหา แต่ไม่มีรายการ มหาจุฬาลงกรณราชวิทยาลัย. (2539). พระไตรปิฎก...")

    langs = [bool(e.get("thai")) for e in entries if e["author"]]
    if True in langs and False in langs and langs.index(False) < len(langs) - 1 - langs[::-1].index(True):
        out("WARN", "รายการภาษาไทยต้องอยู่ก่อนภาษาอังกฤษทั้งหมด")
    for group in (True, False):
        names = [e["author"] for e in entries if e["author"] and bool(e.get("thai")) == group]
        keys = [thai_sort_key(x) if group else x.lower() for x in names]
        for i in range(1, len(keys)):
            if keys[i] < keys[i - 1]:
                out("WARN", f"ลำดับตัวอักษรอาจผิด: '{names[i - 1]}' มาก่อน '{names[i]}'")

    for m in re.finditer(r"\(\s+\d{4}|\d{4}\s+\)", text):
        out("WARN", f"เว้นวรรคในวงเล็บปี: '{text[max(0, m.start() - 15): m.end() + 2]}'")
    for m in re.finditer(r"\[รอข้อมูล[^\]]*\]", text):
        out("WARN", f"ยังมีช่องรอข้อมูล: {m.group(0)}")

    for label in ("คำสำคัญ", "Keywords"):
        km = re.search(r"^" + label + r"\s*:\s*(.+)$", text, re.M)
        if km:
            k = [x for x in re.split(r"\s*,\s*", km.group(1).strip()) if x]
            if not 3 <= len(k) <= 5:
                out("WARN", f"{label} มี {len(k)} คำ (เกณฑ์ 3-5)")
        else:
            out("WARN", f"ไม่พบบรรทัด {label}:")
    for name in ("บทคัดย่อ", "Abstract"):
        sec = re.split(r"^(คำสำคัญ|Keywords)\s*:", section(text, name), flags=re.M)[0]
        if sec:
            wc = word_count(sec)
            if wc is None:
                out("INFO", f"{name}: ติดตั้ง pythainlp เพื่อนับคำภาษาไทย (pip install pythainlp)")
            elif not 300 <= wc <= 400:
                out("WARN", f"{name} ยาว {wc} คำ (เกณฑ์ 300-400)")
            else:
                out("INFO", f"{name} ยาว {wc} คำ")

    recent = 0
    for e in entries:
        if e["year"] and e["year"][:4].isdigit():
            y = int(e["year"][:4])
            be = y if y > 2400 else y + 543
            recent += a.year_be - be <= 5
    if n:
        out("INFO", f"อ้างอิงใน 5 ปีล่าสุด {recent}/{n} ({recent * 100 // n}%)")

    print(f"\nสรุป: ERROR {errors}, WARN {warns}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
