#!/usr/bin/env python3
"""Check that key terms are used consistently across the Thai abstract, English Abstract, body,
tables and figures, and that abbreviations are defined before use.

Usage:
  python -I check_terms.py draft.md [terms.json] [--figures "figures/*.html"]

terms.json (optional) is a list of the article's key terms:
  [{"th": "ใบกำกับภาษีอิเล็กทรอนิกส์", "en": "e-Tax Invoice", "abbr": "",
    "avoid": ["ใบกำกับภาษีดิจิทัล", "electronic tax invoice"],
    "where": ["abstract", "body", "figure", "table"]}]
  th/en  the one form to use in each language (en is also what the English Abstract must use)
  abbr   optional abbreviation; its full form (th or en) must appear before the first use
  avoid  variants that must not appear anywhere (prose, tables, figure text)
  where  optional: places where the term must appear; "figure" needs --figures

Without terms.json the script still reports every abbreviation-like token (RPA, ERP, TOE ...)
with where it is first defined, and prints a terms.json skeleton to fill in.

Exit 0 = no WARN, 1 = WARN found, 2 = error. A quiet run means the listed terms are consistent,
not that the article uses the right terms.
"""
import argparse
import glob
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REF_HEAD = re.compile(r"^#\s*(เอกสารอ้างอิง|บรรณานุกรม|References?)\s*$", re.M)
ABBR = re.compile(r"\b[A-Z][A-Z0-9&-]{1,7}\b")
ABBR_SKIP = {"SME", "SMEs", "AI", "A4", "PDF", "DOI", "URL", "ISBN", "ISSN", "APA", "TCI", "USA", "UK", "OK", "II", "III", "IV"}


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def section(text, name):
    m = re.search(r"^#\s*" + name + r"\s*$(.*?)(?=^#\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def html_text(path):
    h = open(path, encoding="utf-8", errors="replace").read()
    h = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<!--.*?-->", " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    h = h.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", h)


def count(term, text):
    if not term:
        return 0
    return len(re.findall(re.escape(term), text, flags=re.I if not re.search(r"[฀-๿]", term) else 0))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("draft")
    p.add_argument("terms", nargs="?", help="terms.json (optional)")
    p.add_argument("--figures", default="figures/*.html", help="glob of figure HTML/SVG files, relative to the draft (default figures/*.html)")
    a = p.parse_args()
    try:
        raw = open(a.draft, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        print(f"ERROR cannot read draft: {e}")
        return 2
    text = strip_frontmatter(raw)
    m = REF_HEAD.search(text)
    if m:
        text = text[: m.start()]
    text = re.sub(r"\[/?ตัวบท\]", "", text)
    th_abs = section(text, "บทคัดย่อ")
    en_abs = section(text, "Abstract")
    lines = text.split("\n")
    table_text = "\n".join(l for l in lines if l.strip().startswith("|"))
    body_lines = [l for l in lines if l.strip() and not l.strip().startswith(("|", "#", "!["))]
    body = "\n".join(body_lines)
    body_only = body.replace(th_abs, "").replace(en_abs, "")
    base = os.path.dirname(os.path.abspath(a.draft))
    fig_files = sorted(glob.glob(os.path.join(base, a.figures)))
    fig_text = " ".join(html_text(f) for f in fig_files)
    captions = " ".join(re.findall(r"!\[(.*?)\]", text))

    warns = 0

    def warn(code, msg):
        nonlocal warns
        warns += 1
        print(f"WARN {code}: {msg}")

    def line_of(term, scope_text):
        for i, l in enumerate(lines, 1):
            if term in l:
                return i
        return "?"

    # ---- abbreviations (always) ----
    seen = {}
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("#"):
            continue
        for mm in ABBR.finditer(l):
            tok = mm.group(0)
            if tok in ABBR_SKIP or tok.isdigit() or len(tok) < 2:
                continue
            seen.setdefault(tok, []).append((i, l))
    defined_at = {}
    for tok, occ in seen.items():
        first_line, first_text = occ[0]
        # defined if the first occurrence is in "(TOK)" right after words, or "TOK (full form)" / "TOK หมายถึง"
        pat_def = re.compile(r"\(" + re.escape(tok) + r"\)|" + re.escape(tok) + r"\s*[\(:]|" + re.escape(tok) + r"\s*(หมายถึง|คือ|ย่อมาจาก)")
        defined_at[tok] = first_line if pat_def.search(first_text) else None
    undefined = [t for t, d in defined_at.items() if d is None and len(seen[t]) >= 2]
    if seen:
        print("INFO T0: คำย่อที่พบ (บรรทัดแรกที่ใช้ → นิยามพบที่บรรทัดแรกหรือไม่):")
        for tok, occ in sorted(seen.items(), key=lambda x: x[1][0][0]):
            print(f"      - {tok}: ใช้ {len(occ)} ครั้ง บรรทัดแรก บ.{occ[0][0]} {'นิยามในบรรทัดแรก' if defined_at[tok] else 'ไม่พบรูปแบบนิยามในบรรทัดแรก'}")
    for tok in undefined:
        warn("T1", f"คำย่อ \"{tok}\" ใช้ {len(seen[tok])} ครั้ง แต่บรรทัดแรก (บ.{seen[tok][0][0]}) ไม่มีรูป \"ชื่อเต็ม ({tok})\" ตรวจว่านิยามไว้ก่อนใช้ (ถ้าเป็นชื่อเฉพาะ/ชื่อระบบ ให้ใส่ใน ABBR_SKIP ของ terms.json: \"skip_abbr\")")

    # ---- terms.json ----
    if not a.terms:
        skeleton = [{"th": "", "en": "", "abbr": t, "avoid": [], "where": ["body"]} for t in sorted(seen)[:8]]
        print("\nINFO T9: ไม่มี terms.json จึงตรวจเฉพาะคำย่อ สร้างไฟล์จากโครงนี้แล้วเติมคำหลักของบทความ (แนวคิดหลัก ตัวแปร ชื่อกรอบ ระดับ/องค์ประกอบในภาพ):")
        print(json.dumps(skeleton, ensure_ascii=False, indent=1))
        print(f"\nสรุป: WARN {warns}")
        return 1 if warns else 0
    try:
        terms = json.load(open(a.terms, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR cannot read terms.json: {e}")
        return 2
    if isinstance(terms, dict):
        for t in terms.get("skip_abbr", []):
            ABBR_SKIP.add(t)
        terms = terms.get("terms", [])

    print(f"\nคำหลัก {len(terms)} คำ | ภาพที่อ่าน: {', '.join(os.path.basename(f) for f in fig_files) or 'ไม่มี'}")
    print("| คำ (th / en) | บทคัดย่อ | Abstract | เนื้อหา | ตาราง | ภาพ+คำบรรยาย |")
    print("|---|---|---|---|---|---|")
    for t in terms:
        th, en, abbr = t.get("th", ""), t.get("en", ""), t.get("abbr", "")
        forms_th = [x for x in (th,) if x]
        forms_en = [x for x in (en, abbr) if x]
        c_abs = sum(count(x, th_abs) for x in forms_th + ([abbr] if abbr else []))
        c_en = sum(count(x, en_abs) for x in forms_en)
        c_body = sum(count(x, body_only) for x in forms_th + forms_en)
        c_tab = sum(count(x, table_text) for x in forms_th + forms_en)
        c_fig = sum(count(x, fig_text + " " + captions) for x in forms_th + forms_en)
        print(f"| {th} / {en}{' (' + abbr + ')' if abbr else ''} | {c_abs} | {c_en} | {c_body} | {c_tab} | {c_fig} |")
        lab = th or en or abbr
        # avoid-variants anywhere
        for v in t.get("avoid", []):
            places = [name for name, txt in (("บทคัดย่อ", th_abs), ("Abstract", en_abs), ("เนื้อหา", body_only), ("ตาราง", table_text), ("ภาพ", fig_text)) if count(v, txt)]
            if places:
                warn("T2", f"พบรูปแปร \"{v}\" ของคำหลัก \"{lab}\" ใน {', '.join(places)} (บ.{line_of(v, text)}) → ใช้ \"{th if re.search(chr(0x0e00) + '-' + chr(0x0e7f), v) else en}\" ให้ตรงกันทั้งเรื่อง")
        # abstract pairing
        if th and en and c_abs and not c_en:
            warn("T3", f"\"{th}\" อยู่ในบทคัดย่อไทย แต่ Abstract ไม่มี \"{en}\"")
        if th and en and c_en and not c_abs and not count(abbr, th_abs):
            warn("T3", f"\"{en}\" อยู่ใน Abstract แต่บทคัดย่อไทยไม่มี \"{th}\"")
        # required places
        for w in t.get("where", []):
            have = {"abstract": c_abs or c_en, "body": c_body, "table": c_tab, "figure": c_fig}.get(w, 1)
            if not have:
                warn("T4", f"คำหลัก \"{lab}\" กำหนดให้ต้องปรากฏใน {w} แต่ไม่พบ" + (" (ไม่มีไฟล์ภาพให้ตรวจ)" if w == "figure" and not fig_files else ""))
        # abbreviation defined before first use
        if abbr and count(abbr, body):
            first = min((i for i, l in enumerate(lines, 1) if abbr in l and not l.strip().startswith("#")), default=None)
            full_before = any((th and th in l) or (en and en.lower() in l.lower()) for l in lines[: first]) if first else True
            full_same = first and ((th and th in lines[first - 1]) or (en and en.lower() in lines[first - 1].lower()))
            if first and not (full_before or full_same):
                warn("T5", f"คำย่อ \"{abbr}\" ใช้ครั้งแรก บ.{first} ก่อนที่ชื่อเต็ม \"{th or en}\" จะปรากฏ")

    print(f"\nสรุป: WARN {warns} — ตารางด้านบนใช้ดูว่าคำหลักกระจายครบทุกส่วนหรือไม่ (0 ในช่องที่ควรมี = ตรวจ)")
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
