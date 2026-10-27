"""Step 4. Build index.html from code/page_template.html.

Every number in the text is a placeholder like {{farr.deaths|int}} filled from data/results.json, and the
compact page data (work/site.json from step 3, plus the parts of results.json the charts need) is embedded
as `const D = ...`, so the page is a single file.
Formats: int, f1, f2, pct0, pct1, ord (1st, 2nd...), ordrev (rank counted from the bottom), raw.
It also fills code/README_template.md to make README.md.
Usage: python3 code/04_build_site.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
site = json.load(open(os.path.join(ROOT, "work", "site.json"), encoding="utf-8"))
WORDS = "zeroth first second third fourth fifth sixth seventh eighth ninth tenth".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def ordinal(n):
    if n < len(WORDS):
        return WORDS[n]
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "ord": return ordinal(int(v))
    if f == "ordrev":
        k = R["long"]["n_units"] - int(v) + 1
        return "lowest" if k == 1 else ordinal(k) + " lowest"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


def fill(text):
    return re.sub(r"\{\{(.+?)\}\}", sub, text)


if __name__ == "__main__":
    t = fill(open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read())
    site["R"] = {k: R[k] for k in ["farr", "water", "south", "broad", "national", "long"]}
    t = t.replace("/*DATA*/", "const D = " + json.dumps(site, separators=(",", ":"), ensure_ascii=False) + ";")
    assert "{{" not in t
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
    print("index.html", len(t.encode()) // 1024, "KB")
    md = fill(open(os.path.join(ROOT, "code", "README_template.md"), encoding="utf-8").read())
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(md)
    print("README.md written")
