#!/usr/bin/env python3
"""Build refs-log.md from the search-result files, refs.json and refs-dropped.json.

Usage:
  python -I make_refs_log.py <workdir> [--out refs-log.md] [--force] [--date "26 ตุลาคม 2569"]
                             [--tci-glob "tci_*.json"] [--intl-glob "intl_*.json"] [--exclude tci_selected.json]

Counts records in every search-result file written by tci_search.py / academic_search.py --json
(record counts come from the files, never from what a database page displayed), de-duplicates
across files (TCI by id, international by DOI or normalized title), maps each entry of refs.json
back to the file it came from, and lists refs-dropped.json with reasons. Queries are inferred from
file names (tci_<term>_<term>.json -> "term+term"; tci_abs_... -> abstract field) and must be
checked by hand; the generated file marks them.

Writes refs-log.md only if it does not exist (or with --force); otherwise refs-log.generated.md so a
hand-written log is never overwritten. Run it at step 3, right after searching, and again after any
drop, so the review-method paragraph is written from real counts.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"WARN cannot read {path}: {e}")
        return []
    if isinstance(d, dict):
        for k in ("records", "results", "items", "refs"):
            if isinstance(d.get(k), list):
                return d[k]
        return []
    return d if isinstance(d, list) else []


def norm_title(t):
    return re.sub(r"[^0-9a-zA-Z฀-๿]+", "", (t or "").lower())[:80]


def query_from_name(name):
    stem = os.path.splitext(os.path.basename(name))[0]
    field = "บทคัดย่อ" if stem.startswith(("tci_abs_", "intl_abs_")) else "ชื่อเรื่อง"
    stem = re.sub(r"^(tci|intl)_(abs_)?", "", stem)
    if re.fullmatch(r"\d+", stem):
        return f"(ชุดที่ {stem}: ระบุคำค้นเอง)", field
    return stem.replace("_", "+"), field


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--out", default="refs-log.md")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--date", default="", help="search date to print (default: today)")
    ap.add_argument("--tci-glob", default="tci_*.json")
    ap.add_argument("--intl-glob", default="intl_*.json")
    ap.add_argument("--exclude", default="tci_selected.json", help="comma-separated result files that are selections, not searches")
    a = ap.parse_args()
    wd = a.workdir
    excl = {x.strip() for x in a.exclude.split(",") if x.strip()}
    today = datetime.date.today()
    date = a.date or f"{today.day} {['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'][today.month]} {today.year + 543}"

    tci_files = [f for f in sorted(glob.glob(os.path.join(wd, a.tci_glob))) if os.path.basename(f) not in excl]
    intl_files = [f for f in sorted(glob.glob(os.path.join(wd, a.intl_glob))) if os.path.basename(f) not in excl]
    refs = load(os.path.join(wd, "refs.json")) if os.path.exists(os.path.join(wd, "refs.json")) else []
    dropped = load(os.path.join(wd, "refs-dropped.json")) if os.path.exists(os.path.join(wd, "refs-dropped.json")) else []

    out = [f"# บันทึกการค้นเอกสาร (สร้างด้วย make_refs_log.py {today.isoformat()})", "",
           f"จำนวนระเบียนนับจากไฟล์ผลค้นจริง ไม่ใช่ยอดบนหน้าจอฐานข้อมูล วันที่ค้น: {date} (แก้ถ้าค้นหลายวัน) "
           "คำค้นในตารางอนุมานจากชื่อไฟล์ **ต้องตรวจกับคำสั่งที่รันจริง** และเติมเขตข้อมูล/ช่วงปี/ตัวกรองที่ใช้", ""]

    # ---- TCI ----
    tci_ids, tci_total = set(), 0
    tci_by_id = {}
    if tci_files:
        out += ["## TCI", "", "| คำค้น (อนุมานจากชื่อไฟล์) | เขตข้อมูล | ไฟล์ผล | ระเบียน | ใช้ใน refs.json |", "|---|---|---|---|---|"]
    ref_ids = {str(r.get("url", "")).split("=")[-1] for r in refs if r.get("url")} | {str(r.get("id")) for r in refs if r.get("id")}
    for f in tci_files:
        recs = load(f)
        ids = [str(r.get("id") or r.get("url", "").split("=")[-1]) for r in recs]
        used = sum(1 for i in ids if i in ref_ids)
        q, field = query_from_name(f)
        out.append(f"| {q} | {field} | `{os.path.basename(f)}` | {len(recs)} | {used} |")
        tci_total += len(recs)
        for r, i in zip(recs, ids):
            tci_ids.add(i)
            tci_by_id.setdefault(i, []).append(os.path.basename(f))
    if tci_files:
        out += [f"| **รวม** | | | **{tci_total} (ไม่ซ้ำ {len(tci_ids)})** | |", "",
                "คำค้นที่ไม่ได้ระเบียนจึงไม่มีไฟล์ผล: (เติมเอง เพื่อให้ \"ไม่พบ\" มีความหมาย)", ""]

    # ---- international ----
    intl_keys, intl_total, per_source = set(), 0, {}
    if intl_files:
        out += ["## ฐานข้อมูลนานาชาติ", "", "| ประเด็นคำค้น (อนุมานจากชื่อไฟล์) | ไฟล์ผล | ระเบียน | แยกตามฐาน | ใช้ใน refs.json |", "|---|---|---|---|---|"]
    ref_dois = {str(r.get("doi", "")).lower() for r in refs if r.get("doi")}
    ref_titles = {norm_title(r.get("title") or r.get("title_en")) for r in refs}
    for f in intl_files:
        recs = load(f)
        srcs = {}
        used = 0
        for r in recs:
            key = (r.get("doi") or "").lower() or norm_title(r.get("title"))
            intl_keys.add(key)
            srcs[r.get("source", "?")] = srcs.get(r.get("source", "?"), 0) + 1
            if (r.get("doi") or "").lower() in ref_dois or norm_title(r.get("title")) in ref_titles:
                used += 1
        q, _ = query_from_name(f)
        out.append(f"| {q} | `{os.path.basename(f)}` | {len(recs)} | {', '.join(f'{k} {v}' for k, v in sorted(srcs.items()))} | {used} |")
        intl_total += len(recs)
        for k, v in srcs.items():
            per_source[k] = per_source.get(k, 0) + v
    if intl_files:
        out += [f"| **รวม** | | **{intl_total} (ไม่ซ้ำ {len(intl_keys)})** | {', '.join(f'{k} {v}' for k, v in sorted(per_source.items()))} | |", ""]

    # ---- refs.json summary ----
    if refs:
        out += ["## รายการที่ใช้ (refs.json)", ""]
        by_lang = {}
        for r in refs:
            lang = r.get("lang") or ("th" if r.get("authors_th") else "en")
            by_lang.setdefault(lang, {}).setdefault(r.get("read") or "ไม่ระบุ", 0)
            by_lang[lang][r.get("read") or "ไม่ระบุ"] += 1
        for lang, reads in by_lang.items():
            out.append(f"- {lang}: {sum(reads.values())} รายการ ({', '.join(f'{k} {v}' for k, v in reads.items())})")
        not_in_search = []
        for r in refs:
            rid = str(r.get("url", "")).split("=")[-1]
            doi = (r.get("doi") or "").lower()
            if rid in tci_by_id or (doi and doi in {k for k in intl_keys}) or norm_title(r.get("title") or r.get("title_en")) in intl_keys:
                continue
            not_in_search.append(r.get("key_th") or r.get("key_en") or r.get("cite_en") or r.get("title") or r.get("title_en") or "?")
        out += ["", f"แหล่งที่ไม่พบในไฟล์ผลค้นใด (สืบค้นเจาะจง/ตัวบท/คู่มือ/งานต้นฉบับของแนวคิด) {len(not_in_search)} รายการ:", ""]
        out += [f"- {x}" for x in not_in_search]
        out.append("")

    # ---- dropped ----
    if dropped:
        out += ["## รายการที่ตัดออก (refs-dropped.json)", "", "| รายการ | เหตุผล |", "|---|---|"]
        for r in dropped:
            lab = r.get("key_th") or r.get("key_en") or r.get("cite_en") or r.get("title") or r.get("title_en") or "?"
            reason = r.get("drop_reason") or r.get("reason") or r.get("proposed_drop") or "(ไม่ได้บันทึกเหตุผล → เติม `drop_reason`)"
            out.append(f"| {lab} | {reason} |")
        out.append("")

    out += ["## วิธีเขียนย่อหน้าวิธีการจากบันทึกนี้", "",
            "ฐาน + ช่วงปี + จำนวนชุดคำค้น + เขตข้อมูล + จำนวนที่คัดกรองต่อคำค้น → ระเบียนไม่ซ้ำ → ที่คัดเลือก/ที่ใช้ → ที่คัดออกและเหตุ → แหล่งนอกการค้นหลัก "
            "ยอดในย่อหน้าต้องเท่ากับยอดในไฟล์นี้ และคำว่า \"ไม่พบ\" ในบทความหมายถึงไม่พบจากขอบเขตนี้เท่านั้น", ""]

    target = os.path.join(wd, a.out)
    if os.path.exists(target) and not a.force:
        target = os.path.join(wd, os.path.splitext(a.out)[0] + ".generated.md")
        print(f"มี {a.out} อยู่แล้ว เขียนเป็น {os.path.basename(target)} แทน (ใช้ --force เพื่อเขียนทับ)")
    open(target, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print(f"เขียน {target}: TCI {len(tci_files)} ไฟล์ {tci_total} ระเบียน (ไม่ซ้ำ {len(tci_ids)}); นานาชาติ {len(intl_files)} ไฟล์ {intl_total} ระเบียน (ไม่ซ้ำ {len(intl_keys)}); refs {len(refs)}; dropped {len(dropped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
