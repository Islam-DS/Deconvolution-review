# Scopus search log

| Item | Value |
| --- | --- |
| Database | Scopus, through the KazNU institutional login |
| Search date | 22 October 2026, export at 10:47:59 UTC |
| Records found and exported | 1,465 and 1,465 |
| Export format | CSV with all field groups and cited references |
| Working copy | scopus_export_2026-10-22.csv, an unchanged copy of the export |

## Final query

```
TITLE-ABS-KEY ( ( "cell type deconvolution" OR "cell-type deconvolution" OR "cellular deconvolution" OR "computational deconvolution" OR "bulk deconvolution" OR "deconvolution of bulk" OR "reference-based deconvolution" OR "reference-free deconvolution" OR "methylation deconvolution" OR "cell type proportion*" OR "cell-type proportion*" OR "cell type composition" OR "cell-type composition" OR "cell type fraction*" OR "cell-type fraction*" ) AND ( "RNA-seq" OR "transcriptom*" OR "gene expression" OR "DNA methylation" OR "methylom*" OR "multi-omics" OR "multiomics" ) ) AND PUBYEAR > 2008 AND PUBYEAR < 2027 AND ( LIMIT-TO ( DOCTYPE , "ar" ) OR LIMIT-TO ( DOCTYPE , "re" ) OR LIMIT-TO ( DOCTYPE , "cp" ) ) AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

## Earlier query

The first version used the broad term deconvolution together with bulk, tissue, tumour or cancer terms and the same omics terms and limits. It returned 4,643 records, mostly studies that only applied existing tools, so it was narrowed to the final query.

## Profile of the export

The export holds 1,369 articles, 62 reviews and 34 conference papers published from 2010 to 2026. The year 2026 is partial and ends on 22 October. One record is a duplicate. Abstracts are present for all records, cited references for 99%, author keywords for 67% and index keywords for 93%.

Screening removed spatial transcriptomics studies, single cell atlases that only describe composition, and records matched only through index keywords. Foundational papers such as CIBERSORT, the Houseman method and EpiDISH are not records themselves because their abstracts do not use the search phrases. They are heavily cited within the corpus and were added through citation searching.
