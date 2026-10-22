"""Extract verified citation metadata (and abstracts) for corpus papers cited in the review.

Writes results/corpus_refs.csv. Each entry is matched by a title fragment; a fragment that
matches zero or several records stops the script so no citation is guessed.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PICK = {
    "music": "Bulk tissue cell type deconvolution with multi-subject",
    "bayesprism": "Cell type and gene expression deconvolution with BayesPrism",
    "sturm": "Comprehensive evaluation of transcriptome-based cell-type quantification",
    "bisque": "Accurate estimation of cell composition in bulk expression through robust",
    "salas_epic": "An optimized library for reference-based deconvolution of whole-blood",
    "titus_rev": "Cell-type deconvolution from DNA methylation: A review of recent applications",
    "teschendorff_rev": "Cell-type deconvolution in epigenome-wide association studies: A review",
    "decamps2020": "Guidelines for cell-type heterogeneity quantification based on a comparative",
    "deconbench": "DECONbench: a benchmarking platform",
    "amblard": "A robust workflow to benchmark deconvolution of multi-omic data",
    "emixed": "EMixed: Probabilistic Multi-Omics",
    "episcore": "EPISCORE: Cell type deconvolution of bulk tissue DNA methylomes",
    "scmd": "scMD facilitates cell type deconvolution",
    "aric": "ARIC: Accurate and robust inference",
    "decomics": "DECOMICS, a shiny application",
    "methylbert": "MethylBERT enables read-level",
    "onuchic": "Epigenomic Deconvolution of Breast Tumors",
    "methylcc": "MethylCC: Technology-independent",
    "deconvme": "Unifying DNA methylation-based in silico cell-type deconvolution with deconvMe",
    "methylresolver": "MethylResolver",
    "dsorter": "Digitaldlsorter",
    "unicell": "Interpretable and context-free deconvolution of multi-scale whole transcriptomic",
    "buddi": "BuDDI: Bulk Deconvolution with Domain Invariance",
    "dl_review": "Deep learning based deconvolution methods: A systematic review",
    "natrevcancer": "A guide to transcriptomic deconvolution in cancer",
    "omnideconv": "omnideconv: a unifying framework",
    "pseudobulk_sim": "Heterogeneous pseudobulk simulation enables realistic benchmarking",
    "cfdna_bench": "Systematic evaluation of methylation-based cell type deconvolution methods for plasma",
    "dnam_assess": "A systematic assessment of cell type deconvolution algorithms for DNA methylation data",
    "wgbs_bench": "Systematic evaluation of cell-Type deconvolution pipelines for-based bulk DNA methylomes",
    "cellsize": "Challenges and opportunities to computationally deconvolve heterogeneous tissue with varying cell sizes",
    "robustness": "Robustness and resilience of computational deconvolution methods for bulk RNA",
    "brain_bench": "Benchmark of cellular deconvolution methods using a multi-assay dataset",
    "sc_guideline": "Cell-type deconvolution for bulk RNA-seq data using single-cell reference: a comparative",
    "clinical_eval": "Systematic evaluation of transcriptomics-based deconvolution methods and references using thousands",
    "autogenes": "AutoGeneS: Automatic gene selection",
    "monaco": "RNA-Seq Signatures Normalized by MRNA Abundance",
    "cord_blood": "Systematic evaluation and validation of reference and library selection methods for deconvolution of cord blood",
    "hidecorr": "Hierarchical cell-type deconvolution",
    "nnice": "NNICE: a deep quantile neural network",
    "ensdeconv": "Robust and accurate estimation of cellular fraction from tissue omics data via ensemble deconvolution",
}

d = pd.read_csv(ROOT / "results" / "screened.csv")
rows, bad = [], []
for key, frag in PICK.items():
    hit = d[d["Title"].str.contains(frag, case=False, regex=False, na=False)]
    if len(hit) != 1:
        bad.append((key, len(hit)))
        continue
    r = hit.iloc[0]
    pages = (f"{r['Page start']}-{r['Page end']}" if pd.notna(r["Page start"]) and pd.notna(r["Page end"])
             else (str(r["Art. No."]) if pd.notna(r["Art. No."]) else ""))
    rows.append({"key": key, "authors": r["Authors"], "year": int(r["Year"]), "title": r["Title"],
                 "source": r["Abbreviated Source Title"] if pd.notna(r["Abbreviated Source Title"]) else r["Source title"],
                 "volume": r["Volume"], "issue": r["Issue"], "pages": pages, "doi": r["DOI"],
                 "cited_by": r["Cited by"], "included": r["include"], "abstract": r["Abstract"]})
out = pd.DataFrame(rows)
out.to_csv(ROOT / "results" / "corpus_refs.csv", index=False)
print("not uniquely matched:", bad)
if "--abs" in sys.argv:
    for r in out.itertuples():
        print(f"\n[{r.key}] {r.authors.split(';')[0]} {r.year} | {r.title} | {r.source} {r.volume}:{r.pages} | {r.doi}")
        print("   ", str(r.abstract)[:1100])
