"""Scan candidate article topics for literature volume, trend and research gap.

For each candidate it reports:
  - TCI hits where ALL Thai terms appear in the title, and in the abstract
  - TCI hits in the last 3 years vs the 3 years before (trend)
  - TCI hits for each single term (are there enough sources to cite, i.e. >= 10?)
  - OpenAlex hit count for the English query (international interest), optional
  - a rough verdict: gap / suitable / saturated / thin literature
  - with --examples N: the N most recent title matches (to spot near-duplicates)

Usage (one --topic per candidate; fields separated by "|"):
  python -I topic_scan.py \
    --topic "ผู้นำดิจิทัลตามพรหมวิหาร|ภาวะผู้นำดิจิทัล,พรหมวิหาร|digital leadership Brahmavihara" \
    --topic "AI กับธรรมาภิบาลท้องถิ่น|ปัญญาประดิษฐ์,ธรรมาภิบาล,ท้องถิ่น|artificial intelligence local governance" \
    [--examples 3] [--no-intl] [--json out.json]
  label | Thai terms joined by commas (AND) | English query (optional)
"""
import argparse, datetime, json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tci_search  # noqa: E402
from academic_search import get  # noqa: E402

THIS_YEAR = datetime.date.today().year


def tci_counts(terms, field):
    r = tci_search.search(terms, field, "and", 1, 1, [])
    total = int(r.get("total_item") or 0)
    years = {int(y): int(c or 0) for y, c in (r.get("year_articles") or {}).items()}
    recent = sum(years.get(y, 0) for y in range(THIS_YEAR - 2, THIS_YEAR + 1))
    before = sum(years.get(y, 0) for y in range(THIS_YEAR - 5, THIS_YEAR - 2))
    return total, recent, before


def tci_examples(terms, n):
    r = tci_search.search(terms, "title", "and", n, 1, [])
    out = []
    for aid in r.get("article_ids") or []:
        d = tci_search.detail(aid, terms)
        out.append(f"{', '.join(d['authors_th'][:2])} ({int(d['year_ce']) + 543 if d['year_ce'] else '?'}) {d['title_th'] or d['title_en']} — {d['journal_th'] or d['journal_en']}")
    return out


def openalex_count(query):
    p = {"search": query, "per-page": 1, "filter": f"publication_year:{THIS_YEAR - 5}-{THIS_YEAR}"}
    if os.environ.get("OPENALEX_API_KEY"):
        p["api_key"] = os.environ["OPENALEX_API_KEY"]
    return get("https://api.openalex.org/works?" + urllib.parse.urlencode(p))["meta"]["count"]


def verdict(title_hits, abstract_hits, singles):
    enough = sum(min(c, 10) for c in singles.values()) >= 10 and max(singles.values() or [0]) >= 5
    if not enough:
        return "วรรณกรรมบาง — เสี่ยงหาอ้างอิงไม่ครบ 10 ต้องขยายคำค้น/ใช้ฐานนานาชาติ"
    if title_hits == 0 and abstract_hits <= 3:
        return "ช่องว่างสูง — ยังแทบไม่มีใครทำตรง ๆ (ตรวจว่าไม่ใช่เพราะคำค้นแคบเกิน)"
    if title_hits <= 10:
        return "เหมาะสม — มีฐานงานเดิมให้อ้าง แต่ยังไม่อิ่มตัว"
    if title_hits <= 30:
        return "ค่อนข้างมาก — ต้องหามุม/บริบท/วิธีใหม่ให้ชัด"
    return "อิ่มตัว — มีงานตรงหัวข้อจำนวนมาก ควรเปลี่ยนมุมหรือบริบท"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--topic", action="append", required=True)
    p.add_argument("--examples", type=int, default=0)
    p.add_argument("--no-intl", action="store_true", help="skip OpenAlex count")
    p.add_argument("--json")
    a = p.parse_args()
    results = []
    for raw in a.topic:
        parts = [x.strip() for x in raw.split("|")]
        label, terms = parts[0], [t.strip() for t in parts[1].split(",") if t.strip()]
        en = parts[2] if len(parts) > 2 else ""
        title_hits, recent, before = tci_counts(terms, "title")
        abstract_hits, *_ = tci_counts(terms, "article_abstract")
        singles = {t: tci_counts([t], "title")[0] for t in terms}
        intl = None
        if en and not a.no_intl:
            try:
                intl = openalex_count(en)
            except Exception as e:
                intl = f"error: {e}"
        trend = "เพิ่มขึ้น" if recent > before else "ลดลง" if recent < before else "คงที่"
        res = {"label": label, "terms": terms, "en_query": en, "tci_title": title_hits, "tci_abstract": abstract_hits,
               "tci_recent3y": recent, "tci_prev3y": before, "trend": trend, "tci_single_terms": singles,
               "openalex_5y": intl, "verdict": verdict(title_hits, abstract_hits, singles)}
        if a.examples:
            res["examples"] = tci_examples(terms, a.examples)
        results.append(res)

        print(f"■ {label}")
        print(f"  TCI ชื่อเรื่องมีทุกคำ: {title_hits} | ในบทคัดย่อ: {abstract_hits} | 3 ปีล่าสุด {recent} vs 3 ปีก่อนหน้า {before} ({trend})")
        print("  แยกคำ (ชื่อเรื่อง): " + ", ".join(f"{t} {c}" for t, c in singles.items()))
        if en:
            print(f"  OpenAlex 5 ปี \"{en}\": {intl if intl is not None else 'ข้าม'}")
        print(f"  ประเมิน: {res['verdict']}")
        for ex in res.get("examples", []):
            print(f"    - {ex}")
        print()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
