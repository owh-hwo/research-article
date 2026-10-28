#!/usr/bin/env python3
"""Generate the reference list(s) for draft.md from refs.json.

Usage:
  python -I make_reflist.py refs.json --style th-apa [--out references.md]
  python -I make_reflist.py refs.json --style en-apa [--out-en references_en.md] [--out-th references_th.md]
                           [--access-date "October 27, 2026" --access-date-th "27 ตุลาคม 2569"] [--write-keys]

Styles
  th-apa  Thai-journal APA: Thai works first (all authors, "และ" before the last), then English works
          (APA 7, "&"), each sorted alphabetically. One file (default references.md).
  en-apa  Journals that want every reference in English: Thai works are written from their English
          metadata with "[in Thai]" and sorted together with English works (references_en.md); a second
          Thai-script list for checking (references_th.md).

refs.json fields used (first that exists):
  lang, type (journal|book|report|web|law|code), authors|authors_en / authors_th, year_ce|year / year_be,
  title|title_en / title_th, journal|journal_en / journal_th, volume, issue, pages|pages_or_article|article,
  publisher|publisher_en / publisher_th, url, url2, doi, series, date_en / date_th (law: gazette date),
  gazette_en / gazette_th (law: "Royal Gazette, 143(Part 12A), 1-5"), title_italic (web/report default yes)

--write-keys fills key_th ("ชื่อ นามสกุล และคณะ, ปี") and cite_en ("Surname et al., year"; corporate
authors use their full name, or cite_en_override when set) back into refs.json so check_claims.py
and check_citations.py can match in-text citations. Nothing else in refs.json is touched.
"""
import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

THAI = re.compile(r"[฀-๿]")


try:
    from pythainlp.util import collate as _collate
except Exception:  # noqa: BLE001
    _collate = None

CORPORATE = re.compile(r"\b(The|Department|Ministry|University|Organisation|Organization|Institute|Bank|Council|Association|Office|Bureau|Agency|Committee|Commission|Company|Co\.|Ltd|Inc|Press|Group|Authority|Board|Foundation|Centre|Center|Society|Union|Fund|PBS|BBC|OECD|WHO|IMF)\b")


def thai_key(s):
    s = re.sub(r"[่-๋]", "", s)  # tone marks are secondary; vowels keep dictionary order (consonants sort first)
    if s and s[0] in "เแโใไ" and len(s) > 1:
        s = s[1] + s[0] + s[2:]
    return s


def sort_thai(items):
    """Thai-script entries in dictionary order (pythainlp collate when available); Latin-leading entries after them."""
    th = [x for x in items if THAI.search(x[0][:1])]
    la = [x for x in items if not THAI.search(x[0][:1])]
    if _collate and th:
        order = {k: i for i, k in enumerate(_collate([x[0] for x in th]))}
        th.sort(key=lambda x: order[x[0]])
    else:
        th.sort(key=lambda x: thai_key(x[0]))
    return th + sorted(la, key=lambda x: x[0].lower())


def is_corporate(name):
    return "," not in name and (len(name.split()) > 3 or bool(CORPORATE.search(name)) or any(w.isupper() and len(w) > 1 for w in name.split()))


def strip_year(date, year):
    """'June 16, 2026' -> 'June 16'; '16 มิถุนายน 2569' -> '16 มิถุนายน' (the year is already printed before the date)."""
    d = str(date).strip()
    d = re.sub(r",?\s*" + re.escape(str(year)) + r"\s*$", "", d)
    return re.sub(r",?\s*\d{4}\s*$", "", d).strip()


def g(r, *keys, default=""):
    for k in keys:
        v = r.get(k)
        if v not in (None, "", []):
            return v
    return default


def apa_name(full):
    full = full.strip()
    if "," in full or is_corporate(full):  # already "Surname, I." or a corporate author
        return full
    parts = full.split()
    if len(parts) == 1:
        return parts[0]
    sur = parts[-1]
    return f"{sur[0].upper()}{sur[1:]}, " + " ".join(p[0].upper() + "." for p in parts[:-1])


def join_en(names):
    names = [apa_name(n) for n in names]
    if len(names) == 1:
        s = names[0]
    elif len(names) <= 20:
        s = ", ".join(names[:-1]) + ", & " + names[-1]
    else:
        s = ", ".join(names[:19]) + ", ... " + names[-1]
    return s if s.endswith(".") else s + "."  # APA 7: a period closes the author element (group authors too)


def join_th(names):
    names = [n.strip() for n in names]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " และ" + names[-1]


def cite_en(r, names, year):
    if r.get("cite_en_override"):
        return r["cite_en_override"]
    if len(names) == 1 and is_corporate(names[0]):
        return f"{names[0]}, {year}"
    sur = [apa_name(n).split(",")[0] for n in names]
    if len(sur) == 1:
        return f"{sur[0]}, {year}"
    if len(sur) == 2:
        return f"{sur[0]} & {sur[1]}, {year}"
    return f"{sur[0]} et al., {year}"


def key_th(names, year_be):
    names = [n.strip() for n in names]
    if len(names) == 1:
        return f"{names[0]}, {year_be}"
    if len(names) == 2:
        return f"{names[0]} และ{names[1]}, {year_be}"
    return f"{names[0]} และคณะ, {year_be}"


def vol_issue_pages(r):
    vol, iss = str(g(r, "volume")), str(g(r, "issue")).split(" (")[0]
    pages = str(g(r, "pages", "pages_or_article")).split(" (")[0]
    if g(r, "article"):
        pages = f"Article {r['article']}"
    if not vol and not iss:
        return ""  # caller prints "Advance online publication."
    s = f"*{vol}*" if vol else ""
    if iss:
        s += f"({iss})"
    if pages:
        s = (s + ", " if s else "") + pages
    return s


def doi_or_url(r, allow_url=True):
    """DOI as https://doi.org/…; otherwise the URL for web/report sources, or for a journal article only when
    refs.json sets "url_in_ref": true (a database record link is not a reference URL)."""
    if g(r, "doi"):
        d = str(r["doi"])
        return " " + (d if d.startswith("http") else f"https://doi.org/{d}")
    if (allow_url or r.get("url_in_ref")) and g(r, "url"):
        return f" {r['url']}"
    return ""


def sentence_case(t):
    t = t.strip()
    return t.capitalize() if t.isupper() else t


def en_entry(r, is_thai_work, access_en):
    """English-script entry (APA 7). Thai works get [in Thai] after the title."""
    typ = g(r, "type", default="journal")
    y = g(r, "year_ce", "year")
    tag = " [in Thai]" if is_thai_work else ""
    names = g(r, "authors_en", "authors", default=[])
    title = g(r, "title_en", "title")
    if typ == "law":
        gz = str(g(r, "gazette_en"))
        head, tail = (gz.split(".", 1) + [""])[:2] if "." in gz else (gz, "")
        date = f", {strip_year(r['date_en'], y)}" if g(r, "date_en") else ""
        return title, f"{title}{tag}. ({y}{date}). *{head}*.{tail}" + ("" if tail.endswith(".") or not tail else ".")
    if typ == "code":
        pub = g(r, "publisher_en", "publisher") or (names[0] if names else "")
        urls = " and ".join(u for u in (g(r, "url"), g(r, "url2")) if u)
        acc = f" Retrieved {access_en}, from {urls}" if access_en and urls else (f" {urls}" if urls else "")
        return title, f"{title}{tag}. ({y}).{' ' + pub + '.' if pub else ''}{acc}"
    if typ == "journal":
        jn = g(r, "journal_en", "journal")
        vip = vol_issue_pages(r)
        loc = f"*{jn}*, {vip}." if vip else f"*{jn}*. Advance online publication."
        return join_en(names), f"{join_en(names)} ({y}). {sentence_case(title)}{tag}. {loc}{doi_or_url(r, allow_url=False)}"
    if typ == "book":
        pub = g(r, "publisher_en", "publisher", "journal")
        return join_en(names), f"{join_en(names)} ({y}). *{title}*{tag}. {pub}.{doi_or_url(r, allow_url=False)}"
    if typ == "report":
        pub = g(r, "publisher_en", "publisher", "journal")
        series = f" ({r['series']})" if g(r, "series") else ""
        pub_s = "" if not pub or pub in names else f" {pub}."
        return join_en(names), f"{join_en(names)} ({y}). *{title}*{series}{tag}.{pub_s}{doi_or_url(r)}"
    # web / news
    date = f", {strip_year(r['date_en'], y)}" if g(r, "date_en") else ""
    t = f"*{title}*" if r.get("title_italic", True) else title
    pub = g(r, "publisher_en", "publisher")
    pub_s = "" if not pub or pub in names else f" {pub}."
    return join_en(names), f"{join_en(names)} ({y}{date}). {t}{tag}.{pub_s} {g(r, 'url')}".rstrip()


def th_entry(r, access_th):
    typ = g(r, "type", default="journal")
    y = g(r, "year_be", default=(int(g(r, "year_ce", "year", default=0)) + 543 if g(r, "year_ce", "year") else ""))
    names = g(r, "authors_th", "authors", default=[])
    title = g(r, "title_th", "title")
    if typ == "law":
        gz = str(g(r, "gazette_th"))
        head, tail = (gz.split(".", 1) + [""])[:2] if "." in gz else (gz, "")
        date = f", {strip_year(r['date_th'], y)}" if g(r, "date_th") else ""
        return title, f"{title}. ({y}{date}). *{head}*.{tail}" + ("" if tail.endswith(".") or not tail else ".")
    if typ == "code":
        pub = g(r, "publisher_th", "publisher") or (names[0] if names else "")
        urls = " และ ".join(u for u in (g(r, "url"), g(r, "url2")) if u)
        acc = f" สืบค้นเมื่อ {access_th} จาก {urls}" if access_th and urls else (f" {urls}" if urls else "")
        return title, f"{title}. ({y}).{' ' + pub + '.' if pub else ''}{acc}"
    if typ == "journal":
        jn = g(r, "journal_th", "journal")
        vip = vol_issue_pages(r)
        loc = f"*{jn}*, {vip}." if vip else f"*{jn}*. Advance online publication."
        return join_th(names), f"{join_th(names)}. ({y}). {title}. {loc}{doi_or_url(r, allow_url=False)}"
    if typ == "book":
        pub = g(r, "publisher_th", "publisher")
        return join_th(names), f"{join_th(names)}. ({y}). *{title}*. {pub}."
    if typ == "report":
        pub = g(r, "publisher_th", "publisher")
        pub_s = "" if not pub or pub in names else f" {pub}."
        return join_th(names), f"{join_th(names)}. ({y}). *{title}*.{pub_s}{doi_or_url(r)}"
    date = f", {strip_year(r['date_th'], y)}" if g(r, "date_th") else ""
    t = f"*{title}*" if r.get("title_italic", True) else title
    return join_th(names), f"{join_th(names)}. ({y}{date}). {t}. {g(r, 'url')}".rstrip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs")
    ap.add_argument("--style", choices=["th-apa", "en-apa"], required=True)
    ap.add_argument("--out", default="references.md")
    ap.add_argument("--out-en", default="references_en.md")
    ap.add_argument("--out-th", default="references_th.md")
    ap.add_argument("--access-date", default="", help='en-apa: "Retrieved <date>, from" for web/code sources')
    ap.add_argument("--access-date-th", default="")
    ap.add_argument("--write-keys", action="store_true", help="write key_th / cite_en back into refs.json")
    a = ap.parse_args()
    refs = json.load(open(a.refs, encoding="utf-8"))
    th_items, en_items = [], []
    for r in refs:
        is_th = (g(r, "lang") == "th") or (not g(r, "lang") and bool(g(r, "authors_th") or THAI.search(str(g(r, "title_th", "title")))))
        y_ce, y_be = g(r, "year_ce", "year"), g(r, "year_be")
        if a.write_keys:
            if is_th and g(r, "authors_th"):
                r["key_th"] = key_th(r["authors_th"], y_be or y_ce)
            names_en = g(r, "authors_en", "authors", default=[])
            if names_en:
                r["cite_en"] = cite_en(r, names_en, y_ce)
        if a.style == "th-apa":
            if is_th:
                th_items.append(th_entry(r, a.access_date_th))
            else:
                en_items.append(en_entry(r, False, a.access_date))
        else:
            en_items.append(en_entry(r, is_th, a.access_date))
            if is_th:
                th_items.append(th_entry(r, a.access_date_th))
    en_items.sort(key=lambda x: x[0].lower())
    th_items = sort_thai(th_items)
    fix = lambda s: s.replace("ํา", "ำ")  # noqa: E731  (decomposed sara am from some databases)
    if a.style == "th-apa":
        open(a.out, "w", encoding="utf-8", newline="\n").write("\n\n".join(fix(s) for _, s in th_items + en_items) + "\n")
        print(f"{a.out}: ไทย {len(th_items)} อังกฤษ {len(en_items)}")
    else:
        open(a.out_en, "w", encoding="utf-8", newline="\n").write("\n\n".join(s for _, s in en_items) + "\n")
        open(a.out_th, "w", encoding="utf-8", newline="\n").write("\n\n".join(fix(s) for _, s in th_items) + "\n")
        print(f"{a.out_en}: {len(en_items)} รายการ; {a.out_th}: {len(th_items)} รายการ")
    if a.write_keys:
        json.dump(refs, open(a.refs, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("เขียน key_th / cite_en ลง refs.json แล้ว")
    return 0


if __name__ == "__main__":
    sys.exit(main())
