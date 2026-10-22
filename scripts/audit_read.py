"""Show composition-related sentences of chosen audit records (reading aid; does not open the key file)."""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
s = pd.read_excel(ROOT / "results" / "audit" / "audit_sheet.xlsx", sheet_name="records").set_index("audit_id")
PAT = re.compile(r"deconvol|proportion|composition|cell[- ]type|heterogeneit|estimat|adjust|cibersort|xcell|epidish|"
                 r"houseman|minfi|mcp|bulk|infiltrat|abundance|fraction|correct", re.I)
for aid in sys.argv[1:]:
    ab = str(s.loc[aid, "abstract"])
    sents = [x for x in re.split(r"(?<=[.!?])\s+", ab) if PAT.search(x)]
    print(f"{aid} | {s.loc[aid, 'title'][:90]}")
    for x in sents[:4]:
        print("   -", x[:300])
