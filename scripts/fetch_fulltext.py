"""Download open-access full texts (Europe PMC XML) of the central papers and save plain text.

Output: data/fulltext/<key>.txt. Papers without an open-access PMC version are reported, not guessed.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fulltext"
OUT.mkdir(parents=True, exist_ok=True)

DOIS = {
    "amblard": "10.1186/s13059-025-03897-9", "deconbench": "10.1186/s12859-021-04381-4",
    "onuchic": "10.1016/j.celrep.2016.10.057", "episcore": "10.1186/s13059-020-02126-9",
    "deridder": "10.1038/s41467-024-48466-z", "avila2020": "10.1038/s41467-020-19015-1",
    "sturm": "10.1093/bioinformatics/btz363", "pseudobulk_sim": "10.1186/s13059-024-03292-w",
    "brain_bench": "10.1186/s13059-025-03552-3", "sc_guideline": "10.1093/bib/bbaf031",
    "cfdna_bench": "10.1186/s13059-024-03456-8", "ensdeconv": "10.1093/bioinformatics/btac279",
    "emixed": "10.6339/25-jds1170", "ferro": "10.1093/bib/bbae234", "dl_review": "10.1016/j.csbj.2025.05.038",
    "avila2018": "10.1093/bioinformatics/bty019", "natrevcancer": "10.1038/s41568-025-00886-9",
    "teschendorff_rev": "10.2217/epi-2016-0153", "titus_rev": "10.1093/hmg/ddx275",
}
API = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "review-fulltext-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def to_text(xml: str) -> str:
    xml = re.sub(r"<ref-list.*?</ref-list>", " ", xml, flags=re.S)  # drop bibliography
    xml = re.sub(r"<(title|p|sec|caption|td|th|tr)[^>]*>", "\n", xml)
    t = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"[ \t]+", " ", t)


keys = sys.argv[1:] or list(DOIS)
for k in keys:
    q = urllib.parse.quote(f'DOI:"{DOIS[k]}"')
    res = json.loads(get(f"{API}/search?query={q}&format=json&resultType=core"))["resultList"]["result"]
    pmcid = next((r.get("pmcid") for r in res if r.get("pmcid") and r.get("isOpenAccess") == "Y"), None) \
        or next((r.get("pmcid") for r in res if r.get("pmcid")), None)
    if not pmcid:
        print(f"{k}: no PMC full text")
        continue
    try:
        xml = get(f"{API}/{pmcid}/fullTextXML").decode("utf-8", "replace")
        (OUT / f"{k}.txt").write_text(to_text(xml), encoding="utf-8")
        print(f"{k}: {pmcid} saved ({len(xml) // 1000} kB)")
    except Exception as e:  # noqa: BLE001
        print(f"{k}: {pmcid} full text not available ({e.__class__.__name__})")
    time.sleep(0.4)
