"""Run once: extract label points for countries missing from the 110m Natural Earth file (writes data/ne_label_points_extra.csv).

Needs ne_10m_admin_0_label_points.geojson from https://github.com/nvkelso/natural-earth-vector (public domain), passed
as the first argument. For countries with several points (islands), keeps the one with the lowest scalerank
(Natural Earth's most prominent), then the first listed.
Usage: .venv/bin/python tools/make_label_points.py /path/to/ne_10m_admin_0_label_points.geojson
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
base = set()
for f in json.loads((ROOT / "data" / "ne_110m_admin_0_countries.geojson").read_text())["features"]:
    p = f["properties"]
    base |= {p["ADM0_A3"], p["ISO_A3"]}
best = {}
for f in json.loads(Path(sys.argv[1]).read_text())["features"]:
    code, rank = f["properties"].get("sr_adm0_a3"), f["properties"].get("scalerank", 99)
    if code and code not in base and (code not in best or rank < best[code][0]):
        best[code] = (rank, f["geometry"]["coordinates"])
with open(ROOT / "data" / "ne_label_points_extra.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["iso3", "label_lat", "label_lon"])
    for code in sorted(best):
        lon, lat = best[code][1]
        w.writerow([code, round(lat, 4), round(lon, 4)])
print(len(best), "extra label points written")
