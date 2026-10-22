"""Print sentences from a saved full text that match a regex (helper for reading full texts)."""
import re
import sys
from pathlib import Path

key, pattern = sys.argv[1], sys.argv[2]
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 8
t = (Path(__file__).resolve().parents[1] / "data" / "fulltext" / f"{key}.txt").read_text(encoding="utf-8")
t = re.sub(r"\s+", " ", t)
sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", t)
hits = [s for s in sents if re.search(pattern, s, flags=re.I)]
seen = set()
for s in hits:
    if s in seen:
        continue
    seen.add(s)
    print("-", s[:420])
    if len(seen) >= limit:
        break
