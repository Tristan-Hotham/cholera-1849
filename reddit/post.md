## Title

[OC] The hill or the water? London's 1849 cholera, district by district: Farr's 38 districts (14,007 deaths), Snow's Broad Street map, and whether the worst-hit districts are still the poorest (rank correlation with 2023 income: −0.07)

## Body (optional)

I rebuilt William Farr's 1849 cholera table for London's 38 registration districts and set it beside John Snow's evidence.

Farr's elevation law holds as a pattern: deaths fall steadily as the ground rises (rank correlation -0.81). But the low districts were the ones drinking Thames water from central London, and in south London houses on the two companies' water died at the same rate in 1849 (12.2 per 1,000) and at 13.5 against 3.6 in 1854. Half the 578 deaths on Snow's 1854 map were within 117 m of the Broad Street pump.

Caveat: I linked 1849 districts to today's areas through named places, so the shapes are approximate.

Interactive version: https://tristan-hotham.github.io/cholera-1849/

## Source comment

Source: William Farr (1852), Report on the Mortality of Cholera in England, 1848-49, as tabulated by Bingham, Verlander and Cheal (2004) in the HistData R package (GPL); Snow (1855) Tables IX and XII and Simon (1856) Table II, transcribed by Thomas Coleman in SnowCholera (BSD 2-Clause); Snow's Broad Street map digitised by Dodson and Tobler and georeferenced in Peter Li's cholera R package (GPL); ONS income estimates for small areas FYE2023 and Census 2021 (Open Government Licence v3.0); OS Open Names and OS Open Rivers (OGL v3, contains OS data © Crown copyright and database right 2026).

Tools: Python (pandas, NumPy, SciPy, statsmodels, NetworkX, Shapely, matplotlib).

Interactive: https://tristan-hotham.github.io/cholera-1849/
Blog post: https://blog.tristanhotham.com/2026/10/27/cholera-1849/
Paper: https://doi.org/10.5281/zenodo.23689968
