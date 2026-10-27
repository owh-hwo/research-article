#!/usr/bin/env python3
"""ตรวจคำไทยที่ถูกตัดข้ามบรรทัดใน PDF โดยยึดขอบเขตคำจากร่างต้นฉบับ."""

import argparse
import re
import sys
from pathlib import Path


THAI_WORD = re.compile(r"[ก-๛]{3,}\Z")
THAI_END = re.compile(r"[ก-๛]+$")
THAI_START = re.compile(r"^[ก-๛]+")
INVISIBLE = str.maketrans("", "", "\u200b\u2060\ufeff\u00ad")


def compact(text):
    """ละช่องว่างและอักขระควบคุมการตัดคำ โดยไม่เปลี่ยนอักษรไทย."""
    return re.sub(r"\s+", "", text.translate(INVISIBLE))


def draft_index(source, tokenize):
    """ทำดัชนีขอบคำจากร่างไว้ใช้กับ PDF ทุกฉบับ โดยแก้การแบ่งกำกวมเฉพาะจุด."""
    pieces = []
    interiors = {}
    offset = 0
    # แยกช่วงไทยก่อน เพื่อไม่ให้ตัวตัดคำประมวลผล URL และบรรณานุกรมภาษาอื่นที่ยาว
    for run in re.findall(r"[ก-๛]+|[^ก-๛]+", source.translate(INVISIBLE)):
        is_thai = bool(THAI_START.match(run))
        tokens = tokenize(run, engine="newmm") if is_thai else [run]
        run_start = offset
        short_starts = set()
        boundaries = {offset}
        for token in tokens:
            word = compact(token)
            pieces.append(word)
            # พยางค์สระนำสั้นอาจเกิดจากการแบ่งกำกวม เช่น “เส/นอกรอบ”
            if re.fullmatch(r"[เแโ][ก-ฮ]", word):
                short_starts.add(offset)
            if THAI_WORD.fullmatch(word):
                for cut in range(1, len(word)):
                    interiors[offset + cut] = word
            offset += len(word)
            boundaries.add(offset)
        if short_starts:
            alternate_offset = run_start
            replacement_start = None
            replacement_words = []
            for word in tokenize(run, engine="longest"):
                # ใช้คำยาวเฉพาะจุดกำกวมนี้ ไม่เหมารวมคำประสมทุกคำว่าห้ามแบ่ง
                if alternate_offset in short_starts and THAI_WORD.fullmatch(word):
                    if replacement_start is None:
                        replacement_start = alternate_offset
                if replacement_start is not None:
                    replacement_words.append((alternate_offset, word))
                alternate_offset += len(word)
                if replacement_start is not None and alternate_offset in boundaries:
                    # แทนการแบ่งจนถึงขอบที่ทั้งสองวิธีตรงกัน ป้องกันขอบคำเก่าค้างอยู่
                    for position in range(replacement_start, alternate_offset + 1):
                        interiors.pop(position, None)
                    for start, replacement in replacement_words:
                        if THAI_WORD.fullmatch(replacement):
                            for cut in range(1, len(replacement)):
                                interiors[start + cut] = replacement
                    replacement_start = None
                    replacement_words = []
    return "".join(pieces), interiors


def find_breaks(lines, flat, interiors):
    """เทียบบริบทรอยต่อกับร่าง ไม่ตัดคำ PDF ใหม่จนทำคำที่ขาดดูถูกต้อง."""
    for line_number, (left, right) in enumerate(zip(lines, lines[1:]), 1):
        left = left.translate(INVISIBLE).rstrip()
        right = right.translate(INVISIBLE).lstrip()
        tail = THAI_END.search(left)
        head = THAI_START.match(right)
        if not tail or not head:
            continue
        before, after = tail[0][-24:], head[0][:24]
        context = before + after
        position = flat.find(context)
        words = set()
        boundary_match = False
        while position != -1:
            word = interiors.get(position + len(before))
            if word:
                words.add(word)
            else:
                boundary_match = True
            position = flat.find(context, position + 1)
        # ถ้าบริบทเดียวกันมีทั้งขอบคำและกลางคำ ให้รายงานเพื่อให้คนยืนยัน
        if words:
            yield line_number, before + " / " + after, sorted(words), boundary_match


def scan_pdf(path, flat, interiors, pdfium):
    """คืนจุดต้องตรวจและหน้าที่ไม่มีข้อความ พร้อมปิดทรัพยากร PDF."""
    hits, unreadable = [], []
    document = pdfium.PdfDocument(str(path))
    try:
        if not len(document):
            raise ValueError("PDF ไม่มีหน้า")
        for page_number in range(len(document)):
            page = document[page_number]
            try:
                textpage = page.get_textpage()
                try:
                    text = textpage.get_text_range()
                finally:
                    textpage.close()
            finally:
                page.close()
            if not compact(text):
                unreadable.append(page_number + 1)
                continue
            # ไม่ข้ามบรรทัดว่าง เพราะอาจเป็นคนละย่อหน้าหรือคนละช่องตาราง
            lines = text.splitlines()
            for line, context, words, ambiguous in find_breaks(lines, flat, interiors):
                hits.append((page_number + 1, line, context, words, ambiguous))
    finally:
        document.close()
    return hits, unreadable


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="หาคำไทยที่อาจถูกตัดข้ามบรรทัดใน PDF โดยเทียบขอบคำจากร่าง",
        epilog="ต้องมี pythainlp และ pypdfium2; รหัสออก 0 = ไม่พบ, 1 = พบจุดต้องตรวจ, "
        "2 = ตรวจไม่ครบ/ข้อผิดพลาด (มีลำดับก่อน 1) ผลไม่พบยังต้องตรวจภาพ PDF จริง",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="แสดงวิธีใช้และจบการทำงาน")
    parser.add_argument("draft", type=Path, help="ไฟล์ draft.md ที่ตรงกับ PDF รุ่นที่จะตรวจ")
    parser.add_argument("pdf", type=Path, nargs="+", help="ไฟล์ PDF หนึ่งไฟล์หรือหลายไฟล์")
    args = parser.parse_args(argv)
    try:
        import pypdfium2 as pdfium
        from pythainlp import word_tokenize
    except ImportError as exc:
        print(f"ขาดแพ็กเกจ: {exc.name}; ติดตั้งด้วย pip install pythainlp pypdfium2", file=sys.stderr)
        return 2
    try:
        source = args.draft.read_text(encoding="utf-8-sig")
        flat, interiors = draft_index(source, word_tokenize)
        if not interiors:
            raise ValueError("ร่างไม่มีคำไทยยาวอย่างน้อยสามอักขระที่ใช้เทียบได้")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"อ่านร่างไม่ได้: {exc}", file=sys.stderr)
        return 2

    found = False
    incomplete = False
    for path in args.pdf:
        try:
            hits, unreadable = scan_pdf(path, flat, interiors, pdfium)
        except (OSError, ValueError, pdfium.PdfiumError) as exc:
            print(f"{path}: ตรวจไม่ได้: {exc}", file=sys.stderr)
            incomplete = True
            continue
        print(f"{path}: พบ {len(hits)} จุดที่ต้องตรวจ")
        found = found or bool(hits)
        for page, line, context, words, ambiguous in hits:
            note = " (บริบทซ้ำมีขอบคำต่างกัน ต้องยืนยันด้วยตา)" if ambiguous else ""
            print(f"  หน้า {page} บรรทัดสกัด {line}: {context} — คำในร่าง: {', '.join(words)}{note}")
        if unreadable:
            print("  ตรวจไม่ได้ในหน้าที่ไม่มีข้อความสกัด: " + ", ".join(map(str, unreadable)))
            incomplete = True
    print("ผลนี้เป็นตัวช่วย ต้องเทียบภาพ PDF จริง โดยเฉพาะคำเฉพาะ คอลัมน์ และรอยต่อข้ามหน้า")
    return 2 if incomplete else 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
