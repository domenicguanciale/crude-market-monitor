"""Check that every schematic shipping lane in export_3d.py stays in open water on the coastline in region_land.json.

Run from the project folder: .venv/bin/python tools/check_lanes.py
Exits with an error if any lane crosses land. Run it after changing a waypoint.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import export_3d

LAND = json.loads(export_3d.REGION.read_text())["polygons"]


def inside(x, y, ring):
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def on_land(lon, lat):
    return any(inside(lon, lat, p[0]) and not any(inside(lon, lat, h) for h in p[1:]) for p in LAND)


def hits(points):
    bad = []
    for (la1, lo1), (la2, lo2) in zip(points, points[1:]):
        n = int(max(abs(la1 - la2), abs(lo1 - lo2)) / 0.01) + 1
        for k in range(n + 1):
            la, lo = la1 + (la2 - la1) * k / n, lo1 + (lo2 - lo1) * k / n
            if on_land(lo, la):
                bad.append((round(la, 2), round(lo, 2)))
    return bad


problems = {"trunk": hits(export_3d.TRUNK)}
for key, (_, pts, _) in export_3d.FEEDERS.items():
    join = export_3d.TRUNK[2:] if key == "iran" else export_3d.TRUNK[:1]
    problems[key] = hits(pts + join)
for name, bad in problems.items():
    print(f"{name:<9} {'ok' if not bad else f'{len(bad)} points on land, first {bad[0]}'}")
sys.exit(1 if any(problems.values()) else 0)
