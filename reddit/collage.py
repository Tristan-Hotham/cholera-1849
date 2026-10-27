"""r/dataisbeautiful collage for Cholera 1849, styled after a Victorian statistical plate.
Every number comes from ../data/results.json and the data files. Run from reddit/: python3 collage.py
Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono); defaults to the scratchpad fonts folder.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE = "#E2E9EA", "#141718", "#56615F", "#B9C5C6"
ACC, ACCD = "#A9B813", "#6E7A00"    # sickly yellow-green, and a darker ink of it for text
WATER = "#7E9AA6"
SHADES = ["#F2F4E3", "#DCE39A", "#BCC84A", "#97A41A", "#5C660C", "#1E220A"]
RB = [20, 40, 70, 100, 150]
KX = math.cos(math.radians(51.5))

R = json.load(open(os.path.join(D, "results.json")))
F = pd.read_csv(os.path.join(D, "farr_1849_districts.csv"))
U = json.load(open(os.path.join(D, "units_1849.geojson")))
TH = json.load(open(os.path.join(D, "thames.geojson")))["geometry"]
UT = pd.read_csv(os.path.join(D, "units_then_now.csv"))
DE = pd.read_csv(os.path.join(D, "snow_1854_deaths_distances.csv"))
PU = pd.read_csv(os.path.join(D, "snow_1854_pumps.csv"))
ST = json.load(open(os.path.join(D, "snow_1854_streets.geojson")))["features"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# plate frame: double rule
for inset, lw in [(0.018, 2.2), (0.024, 0.8)]:
    fig.add_artist(Rectangle((inset, inset * 0.8), 1 - 2 * inset, 1 - 2 * inset * 0.8, transform=fig.transFigure, fill=False, ec=FG, lw=lw))

fig.text(0.05, 0.962, "PLATE I.  THE CHOLERA OF 1849 IN THE DISTRICTS OF LONDON", family=MONO, fontsize=11, color=MUT, va="top")
fig.text(0.05, 0.945, "The hill, or the water?", fontproperties=DISP, fontsize=52, color=FG, va="top")
fig.text(0.05, 0.882, f"In 1849 cholera killed {R['farr']['deaths']:,} people in London's 38 districts. William Farr blamed the low,\n"
                      "damp ground by the Thames. John Snow blamed the water. Their own figures, rebuilt.",
         family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.4)

# ---------- hero map
ax = fig.add_axes([0.035, 0.41, 0.6, 0.43])
for ft in U["features"]:
    g, r = ft["geometry"], ft["properties"]["cholera_rate_1849"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    c = SHADES[sum(r >= b for b in RB)]
    for poly in polys:
        xy = np.array(poly[0]); xy[:, 0] *= KX
        ax.add_patch(MPoly(xy, closed=True, fc=c, ec=BG, lw=1.1))
lines = TH["coordinates"] if TH["type"] == "MultiLineString" else [TH["coordinates"]]
for ln in lines:
    a = np.array(ln); a = a[a[:, 0] < 0.06]
    if len(a) > 1:
        ax.plot(a[:, 0] * KX, a[:, 1], color=BG, lw=6, solid_capstyle="round")
        ax.plot(a[:, 0] * KX, a[:, 1], color=WATER, lw=2.6, solid_capstyle="round")
lab = {"Rotherhithe": (0.012, 0.012), "Hampstead": (0, 0), "Wandsworth": (0, 0), "Lewisham": (0, 0), "Paddington": (0, 0), "Bethnal Green": (0, 0.004), "Lambeth": (0, -0.004)}
for ft in U["features"]:
    p = ft["properties"]
    if p["unit"] in lab:
        g = ft["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        xy = np.array(max(polys, key=lambda q: len(q[0]))[0])
        cx, cy = xy[:, 0].mean() * KX + lab[p["unit"]][0], xy[:, 1].mean() + lab[p["unit"]][1]
        ax.text(cx, cy, f"{p['unit'].upper()}\n{p['cholera_rate_1849']:.0f}", ha="center", va="center", family=MONO, fontsize=10.5, color=FG,
                linespacing=1.15, path_effects=[pe.withStroke(linewidth=3.2, foreground="white")])
ax.set_xlim(-0.27 * KX, 0.105 * KX); ax.set_ylim(51.40, 51.59); ax.set_aspect("equal"); ax.axis("off")
# legend
lx = fig.add_axes([0.06, 0.395, 0.56, 0.03]); lx.axis("off"); lx.set_xlim(0, 6); lx.set_ylim(0, 1)
labs = ["under 20", "20 to 39", "40 to 69", "70 to 99", "100 to 149", "150 +"]
for i, (c, t) in enumerate(zip(SHADES, labs)):
    lx.add_patch(Rectangle((i, .45), .95, .5, fc=c, ec=FG, lw=.6))
    lx.text(i + .475, .1, t, ha="center", va="center", family=MONO, fontsize=10, color=FG)
fig.text(0.06, 0.432, "Cholera deaths per 10,000 people, 1849  (district shapes approximate)", family=MONO, fontsize=10, color=MUT)

# ---------- big numbers
tx = fig.add_axes([0.66, 0.405, 0.31, 0.43]); tx.axis("off")
s = R["south"]["simon"]
items = [
    (f"{R['farr']['worst_to_best_ratio']:.0f}×", f"the death rate in Rotherhithe ({R['farr']['worst'][0]['rate']}\nper 10,000), on the river, against\nHampstead ({R['farr']['best'][0]['rate']}), on its hill."),
    (f"{s['ratio_1854']:.1f}×", f"South London, same districts, 1854:\nSouthwark and Vauxhall water {s['southwark_1854']:.1f}\nper 1,000, Lambeth water {s['lambeth_1854']:.1f}.\nIn 1849 both were {s['lambeth_1849']:.1f}."),
    (f"{R['broad']['median_dist_m']} m", f"Half of the {R['broad']['deaths_on_map']} deaths on Snow's 1854\nmap lay this close to the Broad\nStreet pump."),
    (f"{R['long']['chol_ahc']['rho']:.2f}".replace("-", "−"), f"rank correlation between 1849 cholera\nand 2023 income in {R['long']['n_units']} areas. The\nworst-hit places are not the poorest."),
]
for (big, small), y in zip(items, [1.0, 0.735, 0.43, 0.18]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=40, color=ACCD, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.092, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# ---------- small multiples
row_y, row_h = 0.14, 0.16


def panel(x, w, title):
    a = fig.add_axes([x, row_y, w, row_h]); a.set_facecolor(BG)
    for sp in ["top", "right"]: a.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]: a.spines[sp].set_color(FG); a.spines[sp].set_linewidth(.8)
    a.tick_params(colors=FG, labelsize=9.5, length=3)
    for t in a.get_xticklabels() + a.get_yticklabels(): t.set_family(MONO)
    fig.text(x, row_y + row_h + 0.018, title, family=MONO, fontsize=10.5, color=FG, va="bottom", linespacing=1.3)
    return a


fig.text(0.05, row_y + row_h + 0.07, "FIG. 1", family=MONO, fontsize=10, color=MUT)
fig.add_artist(plt.Line2D([0.05, 0.95], [row_y + row_h + 0.064, row_y + row_h + 0.064], transform=fig.transFigure, color=FG, lw=.8))

# 1 Farr's law
a = panel(0.065, 0.18, "Farr's law (black dots:\ncentral Thames water)")
X = lambda e: np.log(np.asarray(e) + 3)
cmap = {"Battersea": FG, "New River": "#7D8A8C", "Kew": ACC}
for w in ["New River", "Kew", "Battersea"]:
    g = F[F.water == w]
    a.scatter(X(g.elevation), g.cholera_drate, s=10 + g.popn / 5000, c=cmap[w], lw=.4, ec=BG, zorder=3)
fl = R["farr"]["farr_law_series"]
a.plot(X(fl["elevation"]), fl["mortality"], color=FG, lw=1.1, ls="--")
a.set_xticks(X([0, 10, 50, 350])); a.set_xticklabels(["0", "10", "50", "350"]); a.set_ylim(0, 215)
a.set_xlabel("feet above the Thames", family=MONO, fontsize=9.5, color=MUT)

# 2 Simon slope
a = panel(0.305, 0.17, "Then the water\nchanged, not the hill")
a.plot([0, 1], [s["southwark_1849"], s["southwark_1854"]], color=FG, lw=2.6, marker="o", ms=6)
a.plot([0, 1], [s["lambeth_1849"], s["lambeth_1854"]], color=ACC, lw=2.6, marker="o", ms=6)
a.text(1.06, s["southwark_1854"], "S. and V.", family=MONO, fontsize=9.5, va="center", color=FG)
a.text(1.06, s["lambeth_1854"], "Lambeth", family=MONO, fontsize=9.5, va="center", color=ACCD)
a.set_xticks([0, 1]); a.set_xticklabels(["1849", "1854"]); a.set_xlim(-.15, 1.0); a.set_ylim(0, 15)
a.set_ylabel("deaths per 1,000", family=MONO, fontsize=9.5, color=MUT)

# 3 Broad Street mini map
a = fig.add_axes([0.53, row_y - 0.012, 0.2, row_h + 0.024]); a.set_facecolor(BG); a.axis("off")
fig.text(0.53, row_y + row_h + 0.018, "Broad Street, 1854:\nevery death on Snow's map", family=MONO, fontsize=10.5, color=FG, va="bottom", linespacing=1.3)
for st in ST:
    c = np.array(st["geometry"]["coordinates"]); a.plot(c[:, 0] * KX, c[:, 1], color="#8E9A9C", lw=.45)
bs = PU[PU.label_histdata == "Broad St"].iloc[0]
col = np.where(DE.nearest_pump_walk == "Broad St", FG, "#8E9A9C")
a.scatter(DE.lon * KX, DE.lat, s=3.2, c=col, lw=0, zorder=3)
a.scatter(PU.lon * KX, PU.lat, s=22, fc=BG, ec=FG, lw=1, zorder=4)
a.scatter([bs.lon * KX], [bs.lat], s=70, fc=ACC, ec=FG, lw=1.2, zorder=5)
for r in (100, 200):
    t = np.linspace(0, 2 * np.pi, 120)
    a.plot(bs.lon * KX + r / 111320 * np.cos(t), bs.lat + r / 111320 * np.sin(t), color=FG, lw=.6, ls=(0, (2, 2)))
a.set_xlim((bs.lon - .0045) * KX, (bs.lon + .0045) * KX); a.set_ylim(bs.lat - .0045, bs.lat + .0045); a.set_aspect("equal")
a.text((bs.lon - .0044) * KX, bs.lat - .0044, "rings: 100 and 200 m", family=MONO, fontsize=8.8, color=MUT)

# 4 then and now
a = panel(0.775, 0.17, "1849 deaths against\n2023 income: no link")
a.scatter(UT.cholera_rate_1849, UT.income_net_ahc_2023 / 1000, s=10 + UT.pop_2021 / 6000, c=FG, alpha=.85, lw=.4, ec=BG)
a.set_xlabel("deaths per 10,000, 1849", family=MONO, fontsize=9.5, color=MUT)
a.set_ylabel("£000 after housing, 2023", family=MONO, fontsize=9.5, color=MUT)
a.set_xlim(0, 220); a.set_ylim(30, 56)

# footer
fig.text(0.05, 0.03,
         "Data: Farr (1852) via Bingham, Verlander and Cheal (2004) and the HistData R package (GPL); Snow (1855) and Simon (1856) via\n"
         "T. Coleman's SnowCholera (BSD 2-Clause); Snow's map via P. Li's cholera R package (GPL); ONS small area income FYE2023 and Census 2021,\n"
         "OS Open Names and OS Open Rivers (OGL v3, contains OS data © Crown copyright and database right 2026). 1849 districts linked to 2021\n"
         "areas by named places: approximate. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=8.4, color=MUT, linespacing=1.4, va="bottom")
fig.savefig(os.path.join(HERE, "the_hill_or_the_water.png"), dpi=200, facecolor=BG)
print("saved")
