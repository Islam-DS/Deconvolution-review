"""Bibliometric analysis of the screened Scopus corpus.

Produces figures (figures/*.pdf, *.png) and tables/numbers (results/*.csv, results/summary.json)
used in the review. Run after screen.py.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES, FIG = ROOT / "results", ROOT / "figures"
FIG.mkdir(exist_ok=True)

# Validated categorical slots 1-3 (dataviz reference palette, light mode).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
})

KW_MAP = {
    r"^(cell[- ]type |cellular |computational |bulk |cell )?deconvolution( analysis| method[s]?)?$": "deconvolution",
    r"^(dna methylation|methylation|dnam|dna-methylation)$": "DNA methylation",
    r"^(bulk )?rna[- ]?seq(uencing)?$|^bulk rna[- ]seq(uencing)?$": "RNA sequencing",
    r"^(single[- ]cell rna[- ]?seq(uencing)?|scrna[- ]?seq|single[- ]cell rna sequencing|single[- ]cell sequencing|single[- ]cell)$": "single cell RNA sequencing",
    r"^(epigenome[- ]wide association stud(y|ies)|ewas)$": "EWAS",
    r"^(tumou?r microenvironment|tme|tumou?r immune microenvironment)$": "tumour microenvironment",
    r"^(cell[- ]type (proportion|composition|fraction)s?|cellular (composition|heterogeneity)|cell composition|cell[- ]type heterogeneity)$": "cell type composition",
    r"^(transcriptom(e|ics)|gene expression profiling)$": "transcriptomics",
    r"^(epigenetic (age|aging|ageing|clock|clocks)|dna methylation age|biological age)$": "epigenetic clocks",
    r"^(immune (cell )?infiltration|tumou?r[- ]infiltrating (immune cells|lymphocytes))$": "immune infiltration",
    r"^cibersort(x)?$": "CIBERSORT(x)",
    r"^(machine learning)$": "machine learning",
    r"^(deep learning|neural network[s]?|deep neural network[s]?)$": "deep learning",
    r"^(epigenetics|epigenetic)$": "epigenetics",
    r"^(multi[- ]?omics|multiomics|multi-omics integration|integrative analysis)$": "multiomics",
    r"^(cell[- ]free dna|cfdna)$": "cell free DNA",
    r"^(prognosis|prognostic (model|signature|biomarker)|survival)$": "prognosis",
    r"^(immunotherapy|immune checkpoint inhibitors?)$": "immunotherapy",
    r"^(biomarker[s]?)$": "biomarker",
    r"^(bioinformatics|computational biology)$": "bioinformatics",
}
COUNTRY_FIX = {"United States": "USA", "United Kingdom": "UK", "Russian Federation": "Russia",
               "South Korea": "S. Korea", "Netherlands": "Netherlands"}


def norm_kw(k: str) -> str:
    k = k.strip().lower().replace("’", "'")
    for rx, lab in KW_MAP.items():
        if re.match(rx, k):
            return lab
    return k


def countries(aff: str) -> set[str]:
    out = set()
    for a in str(aff).split(";"):
        c = a.strip().split(",")[-1].strip()
        if c and c.lower() != "nan" and len(c) < 40:
            out.add(COUNTRY_FIX.get(c, c))
    return out


def split_refs(s: str) -> list[str]:
    return [r.strip() for r in re.split(r"(?<=\(\d{4}\));\s*", str(s)) if r.strip()]


def ref_key(r: str) -> str | None:
    # Scopus format: "Auth A.; Auth B., Title, Source, vol, pp, (YYYY)"; author names contain no commas.
    y = re.search(r"\((\d{4})\)\s*$", r)
    parts = r.split(", ")
    if not y or len(parts) < 3:
        return None
    first = parts[0].split(";")[0].strip().split(" ")[0]
    title = re.sub(r"[^a-z0-9 ]", "", parts[1].lower())[:60]
    return f"{first} ({y.group(1)}) {title}"


def main() -> None:
    d = pd.read_csv(RES / "screened.csv")
    inc = d[d["include"]].copy()
    S: dict = {}

    # ---------- PRISMA numbers
    S["prisma"] = {"identified": int(len(d)), **{k: int(v) for k, v in d["exclusion_reason"].fillna("included").value_counts().items()}}

    # ---------- annual output by modality
    inc["modality"] = np.select(
        [inc["multiomics"], inc["dnam"], inc["rna"]], ["Both", "DNA methylation", "RNA"], "Unclassified")
    yr = inc.groupby(["Year", "modality"]).size().unstack(fill_value=0).reindex(range(2010, 2027), fill_value=0)
    yr.to_csv(RES / "annual_by_modality.csv")
    tot = yr.sum(axis=1)
    S["annual_total"] = {int(k): int(v) for k, v in tot.items()}
    S["cagr_2015_2025"] = round(((tot[2025] / tot[2015]) ** (1 / 10) - 1) * 100, 1)
    S["share_since_2021"] = round(tot.loc[2021:].sum() / tot.sum() * 100, 1)
    S["modality_counts"] = {k: int(v) for k, v in inc["modality"].value_counts().items()}

    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    bottom = np.zeros(len(yr))
    for lab, col in [("RNA", ORANGE), ("DNA methylation", BLUE), ("Both", AQUA), ("Unclassified", "#b9b8b2")]:
        if lab in yr:
            ax.bar(yr.index, yr[lab], bottom=bottom, color=col, label=lab, width=0.8, edgecolor="white", linewidth=0.6)
            bottom += yr[lab].values
    ax.set_xlabel("Publication year"); ax.set_ylabel("Records")
    ax.set_xticks(range(2010, 2027, 4))
    h, l = ax.get_legend_handles_labels()
    ax.legend(h[::-1], l[::-1], loc="upper left", fontsize=7)  # same order as the stack, top to bottom
    fig.savefig(FIG / "fig_annual.pdf"); fig.savefig(FIG / "fig_annual.png"); plt.close(fig)

    # ---------- method-type trends (share of records per period)
    per = pd.cut(inc["Year"], [2009, 2018, 2022, 2026], labels=["2010-2018", "2019-2022", "2023-2026"])
    trend = pd.DataFrame({
        "records": inc.groupby(per, observed=False).size(),
        "deep_learning": inc[inc["dl"]].groupby(per[inc["dl"]], observed=False).size(),
        "multi_omics": inc[inc["multiomics"]].groupby(per[inc["multiomics"]], observed=False).size(),
        "uncertainty": inc[inc["uncert"]].groupby(per[inc["uncert"]], observed=False).size(),
        "methods": inc[inc["study_type"] == "method"].groupby(per[inc["study_type"] == "method"], observed=False).size(),
        "benchmarks": inc[inc["study_type"] == "benchmark"].groupby(per[inc["study_type"] == "benchmark"], observed=False).size(),
    })
    trend.to_csv(RES / "period_trends.csv")
    S["period_trends"] = {str(k): {c: int(v) for c, v in r.items()} for k, r in trend.iterrows()}
    S["study_types"] = {k: int(v) for k, v in inc["study_type"].value_counts().items()}
    S["cancer_records"] = int(inc["cancer"].sum())

    # ---------- methods by modality and approach (the gap table)
    meth = inc[inc["study_type"].isin(["method", "benchmark"])]
    gap = pd.crosstab(meth["modality"], meth["dl"].map({True: "deep learning", False: "other"}))
    gap.to_csv(RES / "methods_modality_dl.csv")
    S["methods_by_modality"] = {k: int(v) for k, v in meth["modality"].value_counts().items()}
    mo_meth = inc[inc["multiomics"] & inc["study_type"].isin(["method", "benchmark"])]
    mo_meth[["Year", "Title", "Source title", "DOI", "Cited by"]].sort_values("Year").to_csv(RES / "multiomics_methods.csv", index=False)

    # ---------- sources, countries, authors
    src = inc["Source title"].value_counts().head(10)
    src.to_csv(RES / "top_sources.csv")
    S["n_sources"] = int(inc["Source title"].nunique())
    cs = inc["Affiliations"].map(countries)
    cc = Counter(c for s in cs for c in s)
    S["n_countries"] = len(cc)
    S["intl_collab_pct"] = round((cs.map(len) > 1).mean() * 100, 1)
    top_c = pd.Series(dict(cc.most_common(12)))
    top_c.to_csv(RES / "top_countries.csv")
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    ax.barh(top_c.index[::-1], top_c.values[::-1], color=BLUE, height=0.65)
    for y, v in enumerate(top_c.values[::-1]):
        ax.text(v + 4, y, str(v), va="center", fontsize=6.5, color=MUTED)
    ax.set_xlabel("Records with at least one author affiliation"); ax.grid(axis="y", visible=False)
    fig.savefig(FIG / "fig_countries.pdf"); fig.savefig(FIG / "fig_countries.png"); plt.close(fig)

    auth = Counter(a.strip() for s in inc["Author full names"].dropna() for a in s.split(";"))
    pd.Series(dict(auth.most_common(15))).to_csv(RES / "top_authors.csv")
    S["mean_authors_per_doc"] = round(inc["Authors"].fillna("").map(lambda s: len(s.split(";"))).mean(), 1)

    # ---------- most cited records
    inc.sort_values("Cited by", ascending=False)[["Year", "Cited by", "Title", "Source title", "DOI", "study_type"]] \
        .head(25).to_csv(RES / "most_cited_records.csv", index=False)

    # ---------- local citation analysis (references cited by included records)
    lc = Counter()
    for r in inc["References"].dropna():
        lc.update({k for k in map(ref_key, split_refs(r)) if k})
    pd.Series(dict(lc.most_common(40)), name="local_citations").to_csv(RES / "top_local_references.csv")
    S["n_cited_references"] = len(lc)

    # ---------- keyword co-occurrence network
    kws = inc["Author Keywords"].dropna().map(lambda s: sorted({norm_kw(k) for k in s.split(";") if k.strip()}))
    kc = Counter(k for ks in kws for k in ks)
    pd.Series(dict(kc.most_common(40))).to_csv(RES / "top_keywords.csv")
    top = [k for k, _ in kc.most_common(24)]
    G = nx.Graph()
    for k in top:
        G.add_node(k, n=kc[k])
    for ks in kws:
        for a, b in combinations([k for k in ks if k in top], 2):
            G.add_edge(a, b, w=G.get_edge_data(a, b, {"w": 0})["w"] + 1)
    G.remove_edges_from([(a, b) for a, b, w in G.edges(data="w") if w < 2])
    comms = nx.community.greedy_modularity_communities(G, weight="w", resolution=1.0)
    S["keyword_clusters"] = [sorted(c, key=lambda k: -kc[k]) for c in comms]
    # How separate are the RNA and methylation clusters? Share of co-occurrence weight between them,
    # and share of records whose keywords touch both clusters.
    meth_c = next(c for c in comms if "DNA methylation" in c)
    rna_c = next(c for c in comms if "deconvolution" in c)
    w_all = sum(w for *_, w in G.edges(data="w"))
    w_between = sum(w for a, b, w in G.edges(data="w") if (a in meth_c and b in rna_c) or (a in rna_c and b in meth_c))
    both = kws.map(lambda ks: bool(set(ks) & meth_c) and bool(set(ks) & rna_c))
    either = kws.map(lambda ks: bool(set(ks) & (meth_c | rna_c)))
    S["cluster_separation"] = {"between_weight_pct": round(100 * w_between / w_all, 1),
                               "records_with_keywords": int(len(kws)),
                               "records_touching_either": int(either.sum()),
                               "records_touching_both": int(both.sum()),
                               "pct_both_of_either": round(100 * both.sum() / either.sum(), 1)}
    pal = [BLUE, ORANGE, AQUA, "#eda100", "#6250d6", "#e87ba4"]
    # Same colour meaning as the growth chart: methylation cluster blue, RNA cluster orange, others aqua.
    def cluster_colour(c: frozenset) -> str:
        return BLUE if "DNA methylation" in c else ORANGE if "deconvolution" in c else AQUA
    col = {k: cluster_colour(c) for c in comms for k in c}
    # Circular layout grouped by cluster: labels sit radially outside the ring and never overlap.
    order = [k for c in comms for k in sorted(c, key=lambda k: -kc[k])]
    ang = {k: 2 * np.pi * i / len(order) + np.pi / 2 for i, k in enumerate(order)}
    pos = {k: (np.cos(a), np.sin(a)) for k, a in ang.items()}
    fig, ax = plt.subplots(figsize=(3.4, 3.4))
    ws = np.array([w for *_, w in G.edges(data="w")])
    for (a, b, w) in G.edges(data="w"):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(
            arrowstyle="-", color=col[a] if col[a] == col[b] else "#bdbcb6", lw=0.2 + 2.2 * w / ws.max(),
            alpha=0.55, connectionstyle="arc3,rad=0.15"))
    for k in order:
        x, y = pos[k]
        ax.scatter(x, y, s=12 + 2.2 * kc[k], color=col[k], edgecolor="white", linewidth=0.7, zorder=3)
        deg = np.degrees(ang[k]) % 360
        flip = 90 < deg < 270
        r = 1.1 + 0.0013 * kc[k]  # clear the bubble, which grows with frequency
        ax.text(r * x, r * y, k.replace("alzheimer", "Alzheimer").replace("EWAS", "EWAS"), rotation=deg - 180 if flip else deg, rotation_mode="anchor",
                ha="right" if flip else "left", va="center", fontsize=8.0, color=INK)
    ax.set_xlim(-2.2, 2.2); ax.set_ylim(-2.2, 2.2); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(FIG / "fig_keywords.pdf"); fig.savefig(FIG / "fig_keywords.png"); plt.close(fig)

    # ---------- keyword evolution by period
    kp = {}
    for p in ["2010-2018", "2019-2022", "2023-2026"]:
        ks = kws[per.loc[kws.index] == p]
        kp[p] = [f"{k} ({n})" for k, n in Counter(k for x in ks for k in x).most_common(12)]
    S["keywords_by_period"] = kp

    (RES / "summary.json").write_text(json.dumps(S, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(S, indent=1, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    main()
