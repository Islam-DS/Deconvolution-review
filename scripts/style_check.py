"""Scan the manuscript body for punctuation the author wants to avoid.

The verbatim Scopus query is skipped because it must stay exact. Reference titles are not checked,
because published titles must be quoted as they are.
"""
import re
from pathlib import Path

s = (Path(__file__).resolve().parents[1] / "paper" / "review.tex").read_text(encoding="utf-8")
body = s.split(r"\maketitle")[1].split(r"\input{refs}")[0]
body = body[:body.find("2009 to 2026:")] + body[body.find("A broader first query"):]  # drop the query
body = re.sub(r"\\begin\{(tikzpicture|equation)\}.*?\\end\{\1\}", "", body, flags=re.S)
body = re.sub(r"\\(begin|end)\{[a-z*]+\}(\{[^}]*\})*|\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", body)  # LaTeX commands

checks = [("em or en dash", r"\u2014|\u2013|--"), ("asterisk", r"\*"), ("parenthesis", r"\((?!Fig)"),
          ("quotation mark", r"``|''|\"|\u201c|\u201d"), ("semicolon", ";"), ("colon", r"(?<!tab)(?<!fig)(?<!https):(?!\d)"),
          ("e.g. or i.e.", r"e\.g\.|i\.e\.")]
for name, pat in checks:
    hits = [m.start() for m in re.finditer(pat, body)]
    print(f"{name}: {len(hits)}", [body[max(0, h - 35):h + 20].replace("\n", " ") for h in hits[:6]])
print("hyphenated words:", sorted(set(re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", body))))
print("approx words:", len(body.split()))
