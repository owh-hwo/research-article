"""Search public scholarly databases and print citation-ready records.

Sources (free public APIs, no login):
  openalex   OpenAlex       - all disciplines, ~250M works, citation counts
  crossref   Crossref       - DOI registry, authoritative bibliographic metadata
  semantic   Semantic Scholar - all disciplines, citation counts (rate-limited without key)
  doaj       DOAJ           - peer-reviewed open-access journals only
  europepmc  Europe PMC     - health, life and behavioural sciences (incl. PubMed)
  eric       ERIC           - education research (US Dept. of Education), peer-review flag
  arxiv      arXiv          - preprints (CS, AI, economics, stats) - NOT peer reviewed
  core       CORE           - open-access full texts from repositories (needs CORE_API_KEY)

Usage:
  python -I academic_search.py "Buddhist leadership" --sources openalex,crossref,doaj --size 5
                               [--years 2020-2026] [--abstract] [--json out.json]
  python -I academic_search.py --doi 10.1234/abcd          # verify one DOI via Crossref

Optional environment variables: OPENALEX_API_KEY, OPENALEX_MAILTO, SEMANTIC_SCHOLAR_API_KEY,
CORE_API_KEY, CONTACT_EMAIL (sent as mailto in the User-Agent for polite API use).
Query in English for international databases; Thai queries work best in tci_search.py.
"""
import argparse, html, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

CONTACT = os.environ.get("CONTACT_EMAIL", "")
UA = {"User-Agent": "research-article-skill/1.0" + (f" (mailto:{CONTACT})" if CONTACT else "")}
TAG = re.compile(r"<[^>]+>")
DEFAULT = "openalex,crossref,doaj"


def get(url, headers=None, raw=False, tries=3):
    h = dict(UA, **(headers or {}))
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
                body = r.read()
            return body if raw else json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < tries - 1:
                time.sleep(2 * (i + 1)); continue
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if i < tries - 1:
                time.sleep(2 * (i + 1)); continue
            raise


def clean(s):
    return html.unescape(TAG.sub("", s or "")).strip()


def rec(source, **kw):
    r = {"source": source, "authors": [], "year": None, "title": "", "venue": "", "volume": "",
         "issue": "", "pages": "", "doi": "", "url": "", "cited": None, "peer_reviewed": None, "abstract": ""}
    r.update({k: v for k, v in kw.items() if v not in (None, "")})
    r["doi"] = re.sub(r"^https?://(dx\.)?doi\.org/", "", str(r["doi"]).strip())
    return r


def in_years(y, years):
    return not years or (y and years[0] <= int(y) <= years[1])


# --- sources -------------------------------------------------------------------
def openalex(q, n, years):
    p = {"search": q, "per-page": n}
    if years:
        p["filter"] = f"publication_year:{years[0]}-{years[1]}"
    if os.environ.get("OPENALEX_API_KEY"):
        p["api_key"] = os.environ["OPENALEX_API_KEY"]
    if os.environ.get("OPENALEX_MAILTO") or CONTACT:
        p["mailto"] = os.environ.get("OPENALEX_MAILTO") or CONTACT
    out = []
    for w in get("https://api.openalex.org/works?" + urllib.parse.urlencode(p)).get("results", []):
        b, loc = w.get("biblio") or {}, (w.get("primary_location") or {})
        src = loc.get("source") or {}
        inv = w.get("abstract_inverted_index") or {}
        abstract = " ".join(t for t, _ in sorted(((t, i) for t, ps in inv.items() for i in ps), key=lambda x: x[1]))
        pages = "-".join(x for x in (b.get("first_page"), b.get("last_page")) if x)
        out.append(rec("openalex", authors=[a["author"]["display_name"] for a in w.get("authorships", [])],
                       year=w.get("publication_year"), title=w.get("display_name") or "", venue=src.get("display_name"),
                       volume=b.get("volume"), issue=b.get("issue"), pages=pages,
                       doi=(w.get("doi") or "").replace("https://doi.org/", ""), url=loc.get("landing_page_url") or w.get("id"),
                       cited=w.get("cited_by_count"), abstract=abstract,
                       peer_reviewed=None if w.get("type") != "article" else ("journal" == src.get("type") or None)))
    return out


def crossref(q, n, years):
    p = {"query.bibliographic": q, "rows": n, "select": "DOI,title,author,issued,container-title,volume,issue,page,is-referenced-by-count,type,URL,abstract"}
    if years:
        p["filter"] = f"from-pub-date:{years[0]},until-pub-date:{years[1]}"
    if CONTACT:
        p["mailto"] = CONTACT
    return [_crossref_item(it) for it in get("https://api.crossref.org/works?" + urllib.parse.urlencode(p))["message"]["items"]]


def _crossref_item(it):
    year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    authors = [" ".join(x for x in (a.get("family"), a.get("given")) if x).replace(" ", ", ", 1) if a.get("family") else a.get("name", "")
               for a in it.get("author", [])]
    return rec("crossref", authors=authors, year=year, title=clean((it.get("title") or [""])[0]),
               venue=clean((it.get("container-title") or [""])[0]), volume=it.get("volume"), issue=it.get("issue"),
               pages=it.get("page"), doi=it.get("DOI"), url=it.get("URL"), cited=it.get("is-referenced-by-count"),
               abstract=clean(it.get("abstract")), peer_reviewed=True if it.get("type") == "journal-article" else None)


def semantic(q, n, years):
    p = {"query": q, "limit": n, "fields": "title,year,authors,venue,journal,externalIds,citationCount,url,abstract,publicationTypes"}
    if years:
        p["year"] = f"{years[0]}-{years[1]}"
    h = {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.environ.get("SEMANTIC_SCHOLAR_API_KEY") else {}
    out = []
    for w in get("https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(p), h, tries=4).get("data", []):
        j = w.get("journal") or {}
        out.append(rec("semantic", authors=[a["name"] for a in w.get("authors", [])], year=w.get("year"),
                       title=w.get("title"), venue=j.get("name") or w.get("venue"), volume=j.get("volume"),
                       pages=(j.get("pages") or "").strip(), doi=(w.get("externalIds") or {}).get("DOI"), url=w.get("url"),
                       cited=w.get("citationCount"), abstract=w.get("abstract"),
                       peer_reviewed=True if "JournalArticle" in (w.get("publicationTypes") or []) else None))
    return out


def doaj(q, n, years):
    query = q + (f" AND bibjson.year:[{years[0]} TO {years[1]}]" if years else "")
    out = []
    for r in get(f"https://doaj.org/api/search/articles/{urllib.parse.quote(query)}?pageSize={n}").get("results", []):
        b = r.get("bibjson", {})
        j = b.get("journal", {})
        doi = next((i.get("id") for i in b.get("identifier", []) if i.get("type", "").lower() == "doi"), "")
        url = next((l.get("url") for l in b.get("link", []) if l.get("url")), "")
        pages = "-".join(x for x in (b.get("start_page"), b.get("end_page")) if x)
        out.append(rec("doaj", authors=[a.get("name", "") for a in b.get("author", [])], year=b.get("year"),
                       title=b.get("title"), venue=j.get("title"), volume=j.get("volume"), issue=j.get("number"),
                       pages=pages, doi=doi, url=url, abstract=b.get("abstract"), peer_reviewed=True))
    return out


def europepmc(q, n, years):
    query = q + (f" AND PUB_YEAR:[{years[0]} TO {years[1]}]" if years else "")
    p = {"query": query, "format": "json", "pageSize": n, "resultType": "core"}
    out = []
    for w in get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(p))["resultList"]["result"]:
        ji = w.get("journalInfo") or {}
        out.append(rec("europepmc", authors=[x.strip() for x in (w.get("authorString") or "").rstrip(".").split(",") if x.strip()],
                       year=w.get("pubYear"), title=clean(w.get("title")), venue=(ji.get("journal") or {}).get("title") or w.get("journalTitle"),
                       volume=ji.get("volume") or w.get("journalVolume"), issue=ji.get("issue") or w.get("issue"),
                       pages=w.get("pageInfo"), doi=w.get("doi"), cited=w.get("citedByCount"),
                       url=f"https://europepmc.org/article/{w.get('source')}/{w.get('id')}", abstract=clean(w.get("abstractText")),
                       peer_reviewed=False if w.get("source") == "PPR" else True))
    return out


def eric(q, n, years):
    s = q + (f" publicationdateyear:[{years[0]} TO {years[1]}]" if years else "")
    p = {"search": s, "rows": n, "format": "json",
         "fields": "id,title,author,publicationdateyear,source,description,peerreviewed,url,publicationtype"}
    out = []
    for d in get("https://api.ies.ed.gov/eric/?" + urllib.parse.urlencode(p))["response"]["docs"]:
        out.append(rec("eric", authors=d.get("author", []), year=d.get("publicationdateyear"), title=d.get("title"),
                       venue=d.get("source"), url=d.get("url") or f"https://eric.ed.gov/?id={d.get('id')}",
                       abstract=d.get("description"), peer_reviewed=d.get("peerreviewed") == "T"))
    return out


def arxiv(q, n, years):
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    p = {"search_query": "all:" + q, "max_results": n * (3 if years else 1), "sortBy": "relevance"}
    root = ET.fromstring(get("https://export.arxiv.org/api/query?" + urllib.parse.urlencode(p), raw=True))
    out = []
    for e in root.findall("a:entry", ns):
        y = (e.findtext("a:published", "", ns) or "")[:4]
        if not in_years(y, years):
            continue
        doi = e.findtext("x:doi", "", ns)
        out.append(rec("arxiv", authors=[a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)], year=y,
                       title=" ".join(e.findtext("a:title", "", ns).split()), venue=e.findtext("x:journal_ref", "", ns) or "arXiv preprint",
                       doi=doi, url=e.findtext("a:id", "", ns), abstract=" ".join(e.findtext("a:summary", "", ns).split()),
                       peer_reviewed=bool(e.findtext("x:journal_ref", "", ns)) or False))
    return out[:n]


def core(q, n, years):
    key = os.environ.get("CORE_API_KEY")
    if not key:
        raise RuntimeError("ต้องตั้ง CORE_API_KEY (ขอฟรีที่ https://core.ac.uk/services/api)")
    query = q + (f" AND yearPublished>={years[0]} AND yearPublished<={years[1]}" if years else "")
    p = {"q": query, "limit": n}
    out = []
    for w in get("https://api.core.ac.uk/v3/search/works?" + urllib.parse.urlencode(p), {"Authorization": f"Bearer {key}"}).get("results", []):
        out.append(rec("core", authors=[a.get("name", "") for a in w.get("authors", [])], year=w.get("yearPublished"),
                       title=w.get("title"), venue=(w.get("journals") or [{}])[0].get("title", "") if w.get("journals") else w.get("publisher"),
                       doi=w.get("doi"), url=(w.get("links") or [{}])[0].get("url") if w.get("links") else w.get("downloadUrl"),
                       cited=w.get("citationCount"), abstract=w.get("abstract")))
    return out


SOURCES = {"openalex": openalex, "crossref": crossref, "semantic": semantic, "doaj": doaj,
           "europepmc": europepmc, "eric": eric, "arxiv": arxiv, "core": core}


def doi_lookup(doi):
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip())
    return _crossref_item(get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"])


def show(i, r, with_abstract):
    pr = {True: "peer-reviewed", False: "NOT peer-reviewed", None: "?"}[r["peer_reviewed"]]
    print(f"[{i}] ({r['source']}) {'; '.join(r['authors'][:6])}{' et al.' if len(r['authors']) > 6 else ''} ({r['year']})")
    print(f"    {r['title']}")
    vi = f"{r['volume']}" + (f"({r['issue']})" if r["issue"] else "")
    print(f"    {r['venue']} {vi} {r['pages']} | cited {r['cited'] if r['cited'] is not None else '?'} | {pr}")
    print(f"    {'https://doi.org/' + r['doi'] if r['doi'] else r['url']}")
    if with_abstract and r["abstract"]:
        print(f"    Abstract: {r['abstract'][:600]}")
    print()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("query", nargs="?")
    p.add_argument("--sources", default=DEFAULT, help=f"comma list from {','.join(SOURCES)} or 'all' (default {DEFAULT})")
    p.add_argument("--size", type=int, default=5, help="results per source")
    p.add_argument("--years", help="e.g. 2020-2026")
    p.add_argument("--abstract", action="store_true")
    p.add_argument("--json", help="write all records to this JSON file")
    p.add_argument("--doi", help="look up one DOI on Crossref (verification)")
    a = p.parse_args()

    if a.doi:
        show(1, doi_lookup(a.doi), True)
        return
    if not a.query:
        p.error("query or --doi required")
    years = tuple(int(x) for x in a.years.split("-")) if a.years else None
    names = list(SOURCES) if a.sources == "all" else [s.strip() for s in a.sources.split(",") if s.strip()]
    if a.sources == "all" and not os.environ.get("CORE_API_KEY"):
        names.remove("core")
    records, seen = [], set()
    for name in names:
        if name not in SOURCES:
            print(f"!! unknown source {name}"); continue
        try:
            got = SOURCES[name](a.query, a.size, years)
        except Exception as e:
            hint = " (จำกัดจำนวนครั้ง: รอสักครู่หรือตั้ง SEMANTIC_SCHOLAR_API_KEY)" if name == "semantic" and "429" in str(e) else ""
            print(f"!! {name}: {e}{hint}\n"); continue
        print(f"=== {name}: {len(got)} รายการ ===\n")
        for r in got:
            k = (r["doi"] or "").lower() or re.sub(r"\W+", "", r["title"].lower())[:80]
            if k in seen:
                continue
            seen.add(k)
            records.append(r)
            show(len(records), r, a.abstract)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
