"""Search the Thai-Journal Citation Index (search.tci-thailand.org) and print
citation-ready records (authors, year, title, journal, volume, issue, pages, link).

Usage:
  python -I tci_search.py "ภาวะผู้นำ" "พรหมวิหาร" [--field title|keyword|article_abstract]
                          [--op and|or] [--size 10] [--page 1] [--years 2022-2026]
                          [--abstract] [--json out.json]

Each positional argument is one search term; terms are combined with --op.
Run with Python (not curl in Git Bash) so Thai text is sent as UTF-8.
"""
import argparse, html, json, re, sys, urllib.parse, urllib.request

BASE = "https://search.tci-thailand.org/php/search/"
UA = {"User-Agent": "Mozilla/5.0"}
TAG = re.compile(r"<[^>]+>")


def _req(path, data=None, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    body = urllib.parse.urlencode(data, doseq=True).encode() if data is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=UA), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(s):
    return html.unescape(TAG.sub("", s or "")).strip()


def search(terms, field, op, size, page, years):
    data = []
    for t in terms:
        data += [("keyword[]", t), ("criteria[]", field), ("opt[]", op)]
    data += [("perform_advance_search", "true"), ("cur_page", page), ("page_size", size),
             ("year_filter", json.dumps(years) if years else ""), ("country_filter", ""),
             ("get_all_article_id", "false"), ("year_num", 10)]
    return _req("advance_search.php", data=data)


def detail(aid, terms):
    info = _req("search_result.php", params={"get_article_info": "true", "article_id": aid,
                                              "advance_search[]": terms})[0]
    try:
        authors = _req("author_info.php", params={"article_id": aid})
    except Exception:
        authors = []
    try:
        link = _req("link.php", data={"lang": "th", "article_id": aid, "title_eng": info.get("article_eng", ""),
                                     "title_loc": info.get("article_loc", ""), "journal_id": info.get("journal_id", ""),
                                     "journal_eng": info.get("journal_eng", ""), "journal_loc": info.get("journal_loc", ""),
                                     "link": "true"})
        m = re.search(r'href=["\']([^"\']+)', link.get("openArticle", ""))
        url = m.group(1) if m else ""
    except Exception:
        url = ""
    return {
        "id": aid,
        "authors_th": [a.get("name_loc") or a.get("name") or "" for a in authors],
        "authors_en": [a.get("name") or "" for a in authors],
        "year_ce": info.get("year"),
        "title_th": clean(info.get("article_loc")),
        "title_en": clean(info.get("article_eng")),
        "journal_th": clean(info.get("journal_loc")),
        "journal_en": clean(info.get("journal_eng")),
        "volume": info.get("volume"), "issue": info.get("issue_num"), "pages": info.get("page_number"),
        "cited": info.get("cited"),
        "abstract": clean(info.get("abstract_loc") or info.get("abstract_eng")),
        "url": url if url.startswith("http") or not url else "https://search.tci-thailand.org/" + url.lstrip("/"),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("terms", nargs="+")
    p.add_argument("--field", default="title")
    p.add_argument("--op", default="and")
    p.add_argument("--size", type=int, default=10)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--years", help="e.g. 2022-2026")
    p.add_argument("--abstract", action="store_true", help="print abstracts")
    p.add_argument("--json", help="also write records to this JSON file")
    a = p.parse_args()
    years = []
    if a.years:
        lo, hi = (int(x) for x in a.years.split("-"))
        years = [str(y) for y in range(hi, lo - 1, -1)]
    res = search(a.terms, a.field, a.op, a.size, a.page, years)
    ids = res.get("article_ids") or []
    print(f"total_hits={res.get('total_item')} showing={len(ids)} page={a.page}\n")
    recs = []
    for i, aid in enumerate(ids, 1):
        r = detail(aid, a.terms)
        recs.append(r)
        print(f"[{i}] {', '.join(r['authors_th'])} ({r['year_ce']}, พ.ศ. {int(r['year_ce']) + 543 if r['year_ce'] else '?'})")
        print(f"    TH: {r['title_th']}")
        print(f"    EN: {r['title_en']}")
        print(f"    {r['journal_th'] or r['journal_en']} | ปีที่ {r['volume']} ฉบับที่ {r['issue']} | หน้า {r['pages']} | cited {r['cited']}")
        print(f"    {r['url']}")
        if a.abstract and r["abstract"]:
            print(f"    บทคัดย่อ: {r['abstract'][:600]}")
        print()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(recs, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
