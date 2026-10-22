"""Build the IEEE-style reference list for paper/review.tex from verified metadata only.

Sources: Scopus export (results/corpus_refs.csv), saved PubMed metadata (data/pubmed/*.json),
and a few hand-entered records verified on Crossref/arXiv/PubMed (MANUAL below).
References are numbered in order of first citation in the .tex file. An unknown key stops the build.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "review.tex"

PMID_KEYS = {
    "25822800": "cibersort", "31061481": "cibersortx", "22568884": "houseman", "28193155": "epidish",
    "29130882": "epic", "31126321": "quantiseq", "27765066": "mcpcounter", "29141660": "xcell",
    "32832661": "scaden", "33159064": "avila2020", "36599988": "loyfer", "28340624": "medecom",
    "24495553": "jaffe", "26956433": "idol", "31278265": "dwls", "24148234": "shenorr",
    "29351586": "avila2018", "33782057": "prisma", "38755121": "deridder", "38762790": "ferro",
    "38751935": "menet", "36347853": "tape", "30498206": "moss",
}
# Verified by hand (PubMed records shown in session; Crossref for Donthu; arXiv abstract page for HADACA3).
MANUAL = {
    "bisque": 'B. Jew \\emph{et al.}, ``Accurate estimation of cell composition in bulk expression through robust integration of single-cell information,\'\' \\emph{Nat. Commun.}, vol. 11, no. 1, Art. no. 1971, 2020, doi: 10.1038/s41467-020-15816-6.',
    "monaco": 'G. Monaco \\emph{et al.}, ``RNA-seq signatures normalized by mRNA abundance allow absolute deconvolution of human immune cell types,\'\' \\emph{Cell Rep.}, vol. 26, no. 6, pp. 1627--1640.e7, 2019, doi: 10.1016/j.celrep.2019.01.041.',
    "reinius": 'L. E. Reinius \\emph{et al.}, ``Differential DNA methylation in purified human blood cells: Implications for cell lineage and studies on disease susceptibility,\'\' \\emph{PLoS One}, vol. 7, no. 7, Art. no. e41361, 2012, doi: 10.1371/journal.pone.0041361.',
    "gong": 'T. Gong and J. D. Szustakowski, ``DeconRNASeq: A statistical framework for deconvolution of heterogeneous tissue samples based on mRNA-Seq data,\'\' \\emph{Bioinformatics}, vol. 29, no. 8, pp. 1083--1085, 2013, doi: 10.1093/bioinformatics/btt090.',
    "donthu": 'N. Donthu, S. Kumar, D. Mukherjee, N. Pandey, and W. M. Lim, ``How to conduct a bibliometric analysis: An overview and guidelines,\'\' \\emph{J. Bus. Res.}, vol. 133, pp. 285--296, 2021, doi: 10.1016/j.jbusres.2021.04.070.',
    "hadaca3": 'H. Barbot \\emph{et al.}, ``On the promises and limits of multi-omics integration for deconvolution: The HADACA3 benchmark,\'\' arXiv:2606.05980 [q-bio.QM], Jun. 2026. \\textbf{[Preprint, not peer-reviewed.]}',
}


def fmt_authors_initials(names: list[tuple[str, str]]) -> str:
    """names: list of (last, initials-without-dots)."""
    def one(last: str, ini: str) -> str:
        ini = " ".join(f"{c}." for c in ini.replace(".", "").replace(" ", "")) if ini else ""
        return f"{ini} {last}".strip()
    if len(names) > 6:
        return one(*names[0]) + " \\emph{et al.}"
    s = [one(*n) for n in names]
    return s[0] if len(s) == 1 else (", ".join(s[:-1]) + (", and " if len(s) > 2 else " and ") + s[-1])


def scopus_names(authors: str) -> list[tuple[str, str]]:
    out = []
    for a in authors.split(";"):
        a = a.strip()
        m = re.match(r"^(.*?)\s+((?:[A-Z][a-z]?\.-?\s?)+)$", a)
        out.append((m.group(1), m.group(2).replace("-", "")) if m else (a, ""))
    return out


def tex_escape(s: str) -> str:
    return (s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
            .replace("–", "--").replace("—", "---").replace("’", "'").replace("ö", '\\"o').replace("ä", '\\"a')
            .replace("é", "\\'e").replace("ü", '\\"u').replace("$\\upsilon$", "$\\upsilon$"))


TITLE_CASE_FIX = {  # sentence case for titles that Scopus or PubMed give in title case
    "EMixed: Probabilistic Multi-Omics Cellular Deconvolution of Bulk Omics Data":
        "EMixed: Probabilistic multi-omics cellular deconvolution of bulk omics data",
    "Epigenomic Deconvolution of Breast Tumors Reveals Metabolic Coupling between Constituent Cell Types":
        "Epigenomic deconvolution of breast tumors reveals metabolic coupling between constituent cell types",
    "in Epigenome-Wide Association Studies": "in epigenome-wide association studies",
}


def sentence_case(title: str) -> str:
    for a, b in TITLE_CASE_FIX.items():
        title = title.replace(a, b)
    # IEEE style used here: capitalise the first word after a colon.
    return re.sub(r":\s+([a-z])", lambda m: ": " + m.group(1).upper(), title)


def entry(authors: str, title: str, journal: str, vol, issue, pages, year, doi) -> str:
    title = tex_escape(sentence_case(str(title).rstrip(".")))
    parts = [f"{authors}, ``{title},'' \\emph{{{tex_escape(journal)}}}"]
    if str(vol) not in ("", "nan", "None"):
        parts.append(f"vol. {vol}")
    if str(issue) not in ("", "nan", "None"):
        parts.append(f"no. {issue}")
    if str(pages) not in ("", "nan", "None"):
        p = str(pages)
        parts.append(f"pp. {p.replace('-', '--')}" if "-" in p else f"Art. no. {p}")
    parts.append(str(year))
    return ", ".join(parts) + f", doi: {str(doi).lower() if str(doi).startswith('10.') else doi}."


def load_all() -> dict[str, str]:
    refs = dict(MANUAL)
    for f in (ROOT / "data" / "pubmed").glob("*.json"):
        for a in json.load(open(f, encoding="utf-8"))["articles"]:
            pmid = a["identifiers"]["pmid"]
            if pmid not in PMID_KEYS:
                continue
            names = [(x["last_name"], x.get("initials", "")) for x in a["authors"] if isinstance(x, dict) and x.get("last_name")]
            c = a.get("citation") or {}
            j = a["journal"]["iso_abbreviation"].replace("Nat ", "Nat. ").replace("Genome Biol", "Genome Biol.") \
                .replace("Brief Bioinform", "Brief. Bioinform.").replace("Curr Opin Immunol", "Curr. Opin. Immunol.") \
                .replace("Sci Adv", "Sci. Adv.").replace("Genome Med", "Genome Med.").replace("Nat. Methods", "Nat. Methods")
            pages = c.get("pages", "")
            if re.fullmatch(r"\d+-\d+", pages or ""):  # expand PubMed short page ranges, e.g. 453-7
                a1, b1 = pages.split("-")
                pages = f"{a1}-{a1[:len(a1) - len(b1)] + b1}"
            refs[PMID_KEYS[pmid]] = entry(fmt_authors_initials(names), a["title"], j, c.get("volume", ""),
                                          c.get("issue", ""), pages, a["publication_date"]["year"], a["doi"])
    for r in pd.read_csv(ROOT / "results" / "corpus_refs.csv").itertuples():
        if r.key in refs:
            continue
        issue = "" if pd.isna(r.issue) else str(r.issue).split(".")[0]
        issue = issue if any(ch.isdigit() for ch in issue) else ""  # Scopus sometimes gives month names
        src = {"Commun. Biolog.": "Commun. Biol."}.get(r.source, r.source)
        refs[r.key] = entry(fmt_authors_initials(scopus_names(r.authors)), r.title, src, r.volume, issue,
                            r.pages, r.year, r.doi)
    return refs


def main() -> None:
    refs = load_all()
    order: list[str] = []
    for grp in re.findall(r"\\cite\{([^}]*)\}", TEX.read_text(encoding="utf-8")):
        for k in (x.strip() for x in grp.split(",")):
            if k not in order:
                order.append(k)
    missing = [k for k in order if k not in refs]
    if missing:
        raise SystemExit(f"Unknown citation keys (not verified): {missing}")
    # PRISMA counts: studies cited in the synthesis, and those found outside the included corpus.
    inc = pd.read_csv(ROOT / "results" / "screened.csv").query("include")
    corpus_dois = set(inc["DOI"].dropna().str.lower())
    method_refs = {"prisma", "donthu"}
    studies = [k for k in order if k not in method_refs]
    doi_of = {k: (re.search(r"doi: (\S+)\.$", refs[k]) or [None, None])[1] for k in studies}
    added = [k for k in studies if (doi_of[k] or "").lower() not in corpus_dois]
    (ROOT / "paper" / "counts.tex").write_text(
        f"\\newcommand{{\\nSynth}}{{{len(studies)}}}\n\\newcommand{{\\nAdded}}{{{len(added)}}}\n", encoding="utf-8")
    print(f"synthesis studies: {len(studies)}; outside corpus: {len(added)} -> {added}")
    body = "\n".join(f"\\bibitem{{{k}}} {refs[k]}" for k in order)
    (ROOT / "paper" / "refs.tex").write_text(
        "% Generated by scripts/build_refs.py -- do not edit by hand.\n"
        f"\\begin{{thebibliography}}{{{len(order)}}}\n{body}\n\\end{{thebibliography}}\n", encoding="utf-8")
    print(f"{len(order)} references written; unused verified entries: {sorted(set(refs) - set(order))}")


if __name__ == "__main__":
    main()
