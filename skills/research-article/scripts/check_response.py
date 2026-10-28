#!/usr/bin/env python3
"""Check that response-to-reviewers.md answers every item of a merged review and uses the fixed
status vocabulary.

Usage:
  python -I check_response.py review-roundN.md response-to-reviewers.md --round N

Collects item codes from the merged review (table codes such as S1, E3, W12, and role codes such as
editor:E1, main:2, specialist:4) and looks for each in the "## รอบที่ N" section of the response
file. Every table row in that section must end with one of:
  แก้แล้ว-ตรวจใน PDF แล้ว | แก้แล้ว | แก้บางส่วน | ไม่แก้ (…เหตุผล…) | ยุติ | ไม่ต้องแก้ | ข้อเสนอ (ไม่แก้)
Rows that say "ตรวจใน PDF แล้ว" are listed so the author can confirm the PDF was actually viewed.

Exit 0 = complete, 1 = missing items or bad status, 2 = error. Lesson behind this: in past rounds
status rows were written as "fixed" for items that were only partly fixed, and several review items
had no row at all; both cost an extra round.
"""
import argparse
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CODE = re.compile(r"^\|\s*([A-Z]{1,2}\d{1,2})\s*\|", re.M)
ROLE = re.compile(r"\b(editor|main|context|specialist|methods?|dhamma|reviewer-[a-z]+|กองบรรณาธิการ)\s*:\s*([A-Z]?\d{1,2})\b")
STATUS = re.compile(r"(แก้แล้ว-ตรวจใน PDF แล้ว|แก้แล้วในรอบ|แก้แล้ว|แก้บางส่วน|ไม่แก้|ยุติ|ไม่ต้องแก้|ข้อเสนอ \(ไม่แก้\)|ไม่มีแล้ว|ไม่รับ)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("review")
    ap.add_argument("response")
    ap.add_argument("--round", required=True, help="round number as written in the response heading (## รอบที่ N)")
    a = ap.parse_args()
    try:
        rev = open(a.review, encoding="utf-8").read()
        resp = open(a.response, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        print(f"ERROR {e}")
        return 2
    codes = []
    for m in CODE.finditer(rev):
        if m.group(1) not in codes:
            codes.append(m.group(1))
    roles = []
    for m in ROLE.finditer(rev):
        k = f"{m.group(1)}:{m.group(2)}"
        if k not in roles:
            roles.append(k)
    sec = re.search(r"^##\s*รอบที่\s*" + re.escape(str(a.round)) + r"\b.*?(?=^##\s|\Z)", resp, re.M | re.S)
    if not sec:
        print(f"ERROR ไม่พบหัวข้อ '## รอบที่ {a.round}' ใน {a.response}")
        return 2
    body = sec.group(0)
    warns = 0
    missing = [c for c in codes if not re.search(r"(?<![A-Z0-9])" + re.escape(c) + r"(?![0-9])", body)]
    missing_roles = [r for r in roles if not re.search(re.escape(r.split(":")[0]) + r"\s*:?\s*" + re.escape(r.split(":")[1]) + r"\b", body)]
    if missing:
        warns += 1
        print(f"WARN C1: รหัสในรายงานรวมที่ไม่มีแถวตอบในรอบที่ {a.round} ({len(missing)}/{len(codes)}): {', '.join(missing)}")
    if missing_roles:
        print(f"INFO C2: รหัสผู้ตรวจ:ข้อ ที่ไม่ปรากฏตรงตัวในตารางตอบ ({len(missing_roles)}/{len(roles)}): {', '.join(missing_roles)} (ตกลงได้ถ้ารวมอยู่ในรหัส S/E แล้ว)")
    rows = [l for l in body.split("\n") if l.strip().startswith("|") and not re.match(r"^\|\s*-", l.strip()) and not re.match(r"^\|\s*(ข้อ|รหัส|ลำดับ)", l.strip())]
    bad = []
    pdf_rows = []
    for l in rows:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        st = cells[-1]
        if not STATUS.search(st):
            bad.append((cells[0][:40], st[:40]))
        if "PDF แล้ว" in st:
            pdf_rows.append(cells[0][:50])
    if bad:
        warns += 1
        print(f"WARN C3: แถวที่สถานะไม่อยู่ในชุดคำที่กำหนด ({len(bad)}):")
        for k, s in bad:
            print(f"      - {k} → \"{s}\"")
    if pdf_rows:
        print(f"INFO C4: แถวที่ระบุว่าตรวจใน PDF แล้ว ({len(pdf_rows)}) ยืนยันว่าเปิดไฟล์ใหม่จริง: {'; '.join(pdf_rows)}")
    print(f"\nสรุป: รหัสในรายงานรวม {len(codes)} (+ รหัสผู้ตรวจ {len(roles)}), แถวตอบ {len(rows)}, WARN {warns}")
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
