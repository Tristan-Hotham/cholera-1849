"""Step 1. Extract the historical tables into plain CSV and GeoJSON files.

Inputs (clone these first; they are not kept in this repository):
  git clone --depth 1 https://github.com/friendly/HistData      (GPL; Farr 1849, Snow 1854 dates, Farr daily deaths)
  git clone --depth 1 https://github.com/lindbrook/cholera      (GPL >= 2; georeferenced Snow map: deaths, pumps, roads)
  git clone --depth 1 https://github.com/tscoleman/SnowCholera  (BSD 2-Clause; Snow 1855 and Simon 1856 tables)
OS Open Rivers (OGL v3) is read in place for the line of the Thames.

Usage:
  python3 code/01_extract.py HISTDATA_DIR CHOLERA_DIR SNOWCHOLERA_DIR

Outputs in data/:
  farr_1849_districts.csv   Farr's 38 London registration districts, 1849 (Bingham et al. 2004 via HistData)
  farr_1849_daily.csv       daily cholera and diarrhoea deaths in 1849 (Farr 1852 Plate 2, via HistData)
  snow_1854_deaths.csv      578 deaths on Snow's map, with longitude and latitude (cholera package)
  snow_1854_pumps.csv       13 pumps on Snow's map
  snow_1854_dates.csv       fatal attacks and deaths by day, 19 August to 30 September 1854 (Snow 1855 Table 1)
  snow_1854_streets.geojson street lines of Snow's map
  snow_1855_table_xii.csv   deaths by South London sub-district, 1849 and 1854, with water supplier (Snow 1855)
  snow_1855_table_ix.csv    deaths per 10,000 houses by water company, 1854 (Snow 1855)
  simon_1856_table_ii.csv   deaths per 1,000 by water company, 1848-49 and 1853-54 (Simon 1856)
  thames.geojson            River Thames centre line in London (OS Open Rivers)
"""
import csv
import json
import os
import sqlite3
import struct
import sys

import pandas as pd
import pyreadr
from pyproj import Transformer
from shapely import wkb
from shapely.geometry import box, mapping
from shapely.ops import transform, linemerge, unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
HD, CH, SC = sys.argv[1:4]
RIVERS = "/home/claude/hist/osrivers/Data/oprvrs_gb.gpkg"


def rd(path, key=None):
    r = pyreadr.read_r(path)
    return r[key] if key else list(r.values())[0]


# ---- Farr 1849, 38 districts
f = rd(os.path.join(HD, "data", "Cholera.RData"))
f["water"] = f["water"].astype(str)
f["region"] = f["region"].astype(str)
f.to_csv(os.path.join(D, "farr_1849_districts.csv"), index=False)
print("districts", len(f), "deaths", f.cholera_deaths.sum(), "pop", f.popn.sum())

# ---- Farr daily deaths 1849
d = rd(os.path.join(HD, "data", "CholeraDeaths1849.RData"))
d = d[["date", "cause_of_death", "deaths"]].copy()
d["cause_of_death"] = d["cause_of_death"].astype(str)
d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
d.to_csv(os.path.join(D, "farr_1849_daily.csv"), index=False)

# ---- Snow 1854 (georeferenced by the cholera package)
fu = rd(os.path.join(CH, "data", "fatalities.unstacked.rda"))
fs = rd(os.path.join(CH, "data", "fatalities.rda"))
fa = rd(os.path.join(CH, "data", "fatalities.anchor.rda"))
m = fu[["case", "lon", "lat"]].merge(fs[["case", "lon", "lat"]].rename(columns={"lon": "lon_stacked", "lat": "lat_stacked"}), on="case")
m["case"] = m["case"].astype(int)
m.to_csv(os.path.join(D, "snow_1854_deaths.csv"), index=False, float_format="%.6f")
fa[["anchor", "case.count", "lon", "lat"]].rename(columns={"case.count": "deaths"}).astype({"anchor": int, "deaths": int}).to_csv(
    os.path.join(D, "snow_1854_addresses.csv"), index=False, float_format="%.6f")
p = rd(os.path.join(CH, "data", "pumps.rda"))
p = p.rename(columns={"street": "street_today"})
hp = rd(os.path.join(HD, "data", "Snow.pumps.RData"))
p["label_histdata"] = hp["label"].astype(str).values
p[["id", "label_histdata", "street_today", "lon", "lat"]].to_csv(os.path.join(D, "snow_1854_pumps.csv"), index=False, float_format="%.6f")
r = rd(os.path.join(CH, "data", "roads.rda"))
feats = []
for sid, g in r.groupby("street"):
    nm = str(g["name"].iloc[0])
    if nm == "Map Frame":
        continue
    feats.append({"type": "Feature", "properties": {"street": int(sid), "name": nm},
                  "geometry": {"type": "LineString", "coordinates": [[round(a, 6), round(b, 6)] for a, b in zip(g.lon, g.lat)]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(D, "snow_1854_streets.geojson"), "w"), separators=(",", ":"))
sd = rd(os.path.join(HD, "data", "Snow.dates.RData"))
sd["date"] = pd.to_datetime(sd["date"]).dt.strftime("%Y-%m-%d")
sd.to_csv(os.path.join(D, "snow_1854_dates.csv"), index=False)
print("snow deaths", len(m), "pumps", len(p), "streets", len(feats), "dates", len(sd))


# ---- Coleman's transcriptions of Snow (1855) and Simon (1856)
def read_coleman(name, header_key):
    rows = list(csv.reader(open(os.path.join(SC, name), encoding="utf-8-sig")))
    i = next(k for k, row in enumerate(rows) if row and row[0] == header_key)
    out = []
    for row in rows[i + 1:]:
        if not row or not row[0] or row[0].startswith("#"):
            break
        out.append(dict(zip(rows[i], row)))
    return pd.DataFrame(out)


x12 = read_coleman("Snow1855_TableXII.csv", "subDistrict")
x12 = x12[["subDistrict", "district", "supplier", "deaths1849", "deaths1854"]]
x12.to_csv(os.path.join(D, "snow_1855_table_xii.csv"), index=False)
# Table IX is stored on one line in the source file; its four values per row are copied here as printed by Snow
ix = open(os.path.join(SC, "Snow1855_TableIX.csv"), encoding="utf-8-sig").read()
assert "40046,1263,315" in ix and "26107,98,37" in ix and "256423,1422,59" in ix
pd.DataFrame([["Southwark and Vauxhall Company", 40046, 1263, 315], ["Lambeth Company", 26107, 98, 37], ["Rest of London", 256423, 1422, 59]],
             columns=["supplier", "houses", "deaths", "deaths_per_10000_houses"]).to_csv(os.path.join(D, "snow_1855_table_ix.csv"), index=False)
s2 = read_coleman("Simon1856_TableII.csv", "district")
s2.to_csv(os.path.join(D, "simon_1856_table_ii.csv"), index=False)
print("table xii", len(x12), "simon", len(s2))

# ---- River Thames through London from OS Open Rivers
to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
to_ll = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True).transform
bb = box(*to_bng(-0.33, 51.40), *to_bng(0.20, 51.60))
con = sqlite3.connect(f"file:{RIVERS}?mode=ro", uri=True)
lines = []
for (g,) in con.execute("select geometry from watercourse_link where watercourse_name='River Thames'"):
    flags = g[3]
    env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    geom = wkb.loads(bytes(g[8 + env:]))
    if geom.intersects(bb):
        lines.append(geom.intersection(bb))
th = linemerge(unary_union(lines)).simplify(15)
th_ll = transform(lambda x, y, z=None: to_ll(x, y), th)
json.dump({"type": "Feature", "properties": {"name": "River Thames"}, "geometry": mapping(th_ll)}, open(os.path.join(D, "thames.geojson"), "w"))
print("thames parts", len(lines))
