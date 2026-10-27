# Cholera 1849: low ground, bad water and a long shadow

William Farr's 1849 cholera figures for London's 38 registration districts, John Snow's 1854 Broad Street map, and a test of whether the worst-hit districts are still the poorest today.

**Interactive version:** https://tristan-hotham.github.io/cholera-1849/
**Paper:** https://doi.org/10.5281/zenodo.23689968
**Blog post:** https://blog.tristanhotham.com/2026/10/27/cholera-1849/

A data study by Dr Tristan Hotham (Independent researcher).

## Headline results

- Farr's 38 districts recorded {{farr.deaths|int}} cholera deaths in 1849 among {{farr.population|int}} people ({{farr.rate_per_10000|f1}} per 10,000). Rotherhithe lost {{farr.worst.0.rate|int}} per 10,000; Hampstead {{farr.best.0.rate|int}}.
- Farr's elevation law holds as a pattern: the rank correlation between height and death rate is {{farr.elev_spearman|f2}}. Districts below 20 feet lost {{farr.bands.0.rate|f1}} per 10,000; those at 100 feet or more, {{farr.bands.4.rate|f1}}.
- Height and water are tangled. Districts on Thames water from Battersea to Waterloo lost {{water.groups.0.rate|f1}} per 10,000, those on Thames water from Kew and Hammersmith {{water.groups.2.rate|f1}}. Height explains {{water.r2.elev|pct0}} of the variation in logged death rates, water {{water.r2.water|pct0}}, both {{water.r2.both|pct0}}.
- South London settles it: houses on Lambeth and on Southwark and Vauxhall water died at the same rate in 1848 to 1849 ({{south.simon.lambeth_1849|f1}} per 1,000), but in 1853 to 1854 at {{south.simon.lambeth_1854|f1}} and {{south.simon.southwark_1854|f1}} (Simon 1856).
- Broad Street, 1854: half the {{broad.deaths_on_map|int}} deaths on Snow's map were within {{broad.median_dist_m|int}} m of the pump; {{broad.share_nearest_broad_walk|pct0}} were nearer, on foot, to Broad Street than to any other pump.
- The long shadow: across {{long.n_units|int}} areas there is no link between the 1849 death rate and 2023 income after housing costs (rank correlation {{long.chol_ahc.rho|f2}}). The 1849 value of houses per person does line up with 2023 total household income ({{long.hv_total.rho|f2}}, p = {{long.hv_total.p|f2}}).

## Files

- `index.html`: the interactive page (maps, charts, table). Data embedded; works as a single file.
- `header.png`: social card (1200 by 630).
- `data/farr_1849_districts.csv`: Farr's 38 districts (deaths, population, elevation, water source, housing figures), from HistData `Cholera`.
- `data/farr_1849_daily.csv`: daily cholera and diarrhoea deaths, England and Wales, 1849, from HistData `CholeraDeaths1849`.
- `data/snow_1854_deaths.csv`, `snow_1854_addresses.csv`, `snow_1854_pumps.csv`, `snow_1854_streets.geojson`: Snow's map, georeferenced, from the cholera R package.
- `data/snow_1854_deaths_distances.csv`: each death with straight and walking distance to the Broad Street pump and its nearest pump on foot.
- `data/snow_1854_dates.csv`: fatal attacks and deaths by day (Snow 1855 Table 1, via HistData `Snow.dates`).
- `data/snow_1855_table_ix.csv`, `snow_1855_table_xii.csv`, `simon_1856_table_ii.csv`: Snow's and Simon's water company tables, from Thomas Coleman's SnowCholera.
- `data/district_seeds.csv`: the {{long.n_seeds|int}} named places (OS Open Names) used to place each 1849 district.
- `data/msoa_to_1849.csv`: every MSOA (2021) in the thirteen inner London boroughs with its 2021 population, FYE2023 income and assigned 1849 area.
- `data/units_then_now.csv` and `data/units_1849.geojson`: the {{long.n_units|int}} areas with 1849 and 2023 figures, and their approximate shapes.
- `data/thames.geojson`: the River Thames in London (OS Open Rivers).
- `data/results.json`: every number quoted on the page, in the paper and the blog post.
- `code/01_extract.py` to `code/05_header.py`: the pipeline. `release/`: paper, blog and Zenodo files. `reddit/`: the collage.

## How to rerun

```
git clone https://github.com/friendly/HistData
git clone https://github.com/lindbrook/cholera
git clone https://github.com/tscoleman/SnowCholera
python3 code/01_extract.py HistData cholera SnowCholera
python3 code/02_link_today.py
python3 code/03_analyse.py
python3 code/04_build_site.py
python3 code/05_header.py
```

Steps 1 and 2 also read OS Open Rivers, OS Open Names, the ONS MSOA centroids, Census 2021 TS001 and the ONS FYE2023 income workbook from local paths set at the top of each script. Needs Python 3 with pandas, numpy, scipy, statsmodels, networkx, shapely, pyproj, pyreadr, openpyxl, matplotlib and playwright.

## Method in brief and known limits

- Death rates are per 10,000 people in mid 1849, from Farr's report as tabulated by Bingham, Verlander and Cheal (2004). The 38 districts total {{farr.deaths|int}}, a little below the {{facts.london_1849_deaths_wikipedia|int}} often quoted for London.
- Regressions use the log death rate, weighted by population, with height as log(feet + 3). Farr's three water groups are coarse.
- Walking distances run along the streets of Snow's map. There are no population figures for the map, so ring densities are deaths per hectare, not rates.
- There is no open boundary file for the 1849 districts that I could use. Each 2021 MSOA goes to the 1849 district with the nearest named place on the same bank of the Thames; MSOAs more than {{long.max_seed_km|int}} km from any named place are dropped ({{long.n_msoas_dropped|int}}). Small districts are merged where MSOAs are too coarse (City, Borough, West End). Shapes are approximate.
- I found no open digital copy of Farr's district table for all of England and Wales, so the study is London-centred.

## Sources and licences

- HistData R package (Friendly and others), https://github.com/friendly/HistData, GPL. `Cholera` from Bingham, P., Verlander, N.Q. and Cheal, M.J. (2004) Public Health 118(6), 387 to 394, based on Farr (1852) Report on the Mortality of Cholera in England, 1848-49. `CholeraDeaths1849` transcribed by James Riley. `Snow.dates` from Snow (1855).
- cholera R package (Peter Li), https://github.com/lindbrook/cholera, GPL (>= 2). Snow's map digitised by Rusty Dodson and Waldo Tobler (1992), georeferenced by the package.
- SnowCholera (Thomas Coleman), https://github.com/tscoleman/SnowCholera, BSD 2-Clause: transcriptions of Snow (1855) Tables IX and XII and Simon (1856) Table II.
- Office for National Statistics: income estimates for small areas, England and Wales, FYE2023; Census 2021 TS001; MSOA 2021 population-weighted centroids; MSOA to BUA lookup. Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Ordnance Survey: OS Open Names and OS Open Rivers, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Historical background: English Wikipedia (CC BY-SA 4.0), articles on John Snow, William Farr, the 1854 Broad Street cholera outbreak, the 1846 to 1860 cholera pandemic, the history of cholera and the Public Health Act 1848.
- Base map tiles on the page © Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community.

Licences here: code MIT (see `LICENSE`); page text CC BY 4.0; data files derived from HistData or the cholera package are GPL as their sources are, files from SnowCholera are BSD 2-Clause, and files from ONS and OS data are Open Government Licence v3.0.

## Citation

Hotham, T. (2026) Cholera 1849: low ground, bad water and a long shadow. Zenodo. https://doi.org/10.5281/zenodo.23689968

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
