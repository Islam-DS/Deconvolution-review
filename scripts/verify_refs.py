"""Final reference check: resolve every DOI on Crossref (and the arXiv id on arXiv) and compare titles.

Prints one line per reference with the title similarity; anything below 0.9 needs a manual look.
"""
import difflib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
refs = (ROOT / "paper" / "refs.tex").read_text(encoding="utf-8")


def norm(t: str) -> str:
    t = re.sub(r"<[^>]+>|\\[a-z]+|[{}`'\"]", " ", t.lower())
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "reference-check/1.0 (mailto:mahbubulislam331@gmail.com)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


bad = 0
for i, (key, body) in enumerate(re.findall(r"\\bibitem\{([^}]+)\}\s*(.+)", refs), 1):
    title = re.search(r"``(.+?),''", body).group(1)
    doi = re.search(r"https://doi\.org/([^}]+)\}", body) or re.search(r"doi: (\S+)\.$", body)
    arx = re.search(r"arXiv:(\d{4}\.\d{4,5})", body)
    try:
        if doi:
            msg = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi.group(1))))["message"]
            found, venue, year = msg["title"][0], (msg.get("container-title") or [""])[0], msg["issued"]["date-parts"][0][0]
        elif arx:
            xml = get(f"http://export.arxiv.org/api/query?id_list={arx.group(1)}").decode()
            found = re.findall(r"<title>(.*?)</title>", xml, flags=re.S)[1]
            venue, year = "arXiv", re.search(r"<published>(\d{4})", xml).group(1)
        else:
            found, venue, year = "", "NO IDENTIFIER", ""
    except Exception as e:  # noqa: BLE001
        found, venue, year = "", f"LOOKUP FAILED {e.__class__.__name__}", ""
    sim = difflib.SequenceMatcher(None, norm(title), norm(found)).ratio()
    flag = "OK " if sim >= 0.9 else "CHECK"
    bad += sim < 0.9
    print(f"[{i:2d}] {flag} {sim:.2f} {key:16s} {year} {venue[:40]}")
    if sim < 0.9:
        print(f"      ours:     {title}\n      registry: {found}")
    time.sleep(0.25)
print(f"\n{bad} reference(s) need a manual look")
