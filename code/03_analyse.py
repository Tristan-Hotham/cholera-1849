"""Step 3. All the analysis. Writes data/results.json (every number used anywhere) and work/site.json
(compact data for the page).

Usage: python3 code/03_analyse.py
Needs: pandas, numpy, scipy, statsmodels, networkx, shapely, pyproj.
"""
import json
import math
import os

import networkx as nx
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from pyproj import Transformer
from scipy import stats
from scipy.optimize import curve_fit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
W = os.path.join(ROOT, "work")
os.makedirs(W, exist_ok=True)
to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
R = {}


def r1(x, n=1):
    return round(float(x), n)


# ======================= 1. Farr's 38 districts =======================
F = pd.read_csv(os.path.join(D, "farr_1849_districts.csv"))
F["rate"] = F.cholera_deaths / F.popn * 10000
tot_d, tot_p = int(F.cholera_deaths.sum()), int(F.popn.sum())
srt = F.sort_values("rate", ascending=False)
R["farr"] = {
    "n_districts": len(F), "deaths": tot_d, "population": tot_p, "rate_per_10000": r1(tot_d / tot_p * 10000),
    "worst": [{"district": r.district, "rate": int(r.cholera_drate), "deaths": int(r.cholera_deaths), "elevation": int(r.elevation), "water": r.water} for r in srt.head(6).itertuples()],
    "best": [{"district": r.district, "rate": int(r.cholera_drate), "deaths": int(r.cholera_deaths), "elevation": int(r.elevation), "water": r.water} for r in srt.tail(6).iloc[::-1].itertuples()],
}
R["farr"]["worst_to_best_ratio"] = r1(srt.iloc[0].cholera_drate / srt.iloc[-1].cholera_drate, 0)
rho, p = stats.spearmanr(F.elevation, F.cholera_drate)
R["farr"]["elev_spearman"] = r1(rho, 2)
R["farr"]["elev_spearman_p"] = float(f"{p:.1g}")
R["farr"]["elev_min"], R["farr"]["elev_max"] = int(F.elevation.min()), int(F.elevation.max())
R["farr"]["n_below_20ft"] = int((F.elevation < 20).sum())

# elevation bands, pooled
bands = [(-5, 20, "Below 20 ft"), (20, 40, "20 to 39 ft"), (40, 60, "40 to 59 ft"), (60, 100, "60 to 99 ft"), (100, 400, "100 ft and above")]
R["farr"]["bands"] = []
for lo, hi, lab in bands:
    g = F[(F.elevation >= lo) & (F.elevation < hi)]
    R["farr"]["bands"].append({"label": lab, "n": len(g), "deaths": int(g.cholera_deaths.sum()), "population": int(g.popn.sum()),
                               "rate": r1(g.cholera_deaths.sum() / g.popn.sum() * 10000)})
R["farr"]["band_ratio_low_high"] = r1(R["farr"]["bands"][0]["rate"] / R["farr"]["bands"][-1]["rate"], 1)

# Farr's own law (his 1852 series, as printed in the HistData documentation) and my fitted hyperbola
R["farr"]["farr_law_series"] = {"elevation": [0, 10, 30, 50, 70, 90, 100, 350], "mortality": [174, 99, 53, 34, 27, 22, 20, 6]}


def hyp(e, a, b):
    return a / (e + b)


(a, b), _ = curve_fit(hyp, F.elevation, F.cholera_drate, p0=(1000, 10), sigma=1 / np.sqrt(F.popn), maxfev=20000)
pred = hyp(F.elevation, a, b)
R["farr"]["fit_a"], R["farr"]["fit_b"] = r1(a, 0), r1(b, 1)
R["farr"]["fit_r2"] = r1(1 - ((F.cholera_drate - pred) ** 2 * F.popn).sum() / (((F.cholera_drate - np.average(F.cholera_drate, weights=F.popn)) ** 2) * F.popn).sum(), 2)

# water supply groups
WN = {"Battersea": "Thames, Battersea to Waterloo Bridge", "New River": "New River, Lea and Ravensbourne", "Kew": "Thames at Kew and Hammersmith"}
R["water"] = {"groups": []}
for w in ["Battersea", "New River", "Kew"]:
    g = F[F.water == w]
    rr, pp = stats.spearmanr(g.elevation, g.cholera_drate)
    R["water"]["groups"].append({"key": w, "label": WN[w], "n": len(g), "deaths": int(g.cholera_deaths.sum()), "population": int(g.popn.sum()),
                                 "rate": r1(g.cholera_deaths.sum() / g.popn.sum() * 10000), "elev_median": r1(g.elevation.median()),
                                 "elev_max": int(g.elevation.max()), "rho_within": r1(rr, 2), "p_within": float(f"{pp:.1g}"),
                                 "house_value_pp": r1(g.house_val.sum() / g.popn.sum(), 2)})
gb = {g["key"]: g for g in R["water"]["groups"]}
R["water"]["ratio_battersea_kew"] = r1(gb["Battersea"]["rate"] / gb["Kew"]["rate"], 1)
R["water"]["ratio_battersea_newriver"] = r1(gb["Battersea"]["rate"] / gb["New River"]["rate"], 1)
R["water"]["battersea_all_below_ft"] = int(F[F.water == "Battersea"].elevation.max())
F["le"] = np.log(F.elevation + 3)
F["lhv"] = np.log(F.house_val / F.popn)
mods = {}
for k, f in [("elev", "le"), ("water", "C(water)"), ("both", "le + C(water)"), ("all", "le + C(water) + lhv")]:
    mods[k] = smf.wls("np.log(cholera_drate) ~ " + f, data=F, weights=F.popn).fit()
R["water"]["r2"] = {k: r1(m.rsquared, 2) for k, m in mods.items()}
R["water"]["elev_fall_per_doubling_alone"] = r1(1 - 2 ** mods["elev"].params["le"], 3)
R["water"]["elev_fall_per_doubling_with_water"] = r1(1 - 2 ** mods["both"].params["le"], 3)
R["water"]["elev_coef_shrink"] = r1(1 - mods["both"].params["le"] / mods["elev"].params["le"], 3)
R["water"]["kew_vs_battersea_same_elev"] = r1(math.exp(mods["both"].params["C(water)[T.Kew]"]), 2)
R["water"]["newriver_vs_battersea_same_elev"] = r1(math.exp(mods["both"].params["C(water)[T.New River]"]), 2)
R["water"]["p_newriver_same_elev"] = r1(mods["both"].pvalues["C(water)[T.New River]"], 2)
R["water"]["lhv_fall_per_doubling_all"] = r1(1 - 2 ** mods["all"].params["lhv"], 3)
R["water"]["p_lhv_all"] = r1(mods["all"].pvalues["lhv"], 2)

# Snow (1855) and Simon (1856): South London's two water companies
x12 = pd.read_csv(os.path.join(D, "snow_1855_table_xii.csv"))
grp = {"SouthwarkVauxhall": "Southwark and Vauxhall only", "SouthwarkVauxhall_Lambeth": "Both companies", "Lambeth": "Lambeth only"}
R["south"] = {"groups": []}
for k, lab in grp.items():
    g = x12[x12.supplier == k]
    R["south"]["groups"].append({"key": k, "label": lab, "n_subdistricts": len(g), "deaths_1849": int(g.deaths1849.sum()), "deaths_1854": int(g.deaths1854.sum()),
                                 "change": r1(g.deaths1854.sum() / g.deaths1849.sum() - 1, 3)})
s2 = pd.read_csv(os.path.join(D, "simon_1856_table_ii.csv"))
t = s2[s2.district == "Totals and means for the whole area"].iloc[0]
R["south"]["simon"] = {"lambeth_1849": float(t.mortrate_lambeth_1848), "lambeth_1854": float(t.mortrate_lambeth_1853),
                       "southwark_1849": float(t.mortrate_southwark_1848), "southwark_1854": float(t.mortrate_southwark_1853),
                       "houses_lambeth": int(t.houses_lambeth), "houses_southwark": int(t.houses_southwark),
                       "deaths_lambeth_1849": int(t.deaths_lambeth_1848), "deaths_lambeth_1854": int(t.deaths_lambeth_1853),
                       "deaths_southwark_1849": int(t.deaths_southwark_1848), "deaths_southwark_1854": int(t.deaths_southwark_1853),
                       "n_districts": 9}
si = R["south"]["simon"]
si["ratio_1854"] = r1(si["southwark_1854"] / si["lambeth_1854"], 1)
si["lambeth_fall"] = r1(1 - si["lambeth_1854"] / si["lambeth_1849"], 3)
ix = pd.read_csv(os.path.join(D, "snow_1855_table_ix.csv"))
R["south"]["table_ix"] = ix.to_dict("records")
R["south"]["table_ix_ratio"] = r1(ix.deaths_per_10000_houses[0] / ix.deaths_per_10000_houses[1], 1)

# national daily deaths 1849
dd = pd.read_csv(os.path.join(D, "farr_1849_daily.csv"))
c = dd[dd.cause_of_death == "Cholera"].dropna(subset=["date"]).copy()
c["date"] = pd.to_datetime(c["date"])
pk = c.loc[c.deaths.idxmax()]
c["month"] = c.date.dt.month
mon = c.groupby("month").deaths.sum()
R["national"] = {"cholera_deaths_1849": int(c.deaths.sum()), "diarrhoea_deaths_1849": int(dd[dd.cause_of_death == "Diarrhaea"].deaths.sum()),
                 "peak_date": pk.date.strftime("%-d %B"), "peak_deaths": int(pk.deaths),
                 "aug_sep_share": r1((mon.get(8, 0) + mon.get(9, 0)) / mon.sum(), 3),
                 "monthly": [int(mon.get(m, 0)) for m in range(1, 13)]}
weekly = c.set_index("date").deaths.resample("W-SAT").sum()
R["national"]["weekly"] = [[d.strftime("%Y-%m-%d"), int(v)] for d, v in weekly.items()]

# ======================= 2. Broad Street 1854 =======================
deaths = pd.read_csv(os.path.join(D, "snow_1854_deaths.csv"))
pumps = pd.read_csv(os.path.join(D, "snow_1854_pumps.csv"))
addr = pd.read_csv(os.path.join(D, "snow_1854_addresses.csv"))
dx, dy = to_bng(deaths.lon.values, deaths.lat.values)
px, py = to_bng(pumps.lon.values, pumps.lat.values)
bs = int(np.where(pumps.label_histdata == "Broad St")[0][0])
E = np.hypot(dx[:, None] - px[None, :], dy[:, None] - py[None, :])  # metres, deaths x pumps
deaths["dist_broad_m"] = E[:, bs]
deaths["nearest_pump_straight"] = pumps.label_histdata.values[E.argmin(1)]

# walking distance along Snow's streets
G = nx.Graph()
streets = json.load(open(os.path.join(D, "snow_1854_streets.geojson")))["features"]
segs = []
for fe in streets:
    co = [to_bng(*xy) for xy in fe["geometry"]["coordinates"]]
    for (x1, y1), (x2, y2) in zip(co[:-1], co[1:]):
        a, b = (round(x1, 1), round(y1, 1)), (round(x2, 1), round(y2, 1))
        G.add_edge(a, b, weight=math.hypot(x2 - x1, y2 - y1))
        segs.append((a, b))
# join street ends that the digitising left a hair apart (under 2 m)
nodes = np.array(list(G.nodes))
from scipy.spatial import cKDTree
tr = cKDTree(nodes)
for i, j in tr.query_pairs(2.0):
    G.add_edge(tuple(nodes[i]), tuple(nodes[j]), weight=float(np.hypot(*(nodes[i] - nodes[j]))))
S0 = np.array([s[0] for s in segs]); S1 = np.array([s[1] for s in segs])


def snap(x, y):
    v = S1 - S0
    t = np.clip(((x - S0[:, 0]) * v[:, 0] + (y - S0[:, 1]) * v[:, 1]) / np.maximum((v ** 2).sum(1), 1e-9), 0, 1)
    qx, qy = S0[:, 0] + t * v[:, 0], S0[:, 1] + t * v[:, 1]
    d = np.hypot(x - qx, y - qy)
    k = int(d.argmin())
    L = math.hypot(*v[k])
    return k, d[k], t[k] * L, (1 - t[k]) * L


big = max(nx.connected_components(G), key=len)
R["broad"] = {"street_nodes": G.number_of_nodes(), "largest_component_share": r1(len(big) / G.number_of_nodes(), 3)}
pump_snap = [snap(x, y) for x, y in zip(px, py)]
dist_from_pump = []
for k, off, da, db in pump_snap:
    a, b = segs[k]
    la = nx.single_source_dijkstra_path_length(G, a, weight="weight")
    lb = nx.single_source_dijkstra_path_length(G, b, weight="weight")
    dist_from_pump.append((k, off, da, db, la, lb))


def walk(x, y, pi):
    k, off, da, db = snap(x, y)
    pk_, poff, pda, pdb, la, lb = dist_from_pump[pi]
    a, b = segs[k]
    if k == pk_:
        return off + poff + abs(da - pda)
    # la/lb are from the two ends of the pump's segment; add the pump's distance to that end
    best = min(la.get(a, np.inf) + da + pda, la.get(b, np.inf) + db + pda, lb.get(a, np.inf) + da + pdb, lb.get(b, np.inf) + db + pdb)
    return off + poff + best


Wk = np.array([[walk(x, y, j) for j in range(len(pumps))] for x, y in zip(dx, dy)])
deaths["walk_broad_m"] = Wk[:, bs]
deaths["nearest_pump_walk"] = pumps.label_histdata.values[Wk.argmin(1)]
deaths["walk_ok"] = np.isfinite(Wk).all(1)
n = len(deaths)
B = R["broad"]
B.update({
    "deaths_on_map": n, "addresses": len(addr), "max_at_address": int(addr.deaths.max()),
    "median_dist_m": int(round(deaths.dist_broad_m.median())), "median_walk_m": int(round(deaths.walk_broad_m.median())),
    "within_100m": int((deaths.dist_broad_m <= 100).sum()), "within_200m": int((deaths.dist_broad_m <= 200).sum()),
    "within_300m": int((deaths.dist_broad_m <= 300).sum()),
    "share_within_200m": r1((deaths.dist_broad_m <= 200).mean(), 3), "share_within_300m": r1((deaths.dist_broad_m <= 300).mean(), 3),
    "nearest_broad_straight": int((deaths.nearest_pump_straight == "Broad St").sum()),
    "share_nearest_broad_straight": r1((deaths.nearest_pump_straight == "Broad St").mean(), 3),
    "nearest_broad_walk": int((deaths.nearest_pump_walk == "Broad St").sum()),
    "share_nearest_broad_walk": r1((deaths.nearest_pump_walk == "Broad St").mean(), 3),
    "nearer_other_pump_walk": int((deaths.nearest_pump_walk != "Broad St").sum()),
    "walk_unreachable": int((~np.isfinite(deaths.walk_broad_m)).sum()), "n_pumps": len(pumps),
})
# deaths by 50 m distance band, and the next most common nearest pump
bins = np.arange(0, 701, 50)
h, _ = np.histogram(deaths.dist_broad_m.clip(upper=699), bins)
B["dist_hist"] = [int(v) for v in h]
nxt = deaths.nearest_pump_walk.value_counts()
B["nearest_walk_counts"] = {k: int(v) for k, v in nxt.items()}
# ring density: deaths per hectare in rings around the pump
ring = []
for lo, hi in [(0, 100), (100, 200), (200, 300), (300, 400), (400, 500)]:
    k = int(((deaths.dist_broad_m >= lo) & (deaths.dist_broad_m < hi)).sum())
    ring.append({"lo": lo, "hi": hi, "deaths": k, "per_ha": r1(k / (math.pi * (hi ** 2 - lo ** 2) / 1e4), 1)})
B["rings"] = ring
B["ring_ratio_first_to_third"] = r1(ring[0]["per_ha"] / ring[2]["per_ha"], 1)
sd = pd.read_csv(os.path.join(D, "snow_1854_dates.csv"))
B["attacks_date_unknown"] = int(sd[sd.date.isna()].attacks.sum())
sd = sd.dropna(subset=["date"]).copy()
sd["date"] = pd.to_datetime(sd["date"])
B["dates_total_deaths"] = int(sd.deaths.sum())
B["dates_total_attacks"] = int(sd.attacks.sum()) + B["attacks_date_unknown"]
pkd = sd.loc[sd.attacks.idxmax()]
B["peak_attack_date"] = pkd.date.strftime("%-d %B")
B["peak_attacks"] = int(pkd.attacks)
B["attacks_before_handle"] = int(sd[sd.date < "1854-09-08"].attacks.sum())
B["attacks_from_handle"] = int(sd[sd.date >= "1854-09-08"].attacks.sum())
B["attacks_31aug_2sep"] = int(sd[(sd.date >= "1854-08-31") & (sd.date <= "1854-09-02")].attacks.sum())
B["attacks_day_before_handle"] = int(sd[sd.date == "1854-09-07"].attacks.iloc[0])
B["series"] = [[d.strftime("%Y-%m-%d"), int(a_), int(b_)] for d, a_, b_ in zip(sd.date, sd.attacks, sd.deaths)]
out = deaths[["case", "lon", "lat", "dist_broad_m", "walk_broad_m", "nearest_pump_straight", "nearest_pump_walk"]].copy()
out[["dist_broad_m", "walk_broad_m"]] = out[["dist_broad_m", "walk_broad_m"]].round(1)
out.to_csv(os.path.join(D, "snow_1854_deaths_distances.csv"), index=False)

# ======================= 3. The long shadow =======================
U = pd.read_csv(os.path.join(D, "units_then_now.csv"))
M = pd.read_csv(os.path.join(D, "msoa_to_1849.csv"))
Mi = M[M.in_scope]
L = {"n_units": len(U), "n_msoas": int(len(Mi)), "n_msoas_dropped": int((~M.in_scope).sum()), "pop_2021": int(Mi.pop2021.sum()),
     "max_seed_km": 4, "n_seeds": int(len(pd.read_csv(os.path.join(D, "district_seeds.csv"))))}
for k, x, y in [("chol_ahc", "cholera_rate_1849", "income_net_ahc_2023"), ("chol_total", "cholera_rate_1849", "income_total_2023"),
                ("hv_ahc", "house_value_pp_1849", "income_net_ahc_2023"), ("hv_total", "house_value_pp_1849", "income_total_2023"),
                ("hv_chol", "house_value_pp_1849", "cholera_rate_1849")]:
    rr, pp = stats.spearmanr(U[x], U[y])
    L[k] = {"rho": r1(rr, 2), "p": r1(pp, 3)}
    for bank in "NS":
        g = U[U.bank == bank]
        rr, pp = stats.spearmanr(g[x], g[y])
        L[k][bank] = {"rho": r1(rr, 2), "p": r1(pp, 2), "n": len(g)}
# permutation check of the house-value link, because units are few and unequal
rng = np.random.default_rng(1849)
obs = stats.spearmanr(U.house_value_pp_1849, U.income_total_2023)[0]
perm = [stats.spearmanr(rng.permutation(U.house_value_pp_1849.values), U.income_total_2023)[0] for _ in range(10000)]
L["hv_total"]["perm_p"] = r1(np.mean(np.abs(perm) >= abs(obs)), 3)
q = U.sort_values("cholera_rate_1849", ascending=False)
top, bot = q.head(8), q.tail(8)
w = lambda g, c: float((g[c] * g.pop_2021).sum() / g.pop_2021.sum())
L["worst8"] = {"units": list(top.unit), "rate_1849": r1(top.cholera_deaths_1849.sum() / top.pop_1849.sum() * 10000), "income_ahc": int(round(w(top, "income_net_ahc_2023"), -2)),
               "income_total": int(round(w(top, "income_total_2023"), -2))}
L["best8"] = {"units": list(bot.unit), "rate_1849": r1(bot.cholera_deaths_1849.sum() / bot.pop_1849.sum() * 10000), "income_ahc": int(round(w(bot, "income_net_ahc_2023"), -2)),
              "income_total": int(round(w(bot, "income_total_2023"), -2))}
L["london_income_ahc_all"] = int(round(w(Mi.rename(columns={"pop2021": "pop_2021"}), "income_net_ahc"), -2))
ex = {}
for u in ["Rotherhithe", "Bermondsey", "Wandsworth", "Bethnal Green", "Hampstead", "Chelsea", "Newington", "Paddington", "Lambeth", "Stepney"]:
    r = U[U.unit == u].iloc[0]
    ex[u] = {"rate_1849": float(r.cholera_rate_1849), "income_ahc": int(r.income_net_ahc_2023), "income_total": int(r.income_total_2023),
             "house_value_pp": float(r.house_value_pp_1849), "msoas": int(r.msoas_2021),
             "rank_income_ahc": int(U.income_net_ahc_2023.rank(ascending=False)[r.name]), "rank_rate": int(U.cholera_rate_1849.rank(ascending=False)[r.name]),
             "rank_house_value": int(U.house_value_pp_1849.rank(ascending=False)[r.name])}
L["examples"] = ex
L["richest_unit"] = U.loc[U.income_net_ahc_2023.idxmax()].unit
L["richest_ahc"] = int(U.income_net_ahc_2023.max())
L["poorest_unit"] = U.loc[U.income_net_ahc_2023.idxmin()].unit
L["poorest_ahc"] = int(U.income_net_ahc_2023.min())
L["rank_cholera_of_richest"] = int(U.cholera_rate_1849.rank(ascending=False)[U.income_net_ahc_2023.idxmax()])
L["rank_cholera_of_poorest"] = int(U.cholera_rate_1849.rank(ascending=False)[U.income_net_ahc_2023.idxmin()])
R["long"] = L

# ======================= history facts (Wikipedia, CC BY-SA 4.0) =======================
R["facts"] = {
    "england_wales_1848_49_deaths": 52000, "london_1849_deaths_wikipedia": 14137, "london_1832_deaths": 6536, "london_1853_54_deaths": 10739,
    "broad_street_deaths_wikipedia": 420, "broad_street_first_three_days": 127, "snow_born": 1813, "pump_handle_removed": "8 September 1854",
    "public_health_act": 1848, "east_end_1866_deaths": 5596,
    "snow_decidedly_nearer_other_pump": 10, "snow_families_preferred_broad": 5, "snow_children_school": 3, "snow_drank_pump_water": 61,
    "sources": {"england_wales_1848_49_deaths": "1846-1860 cholera pandemic", "london_1849_deaths_wikipedia": "History of cholera; 1846-1860 cholera pandemic",
                "london_1832_deaths": "History of cholera", "london_1853_54_deaths": "History of cholera", "broad_street_deaths_wikipedia": "1854 Broad Street cholera outbreak",
                "broad_street_first_three_days": "1854 Broad Street cholera outbreak", "snow_born": "John Snow", "pump_handle_removed": "1854 Broad Street cholera outbreak (quoting Snow 1855)",
                "public_health_act": "Public Health Act 1848", "east_end_1866_deaths": "History of cholera",
                "snow_decidedly_nearer_other_pump": "1854 Broad Street cholera outbreak (quoting Snow 1855)", "snow_families_preferred_broad": "same", "snow_children_school": "same", "snow_drank_pump_water": "same"},
}
R["facts"]["farr_share_of_wiki_london"] = r1(tot_d / 14137, 3)

json.dump(R, open(os.path.join(D, "results.json"), "w"), indent=1, ensure_ascii=False)

# ======================= compact site data =======================
units = json.load(open(os.path.join(D, "units_1849.geojson")))
site = {
    "districts": F[["district", "cholera_drate", "cholera_deaths", "popn", "elevation", "water", "region", "house_valpp"]].to_dict("records"),
    "units": units,
    "deaths": [[round(a, 6), round(b, 6), round(c_, 6), round(d_, 6), int(e_), int(f_), g_] for a, b, c_, d_, e_, f_, g_ in zip(
        deaths.lon, deaths.lat, pd.read_csv(os.path.join(D, "snow_1854_deaths.csv")).lon_stacked, pd.read_csv(os.path.join(D, "snow_1854_deaths.csv")).lat_stacked,
        deaths.dist_broad_m.round(), deaths.walk_broad_m.round(), deaths.nearest_pump_walk)],
    "pumps": pumps[["label_histdata", "street_today", "lon", "lat"]].values.tolist(),
    "streets": [[[round(x, 5), round(y, 5)] for x, y in fe["geometry"]["coordinates"]] for fe in streets],
    "thames": json.load(open(os.path.join(D, "thames.geojson")))["geometry"],
    "msoa": [[round(r.lon, 4), round(r.lat, 4), r.unit, int(r.income_net_ahc), r.MSOA21NM] for r in Mi.itertuples()],
}
json.dump(site, open(os.path.join(W, "site.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["water", "south", "broad", "long"]}, indent=0, default=str)[:6000])
