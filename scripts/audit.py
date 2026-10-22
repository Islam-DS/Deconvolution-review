"""Blind screening audit.

make:  draw a random sample of 60 included and 40 excluded records and write
       results/audit/audit_sheet.xlsx (no script decisions shown) plus a hidden key file.
score: read the filled sheet, compare each reader with the script, and with each other,
       and write paper/audit.tex with the numbers used in the manuscript.

Readers enter I (include) or E (exclude) in reader1 and, optionally, reader2.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "results" / "audit"
SHEET, KEY = AUD / "audit_sheet.xlsx", AUD / "audit_key.csv"
CRITERIA = ("Include if the record estimates cell type proportions from bulk RNA or DNA methylation data, or adjusts "
            "a bulk analysis for estimated composition. Exclude spatial transcriptomics without bulk data, single cell "
            "studies that only describe composition, and records unrelated to cell composition.")


def make() -> None:
    AUD.mkdir(parents=True, exist_ok=True)
    if SHEET.exists():
        sys.exit("audit_sheet.xlsx already exists; delete it first to draw a new sample.")
    d = pd.read_csv(ROOT / "results" / "screened.csv")
    inc = d[d["include"]].sample(60, random_state=2026)
    exc = d[~d["include"] & (d["exclusion_reason"] != "duplicate")].sample(40, random_state=2026)
    s = pd.concat([inc, exc]).sample(frac=1, random_state=7).reset_index(drop=True)
    s["audit_id"] = [f"A{i + 1:03d}" for i in range(len(s))]
    s[["audit_id", "EID", "include"]].rename(columns={"include": "script_include"}).to_csv(KEY, index=False)
    sheet = pd.DataFrame({"audit_id": s["audit_id"], "title": s["Title"], "year": s["Year"],
                          "author_keywords": s["Author Keywords"].fillna(""), "abstract": s["Abstract"].fillna(""),
                          "reader1 (I/E)": "", "reader1 note": "", "reader2 (I/E)": "", "reader2 note": ""})
    with pd.ExcelWriter(SHEET) as xw:
        sheet.to_excel(xw, sheet_name="records", index=False)
        pd.DataFrame({"criteria": [CRITERIA]}).to_excel(xw, sheet_name="criteria", index=False)
    print(f"wrote {SHEET} ({len(sheet)} records); key kept in {KEY.name}")


def kappa(a: pd.Series, b: pd.Series) -> float:
    po = (a == b).mean()
    pe = (a.mean() * b.mean()) + ((1 - a.mean()) * (1 - b.mean()))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def score() -> None:
    s = pd.read_excel(SHEET, sheet_name="records").merge(pd.read_csv(KEY), on="audit_id")
    r1 = s["reader1 (I/E)"].astype(str).str.strip().str.upper()
    lines = []
    assistant = AUD / "assistant_decisions.csv"
    if not r1.isin(["I", "E"]).all() and assistant.exists():
        # No human reader yet: report the AI assistant's blind check as such (auditDone = 2).
        a = s.merge(pd.read_csv(assistant), on="audit_id")
        h = a["assistant"].str.strip().str.upper().eq("I")
        sc = a["script_include"].astype(bool)
        prec = (h & sc).sum() / sc.sum() * 100
        npv = (~h & ~sc).sum() / (~sc).sum() * 100
        k = kappa(h.astype(int), sc.astype(int))
        lines += [r"\newcommand{\auditDone}{2}", f"\\newcommand{{\\auditPrec}}{{{prec:.0f}}}",
                  f"\\newcommand{{\\auditNPV}}{{{npv:.0f}}}", f"\\newcommand{{\\auditKappa}}{{{k:.2f}}}",
                  r"\newcommand{\auditTwo}{0}"]
        print(f"assistant vs script: inclusion precision {prec:.0f}%, exclusion agreement {npv:.0f}%, kappa {k:.2f}")
        disagree = a.loc[h != sc, ["audit_id", "assistant", "script_include", "note"]]
        disagree.to_csv(AUD / "disagreements.csv", index=False)
        print(f"{len(disagree)} disagreements written to disagreements.csv")
    elif not r1.isin(["I", "E"]).all():
        print("reader1 column incomplete: manuscript keeps the PENDING marker.")
        lines.append(r"\newcommand{\auditDone}{0}")
    else:
        h = r1.eq("I")
        sc = s["script_include"].astype(bool)
        prec = (h & sc).sum() / sc.sum() * 100
        npv = (~h & ~sc).sum() / (~sc).sum() * 100
        k = kappa(h.astype(int), sc.astype(int))
        lines += [r"\newcommand{\auditDone}{1}", f"\\newcommand{{\\auditPrec}}{{{prec:.0f}}}",
                  f"\\newcommand{{\\auditNPV}}{{{npv:.0f}}}", f"\\newcommand{{\\auditKappa}}{{{k:.2f}}}"]
        print(f"reader1 vs script: inclusion precision {prec:.0f}%, exclusion agreement {npv:.0f}%, kappa {k:.2f}")
        r2 = s["reader2 (I/E)"].astype(str).str.strip().str.upper()
        if r2.isin(["I", "E"]).all():
            k12 = kappa(h.astype(int), r2.eq("I").astype(int))
            lines += [r"\newcommand{\auditTwo}{1}", f"\\newcommand{{\\auditKappaReaders}}{{{k12:.2f}}}"]
            print(f"reader1 vs reader2: kappa {k12:.2f}")
        else:
            lines.append(r"\newcommand{\auditTwo}{0}")
    (ROOT / "paper" / "audit.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    {"make": make, "score": score}[sys.argv[1]]()
