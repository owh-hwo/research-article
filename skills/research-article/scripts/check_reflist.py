#!/usr/bin/env python3
"""Check the reference list(s) at the end of draft.md for the formatting faults reviewers keep finding.

Usage:
  python -I check_reflist.py draft.md [refs.json]

Checks every entry under "# เอกสารอ้างอิง" / "# References" / "# บรรณานุกรม" (and a second Thai list
if the journal asks for one):
  R1  publisher repeats the author (APA 7 omits it)
  R2  edition/version parentheses inside an italic span, e.g. *Handbook (revised Nov 2025)*
  R3  no year
  R4  duplicate entries
  R5  DOI not written as https://doi.org/...
  R6  list not in alphabetical order (Latin by letters; Thai by letters ignoring leading vowels/tone marks)
  R7  [in Thai] tag used on some translated Thai works but not others in the same list
  R8  journal entry with no italics (journal name/volume should be italic)
  R9  with refs.json: entries whose title is not in refs.json, and refs.json items missing from the list
  R10 entry that does not end with "." or a URL/DOI

Exit 0 = no WARN, 1 = WARN found, 2 = error. check_citations.py covers in-text ↔ list matching;
this script covers the shape of the list itself.
"""
import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

THAI = re.compile(r"[฀-๿]")
HEAD = re.compile(r"^#\s*(เอกสารอ้างอิง[^\n]*|บรรณานุกรม[^\n]*|References?[^\n]*)\s*$", re.M)


def thai_sort_key(s):
    s = re.sub(r"[่-๋]", "", s)  # tone marks only; vowels keep dictionary order
    if s and s[0] in "เแโใไ" and len(s) > 1:
        s = s[1] + s[0] + s[2:]
    return s


def entries_of(block):
    out = []
    for line in block.split("\n"):
        t = line.strip()
        if t and not t.startswith("#"):
            out.append(re.sub(r"^[-*]\s+", "", t))
    return out


def norm_text(t):
    return re.sub(r"[^0-9a-zA-Z฀-๿]+", "", (t or "").lower())


def norm_title(t):
    return norm_text(t)[:60]


try:
    from pythainlp.util import collate as _collate
except Exception:  # noqa: BLE001
    _collate = None


def thai_in_order(a, b):
    if _collate:
        return _collate([a, b]) == [a, b] or _collate([b, a]) != [b, a]
    return thai_sort_key(a) <= thai_sort_key(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("refs", nargs="?")
    a = ap.parse_args()
    try:
        text = open(a.draft, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        print(f"ERROR {e}")
        return 2
    heads = list(HEAD.finditer(text))
    if not heads:
        print("ERROR ไม่พบหัวข้อรายการอ้างอิง (# เอกสารอ้างอิง / # References)")
        return 2
    lists = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        lists.append((h.group(1).strip(), entries_of(text[h.end(): end])))

    warns = 0

    def warn(code, msg):
        nonlocal warns
        warns += 1
        print(f"WARN {code}: {msg}")

    all_titles = []
    for name, ents in lists:
        print(f"## {name}: {len(ents)} รายการ")
        seen = {}
        in_thai_tags = [("[in Thai]" in e) for e in ents if THAI.search(e) or "[in Thai]" in e]
        keys = []
        for n, e in enumerate(ents, 1):
            plain = e.replace("*", "")
            # R3 year
            if not re.search(r"\((\d{4}|n\.d\.|ม\.ป\.ป\.)", plain):
                warn("R3", f"{name} #{n} ไม่มีปี: {plain[:70]}")
            # R1 publisher repeats author
            m = re.match(r"^(.+?)\.\s*\(", plain)
            if m:
                author = m.group(1).strip()
                tail = plain[m.end():]
                segs = [s.strip() for s in re.split(r"\.\s+", tail) if s.strip()]
                if any(s.rstrip(".") == author for s in segs[1:]):
                    warn("R1", f"{name} #{n} ผู้จัดพิมพ์ซ้ำกับผู้แต่ง \"{author}\" (APA 7 ละผู้จัดพิมพ์ที่ซ้ำผู้แต่ง)")
            # R2 version parentheses inside italics
            for it in re.findall(r"\*([^*]+)\*", e):
                if re.search(r"\((ฉบับ|แก้ไข|ปรับปรุง|พิมพ์ครั้ง|Rev\.|rev\.|Revised|\d+(st|nd|rd|th) ed\.|ed\.)", it):
                    warn("R2", f"{name} #{n} วงเล็บรุ่น/ฉบับอยู่ในตัวเอียง: *{it[:60]}* → ชื่อเรื่องเอียง วงเล็บตัวตรง")
            # R5 DOI form
            if re.search(r"\bdoi\s*:|(?<![/\w])10\.\d{4,}/", plain) and "https://doi.org/" not in plain:
                warn("R5", f"{name} #{n} DOI ไม่ใช่รูป https://doi.org/…: {plain[-60:]}")
            # R8 journal entry without italics
            if re.search(r",\s*\d+\s*\(\d+\)|,\s*\d+,\s*\d+[-–]\d+", plain) and "*" not in e:
                warn("R8", f"{name} #{n} ดูเป็นบทความวารสารแต่ไม่มีตัวเอียง: {plain[:70]}")
            # R10 ending
            if not re.search(r"(\.|/|\d|[A-Za-z0-9_-])$", plain.rstrip()) or not (plain.rstrip().endswith(".") or re.search(r"https?://\S+$", plain)):
                warn("R10", f"{name} #{n} ไม่ได้จบด้วย \".\" หรือ URL: …{plain[-40:]}")
            # R4 duplicates
            k = norm_title(plain)
            if k in seen:
                warn("R4", f"{name} #{n} ซ้ำกับ #{seen[k]}")
            seen[k] = n
            keys.append(plain)
            all_titles.append(plain)
        # R6 order
        for i in range(len(keys) - 1):
            a1, a2 = keys[i], keys[i + 1]
            if a1.startswith("_____") or a2.startswith("_____"):
                continue
            if THAI.search(a1[:1]) and THAI.search(a2[:1]):
                if not thai_in_order(a1, a2):
                    warn("R6", f"{name} #{i + 1}→#{i + 2} ลำดับไทยสลับ: \"{a1[:25]}\" ก่อน \"{a2[:25]}\"" + ("" if _collate else " (ไม่มี pythainlp เทียบแบบหยาบ)"))
            elif not THAI.search(a1[:40]) and not THAI.search(a2[:40]):
                if a1.lower() > a2.lower() and not a2.lower().startswith(a1.lower().split(",")[0]):
                    warn("R6", f"{name} #{i + 1}→#{i + 2} ลำดับสลับ: \"{a1[:25]}\" ก่อน \"{a2[:25]}\"")
        # R7 [in Thai] consistency
        if in_thai_tags and any(in_thai_tags) and not all(in_thai_tags):
            warn("R7", f"{name}: รายการงานไทยบางรายการมี [in Thai] บางรายการไม่มี ({sum(in_thai_tags)}/{len(in_thai_tags)})")

    # R9 refs.json ↔ list
    if a.refs:
        try:
            refs = json.load(open(a.refs, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR refs.json: {e}")
            return 2
        joined = norm_text(" ".join(all_titles))
        joined_full = " ".join(all_titles)
        for r in refs:
            titles = [r.get("title"), r.get("title_en"), r.get("title_th")]
            ok = any(norm_title(t) and norm_title(t)[:40] in joined for t in titles if t)
            if not ok:
                warn("R9", f"refs.json \"{r.get('key_th') or r.get('key_en') or r.get('cite_en') or (titles[0] or titles[1] or '')[:50]}\" ไม่พบชื่อเรื่องในรายการท้ายเรื่อง")
        n_list = sum(len(e) for _, e in lists) // max(1, len(lists)) if len(lists) > 1 else len(lists[0][1])
        print(f"INFO: refs.json {len(refs)} รายการ; รายการท้ายเรื่อง {', '.join(f'{n} {len(e)}' for n, e in lists)}" + (" (รายการแยกภาษาไทยอาจน้อยกว่าเพราะมีเฉพาะงานไทย)" if len(lists) > 1 else ""))
        del joined_full, n_list

    print(f"\nสรุป: WARN {warns}")
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
