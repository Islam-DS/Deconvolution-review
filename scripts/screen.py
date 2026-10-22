"""Rule-based screening and classification of the Scopus export.

Every rule is explicit so the screening is reproducible and can be audited.
Output: results/screened.csv with one row per record and its labels.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "scopus" / "scopus_export_2026-10-22.csv"
OUT = ROOT / "results"

# Query phrases: at least one must appear in title, abstract or author keywords
# (records matched only through Scopus-assigned index keywords are excluded).
CORE = re.compile(
    r"deconvol|cell[- ]type (?:proportion|composition|fraction)|"
    r"cellular (?:composition|deconvolution)|cell (?:type )?(?:proportion|fraction)s? estimat"
)
SPATIAL = re.compile(r"spatial(?:ly)? (?:resolved |)transcriptom|\bvisium\b|\bspot[- ]level|spatial omics|\bspots?\b.*deconvol")
BULK = re.compile(r"\bbulk\b|whole[- ]blood|tissue (?:sample|profile)|tumou?r (?:sample|tissue)|methylation array|epic array|450k")
RNA = re.compile(r"rna[- ]seq|transcriptom|gene expression|microarray|scrna|single[- ]cell rna")
DNAM = re.compile(r"methylation|methylom|\bdnam\b|\bcpg\b|epigenom|bisulfite|cfdna")
MULTI = re.compile(r"multi[- ]?omic|multimodal|multi[- ]modal|integrat\w* (?:of )?(?:rna|transcriptom|methylation|omics)")
DL = re.compile(r"deep learning|neural network|autoencoder|transformer|deep[- ]?neural|convolutional|graph neural")
ML = re.compile(r"machine learning|random forest|support vector|gradient boost|xgboost|elastic net")
CANCER = re.compile(r"cancer|tumou?r|carcinoma|oncolog|melanoma|glioma|leukemi|lymphoma|neoplas")
METHOD = re.compile(
    r"\bwe (?:present|propose|develop|developed|introduce|introduced|describe)\b|"
    r"\bnovel (?:method|approach|algorithm|framework|tool)|\bhere,? we (?:present|propose|develop)"
)
BENCH = re.compile(r"benchmark|comparison of|comparative (?:evaluation|analysis)|systematic(?:ally)? (?:evaluat|assess|compar)|evaluation of .*method")
SC_TITLE = re.compile(r"single[- ]cell|single[- ]nucle|scrna|snrna|\batlas\b|cell landscape")
ESTIM = re.compile(r"estimat|infer|bulk|adjust|correct(?:ed|ion|ing) for|heterogeneity|methylation|proportion")
UNCERT = re.compile(r"uncertaint|confidence interval|credible interval|bayesian")


def screen() -> pd.DataFrame:
    """Return the export with screening decisions and topic labels."""
    d = pd.read_csv(SRC, encoding="utf-8-sig")
    n0 = len(d)
    d["dup"] = d.duplicated(subset=["DOI"], keep="first") & d["DOI"].notna()
    low = lambda c: d[c].fillna("").str.lower()  # noqa: E731
    title, abstract, akw = low("Title"), low("Abstract"), low("Author Keywords")
    text = title + " " + abstract + " " + akw

    d["core_hit"] = text.str.contains(CORE)
    d["spatial_only"] = (
        (title + " " + akw).str.contains(SPATIAL) | (abstract.str.contains(SPATIAL) & ~text.str.contains(BULK))
    ) & ~title.str.contains(r"\bbulk\b")  # methods covering both bulk and spatial data stay in
    # Estimation focus: the composition of a bulk profile is estimated or adjusted for,
    # not merely described from single-cell data.
    sc_primary = title.str.contains(SC_TITLE) & ~(title + " " + akw).str.contains(CORE)
    estimation = (title + " " + akw).str.contains(CORE) | abstract.str.contains(r"deconvol") | (
        abstract.str.contains(CORE) & abstract.str.contains(ESTIM)
    )
    d["estimation_focus"] = estimation & ~sc_primary
    d["include"] = ~d["dup"] & d["core_hit"] & ~d["spatial_only"] & d["estimation_focus"]
    d["exclusion_reason"] = ""
    d.loc[d["dup"], "exclusion_reason"] = "duplicate"
    d.loc[~d["dup"] & ~d["core_hit"], "exclusion_reason"] = "query terms only in index keywords"
    d.loc[~d["dup"] & d["core_hit"] & d["spatial_only"], "exclusion_reason"] = "spatial transcriptomics deconvolution"
    d.loc[~d["dup"] & d["core_hit"] & ~d["spatial_only"] & ~d["estimation_focus"], "exclusion_reason"] = (
        "composition only described (e.g. single-cell atlas), not estimated from bulk"
    )

    for name, rx in [("rna", RNA), ("dnam", DNAM), ("multi", MULTI), ("dl", DL), ("ml", ML),
                     ("cancer", CANCER), ("uncert", UNCERT)]:
        d[name] = text.str.contains(rx)
    d["multiomics"] = d["multi"] | (d["rna"] & d["dnam"])
    d["deconv_in_title"] = title.str.contains(CORE)
    d["is_review"] = d["Document Type"].eq("Review")
    d["is_benchmark"] = title.str.contains(BENCH) & d["deconv_in_title"]
    d["is_method"] = d["deconv_in_title"] & abstract.str.contains(METHOD) & ~d["is_benchmark"] & ~d["is_review"]
    d["study_type"] = "application"
    d.loc[d["is_method"], "study_type"] = "method"
    d.loc[d["is_benchmark"], "study_type"] = "benchmark"
    d.loc[d["is_review"], "study_type"] = "review"
    assert len(d) == n0
    return d


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    d = screen()
    d.to_csv(OUT / "screened.csv", index=False)
    inc = d[d["include"]]
    print("records", len(d), "| included", len(inc))
    print(d["exclusion_reason"].value_counts().to_string())
    print(inc["study_type"].value_counts().to_string())
    for c in ["rna", "dnam", "multiomics", "dl", "ml", "cancer", "uncert"]:
        print(c, int(inc[c].sum()))
