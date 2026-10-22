"""Print compact citation lines from a saved PubMed metadata JSON file (verification helper)."""
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
show_abs = len(sys.argv) > 2
for a in d["articles"]:
    au = a.get("authors") or []
    names = [x.get("last_name", "") if isinstance(x, dict) else str(x) for x in au]
    c = a.get("citation") or {}
    j = (a.get("journal") or {}).get("iso_abbreviation", "")
    date = a.get("publication_date")
    year = date.get("year") if isinstance(date, dict) else str(date)[:4]
    pmid = a["identifiers"].get("pmid") if isinstance(a.get("identifiers"), dict) else a.get("identifiers")
    print(f"{pmid} | {', '.join(names[:3])}{' et al.' if len(names) > 3 else ''} | {a['title']} | {j} {year} "
          f"{c.get('volume', '')}({c.get('issue', '')}):{c.get('pages', '')} | doi {a.get('doi')}")
    if show_abs:
        print("   ", (a.get("abstract") or "")[:900].replace("\n", " "))
