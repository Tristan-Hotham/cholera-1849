"""Step 2. Link Farr's 1849 districts to today's small areas (MSOA 2021), approximately.

There is no open digital boundary file for the 1849 London registration districts that I could use,
so I do this in a simple, explicit way:

1. Each 1849 district gets one or more seed places: named areas that lay inside it, looked up by name
   in OS Open Names (the list is in SEEDS below, and every seed's coordinates are written to
   data/district_seeds.csv). A few small neighbouring districts that I cannot separate at MSOA scale
   are merged into one unit (the three City districts; the three Borough districts of Southwark;
   the four West End districts of St James, Hanover Square and Mayfair, Strand and St Martin-in-the-Fields).
2. Every 2021 MSOA in the thirteen inner London boroughs that cover the 1849 metropolis is given to the
   unit with the nearest seed (by its population-weighted centroid), on the same bank of the Thames.
   MSOAs more than 4 km from every seed are left out.
3. Each unit gets its 2021 population (Census 2021) and population-weighted mean of the ONS FYE2023
   MSOA income estimates. Shapes for the map are Voronoi cells around MSOA centroids, merged by unit.

Usage: python3 code/02_link_today.py
Outputs: data/district_seeds.csv, data/msoa_to_1849.csv, data/units_then_now.csv, data/units_1849.geojson
"""
import csv
import json
import os

import numpy as np
import openpyxl
import pandas as pd
from pyproj import Transformer
from scipy.spatial import Voronoi, cKDTree
from shapely.geometry import MultiPoint, Point, Polygon, mapping
from shapely.ops import transform, unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
D8 = "/home/claude/hist/_data8"
OSN = "/home/claude/hist/osnames_gb.tsv"
to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
to_ll = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True).transform

# unit name -> (Farr districts in it, bank, seed place names in OS Open Names)
UNITS = {
    "City of London": (["London City", "West London", "East London"], "N", ["City of London"]),
    "Borough (St Saviour, St Olave, St George)": (["St Saviour", "St Olave", "St George Southwark"], "S", ["Southwark"]),
    "Westminster": (["Westminster"], "N", ["City of Westminster"]),
    "West End (St James, Mayfair, Strand, St Martin)": (["St James Westminster", "Hanover Square & Mayfair", "Strand", "St Martin-in-the-Fields"], "N", ["Strand", "Soho", "St James's", "Mayfair"]),
    "Belgrave": (["Belgrave"], "N", ["Belgravia", "Pimlico"]),
    "St Giles": (["St Giles"], "N", ["St Giles", "Bloomsbury"]),
    "Holborn": (["Holborn"], "N", ["Holborn"]),
    "Clerkenwell": (["Clerkenwell"], "N", ["Clerkenwell"]),
    "St Luke": (["St Luke"], "N", ["St Luke's"]),
    "Marylebone": (["Marylebone"], "N", ["Marylebone", "St John's Wood"]),
    "Paddington": (["Paddington"], "N", ["Paddington", "Bayswater", "Maida Vale"]),
    "Hampstead": (["Hampstead"], "N", ["Hampstead"]),
    "St Pancras": (["St Pancras"], "N", ["St Pancras", "Camden Town", "Kentish Town", "Somers Town", "Gospel Oak"]),
    "Islington": (["Islington"], "N", ["Islington", "Highbury", "Lower Holloway", "Upper Holloway"]),
    "Hackney": (["Hackney"], "N", ["Hackney", "Homerton", "Stoke Newington", "Upper Clapton", "Lower Clapton"]),
    "Shoreditch": (["Shoreditch"], "N", ["Shoreditch", "Hoxton", "Haggerston"]),
    "Bethnal Green": (["Bethnal Green"], "N", ["Bethnal Green"]),
    "Whitechapel": (["Whitechapel"], "N", ["Whitechapel", "Spitalfields"]),
    "St George in the East": (["St George East"], "N", ["Wapping", "Shadwell"]),
    "Stepney": (["Stepney"], "N", ["Stepney", "Limehouse", "Mile End"]),
    "Poplar": (["Poplar"], "N", ["Poplar", "Bow", "Bromley"]),
    "Kensington (with Hammersmith, Brompton and Fulham)": (["Hammersmith, Brompton, Kensington and Fulham"], "N", ["Kensington", "Brompton", "Hammersmith", "Fulham", "Notting Hill"]),
    "Chelsea": (["Chelsea"], "N", ["Chelsea"]),
    "Greenwich": (["Greenwich"], "S", ["Greenwich", "Deptford"]),
    "Lewisham": (["Lewisham"], "S", ["Lewisham", "Lee", "Eltham", "Lower Sydenham"]),
    "Wandsworth": (["Wandsworth"], "S", ["Wandsworth", "Battersea", "Putney", "Clapham", "Upper Tooting", "Streatham"]),
    "Lambeth": (["Lambeth"], "S", ["Lambeth", "Kennington", "Vauxhall", "Brixton", "Stockwell", "West Norwood"]),
    "Camberwell": (["Camberwell"], "S", ["Camberwell", "Peckham", "Dulwich"]),
    "Newington": (["Newington"], "S", ["Newington", "Walworth"]),
    "Bermondsey": (["Bermondsey"], "S", ["Bermondsey"]),
    "Rotherhithe": (["Rotherhithe"], "S", ["Rotherhithe"]),
}
LADS = {"City of London": "N", "Westminster": "N", "Camden": "N", "Islington": "N", "Hackney": "N", "Tower Hamlets": "N",
        "Kensington and Chelsea": "N", "Hammersmith and Fulham": "N",
        "Southwark": "S", "Lambeth": "S", "Wandsworth": "S", "Lewisham": "S", "Greenwich": "S"}
MAXKM = 4.0

F = pd.read_csv(os.path.join(D, "farr_1849_districts.csv"))
allf = [d for u in UNITS.values() for d in u[0]]
assert sorted(allf) == sorted(F.district), set(F.district) ^ set(allf)

# seeds from OS Open Names (populated places in London; the inner-London box excludes namesakes elsewhere)
want = {s for u in UNITS.values() for s in u[2]}
hits = {}
for r in csv.DictReader(open(OSN, encoding="utf-8"), delimiter="\t"):
    if r["name1"] in want and r["type"] == "populatedPlace":
        lat, lon = float(r["lat"]), float(r["lon"])
        if 51.41 < lat < 51.60 and -0.30 < lon < 0.10:
            hits.setdefault(r["name1"], []).append((r["local_type"], lat, lon))
seeds = []
for u, (ds, bank, names) in UNITS.items():
    for n in names:
        h = hits[n]
        h = [x for x in h if x[0] in ("City", "Other Settlement", "Suburban Area")] or h
        assert len(h) == 1, (n, h)
        seeds.append({"unit": u, "bank": bank, "seed": n, "os_local_type": h[0][0], "lat": h[0][1], "lon": h[0][2]})
S = pd.DataFrame(seeds)
S.to_csv(os.path.join(D, "district_seeds.csv"), index=False)
print("seeds", len(S))

# MSOAs
geo = json.load(open(os.path.join(D8, "ons_geo.json")))
pwc = pd.DataFrame(geo["msoa21_pwc"])[["MSOA21CD", "_x", "_y"]].rename(columns={"_x": "lon", "_y": "lat"})
lk = pd.DataFrame(geo["msoa21_bua22_lookup"])[["MSOA21CD", "MSOA21NM", "LAD22NM"]]
M = pwc.merge(lk, on="MSOA21CD")
M = M[M.LAD22NM.isin(LADS)].copy()
M["bank"] = M.LAD22NM.map(LADS)
pop = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-msoa.csv"))
pop = pop.rename(columns={"geography code": "MSOA21CD", "Residence type: Total; measures: Value": "pop2021"})[["MSOA21CD", "pop2021"]]
M = M.merge(pop, on="MSOA21CD", how="left")
wb = openpyxl.load_workbook(os.path.join(D8, "ons_msoa_income_fye2023.xlsx"), read_only=True)
for sheet, col in [("Total annual income", "income_total"), ("Net income after housing costs", "income_net_ahc")]:
    rows = list(wb[sheet].iter_rows(values_only=True))
    i = next(k for k, r in enumerate(rows) if r and r[0] == "MSOA code")
    inc = pd.DataFrame([(r[0], r[6]) for r in rows[i + 1:] if r and r[0]], columns=["MSOA21CD", col])
    M = M.merge(inc, on="MSOA21CD", how="left")
assert M.pop2021.notna().all() and M.income_total.notna().all() and M.income_net_ahc.notna().all()

# nearest seed on the same bank
M["x"], M["y"] = to_bng(M.lon.values, M.lat.values)
S["x"], S["y"] = to_bng(S.lon.values, S.lat.values)
M["unit"], M["seed"], M["seed_km"] = None, None, np.nan
for bank in "NS":
    ss = S[S.bank == bank].reset_index(drop=True)
    tr = cKDTree(ss[["x", "y"]].values)
    idx = M.bank == bank
    dist, j = tr.query(M.loc[idx, ["x", "y"]].values)
    M.loc[idx, "unit"] = ss.unit.values[j]
    M.loc[idx, "seed"] = ss.seed.values[j]
    M.loc[idx, "seed_km"] = dist / 1000
M["in_scope"] = M.seed_km <= MAXKM
print("MSOAs in 13 boroughs", len(M), "in scope", int(M.in_scope.sum()))
M[["MSOA21CD", "MSOA21NM", "LAD22NM", "lon", "lat", "pop2021", "income_total", "income_net_ahc", "unit", "seed", "seed_km", "in_scope"]].to_csv(
    os.path.join(D, "msoa_to_1849.csv"), index=False, float_format="%.5f")
Mi = M[M.in_scope]

# then-and-now table by unit
rows = []
for u, (ds, bank, names) in UNITS.items():
    f = F[F.district.isin(ds)]
    g = Mi[Mi.unit == u]
    w = g.pop2021
    rows.append({
        "unit": u, "farr_districts": "; ".join(ds), "bank": bank, "region_1849": "/".join(sorted(set(f.region))),
        "water_1849": "/".join(sorted(set(f.water))),
        "pop_1849": int(f.popn.sum()), "cholera_deaths_1849": int(f.cholera_deaths.sum()),
        "cholera_rate_1849": round(f.cholera_deaths.sum() / f.popn.sum() * 10000, 1),
        "elevation_ft": round(float((f.elevation * f.popn).sum() / f.popn.sum()), 1),
        "house_value_pp_1849": round(float(f.house_val.sum() / f.popn.sum()), 3),
        "poor_rate_1849": round(float((f.poor_rate * f.house_val).sum() / f.house_val.sum()), 4),
        "persons_per_house_1849": round(float(f.popn.sum() / f.houses.sum()), 2),
        "msoas_2021": len(g), "pop_2021": int(w.sum()),
        "income_total_2023": round(float((g.income_total * w).sum() / w.sum())),
        "income_net_ahc_2023": round(float((g.income_net_ahc * w).sum() / w.sum())),
        "seeds": "; ".join(names),
    })
U = pd.DataFrame(rows)
assert (U.msoas_2021 > 0).all(), U[U.msoas_2021 == 0]
U.to_csv(os.path.join(D, "units_then_now.csv"), index=False)
print(U[["unit", "cholera_rate_1849", "house_value_pp_1849", "msoas_2021", "income_net_ahc_2023"]].to_string())

# shapes: Voronoi cells around MSOA centroids, clipped to a buffer around them, merged by unit
P = Mi[["x", "y"]].values
far = np.array([[P[:, 0].min() - 2e4, P[:, 1].min() - 2e4], [P[:, 0].min() - 2e4, P[:, 1].max() + 2e4],
                [P[:, 0].max() + 2e4, P[:, 1].min() - 2e4], [P[:, 0].max() + 2e4, P[:, 1].max() + 2e4]])
vor = Voronoi(np.vstack([P, far]))
hull = unary_union([Point(p).buffer(1100) for p in P]).buffer(-300)
cells = []
for i in range(len(P)):
    reg = vor.regions[vor.point_region[i]]
    poly = Polygon(vor.vertices[reg]).intersection(hull)
    cells.append(poly)
Mi = Mi.assign(cell=cells)
feats = []
for _, r in U.iterrows():
    geom = unary_union(list(Mi[Mi.unit == r.unit].cell)).buffer(1).buffer(-1).simplify(40)
    gl = transform(lambda x, y, z=None: to_ll(x, y), geom)
    props = {k: (v.item() if hasattr(v, "item") else v) for k, v in r.items()}
    feats.append({"type": "Feature", "properties": props, "geometry": mapping(gl)})


def rnd(o):
    if isinstance(o, float):
        return round(o, 5)
    if isinstance(o, (list, tuple)):
        return [rnd(x) for x in o]
    if isinstance(o, dict):
        return {k: rnd(v) for k, v in o.items()}
    return o


json.dump(rnd({"type": "FeatureCollection", "features": feats}), open(os.path.join(D, "units_1849.geojson"), "w"), separators=(",", ":"))
print("geojson", os.path.getsize(os.path.join(D, "units_1849.geojson")))
