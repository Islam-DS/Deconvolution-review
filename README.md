# A Bibliometric Review of Cell Type Deconvolution Using RNA and DNA Methylation Data

This repository holds the code, search details and screening decisions behind the review by Md. Mahbubul Islam, Al-Farabi Kazakh National University.

## How to reproduce the analysis

You need Python 3 with pandas, numpy, matplotlib, networkx and openpyxl. For the PDF you need a LaTeX system such as MiKTeX or TeX Live. Run these commands from this folder in order.

```
python -I scripts/screen.py
python -I scripts/bibliometrics.py
python -I scripts/pick_refs.py
python -I scripts/build_refs.py
python -I scripts/audit.py score
```

The manuscript itself will be added to this repository after publication.

The first script screens the Scopus export with written rules. The second produces all figures and bibliometric tables. The third and fourth build the reference list from verified records and stop if any citation cannot be verified. The fifth scores the screening audit. A Scopus export of your own, made with the query in the search log, is needed because the original export cannot be shared.

## What each file contains

| Path | Contents |
| --- | --- |
| data/scopus/SEARCH_LOG.md | The exact Scopus query, search date and record counts |
| results/records_and_decisions.csv | Every record with its identifier, DOI, title, year and screening decision |
| results/summary.json and other tables | Bibliometric results used in the paper |
| results/growth_baseline.md | PubMed queries and counts used as the growth baseline |
| results/audit | Blind audit decisions and the hidden key with the script decisions |
| figures | All figures of the paper |
| scripts | All analysis code |

Scopus abstracts, the raw export and downloaded full texts are not included because of licence terms.

## Helper scripts

The script fetch_fulltext.py downloads open access full texts from Europe PMC, ft_grep.py searches them, verify_refs.py checks every reference against Crossref and arXiv, and style_check.py checks the manuscript text for punctuation.
