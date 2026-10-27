"""Step 5. Render header.png (1200x630 social card) with Playwright Chromium.

Fonts: set FONT_DIR to a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf and IBMPlexMono-Regular.ttf
(from github.com/google/fonts); otherwise system serifs are used.
Usage: python3 code/05_header.py
"""
import json
import math
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
U = json.load(open(os.path.join(ROOT, "data", "units_1849.geojson")))
TH = json.load(open(os.path.join(ROOT, "data", "thames.geojson")))["geometry"]
FD = os.environ.get("FONT_DIR", "")
RB, RC = [20, 40, 70, 100, 150], ["#F1F2DC", "#DDE29F", "#B9C24F", "#8C981A", "#56600E", "#22260A"]

lon0, lon1, lat0, lat1 = -0.265, 0.103, 51.405, 51.585
kx = math.cos(math.radians(51.5))
Wm, Hm = 580, 580 * (lat1 - lat0) / ((lon1 - lon0) * kx)


def P(lon, lat):
    return (lon - lon0) / (lon1 - lon0) * Wm, (lat1 - lat) / (lat1 - lat0) * Hm


def ring(cs):
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (P(*c) for c in cs)) + "Z"


paths = []
for f in U["features"]:
    g, r = f["geometry"], f["properties"]["cholera_rate_1849"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    d = " ".join(ring(rg) for poly in polys for rg in poly)
    c = RC[sum(r >= b for b in RB)]
    paths.append(f'<path d="{d}" fill="{c}" stroke="#E7ECEC" stroke-width="1.2" fill-rule="evenodd"/>')
lines = TH["coordinates"] if TH["type"] == "MultiLineString" else [TH["coordinates"]]
thames = "".join(f'<path d="M{"L".join(f"{x:.1f} {y:.1f}" for x, y in (P(*c) for c in ln))}" fill="none" stroke="#2D5F80" stroke-width="3" stroke-opacity=".7"/>' for ln in lines)
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#E7ECEC;color:#16191A;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:64px;top:70px;font:400 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#5C6668;display:flex;gap:12px;align-items:center}}
.k b{{background:#16191A;color:#E7ECEC;padding:7px 9px;font-weight:400}}
h1{{position:absolute;left:60px;top:112px;margin:0;font:900 132px/.86 Fraunces,Georgia,serif;letter-spacing:-.02em;font-variation-settings:'wght' 900,'opsz' 72,'SOFT' 50}}
h1 em{{font-style:normal;color:#7F8C0B;display:block}}
p{{position:absolute;left:64px;top:372px;width:500px;margin:0;font-size:26px;line-height:1.36}}
.f{{position:absolute;left:64px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#5C6668}}
svg{{position:absolute;right:24px;top:{(630 - Hm) / 2:.0f}px}}
.cap{{position:absolute;right:40px;bottom:30px;font:400 13px/1.3 'IBM Plex Mono',monospace;color:#5C6668;text-align:right}}
</style></head><body>
<div class="k"><b>Data study</b><span>Public health × history</span></div>
<h1>Cholera<em>1849</em></h1>
<p>{R['farr']['deaths']:,} deaths in London. Was it the low ground or the water, and does the map still show today?</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Wm}" height="{Hm:.0f}" viewBox="0 0 {Wm} {Hm:.0f}">{''.join(paths)}{thames}</svg>
<div class="cap">Deaths per 10,000, by 1849 district</div>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html")
open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + tmp)
    pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png"))
    b.close()
print("header.png written")
