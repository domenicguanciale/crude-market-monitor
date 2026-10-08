"""Refresh every data source, recalculate, and rebuild the showcase and the Monday read, in order.

Run: .venv/bin/python update.py            everything
     .venv/bin/python update.py --skip-markets   everything except the prediction market download

Each step is a separate script that can also be run on its own. A failing step is reported and the
rest continue, so one unavailable source does not block the others.
"""

import subprocess
import sys
import time

STEPS = [
    ("EIA weekly data and prices", ["fetch.py"]),
    ("Five-year comparison, score, spread, futures curve", ["calculate.py"]),
    ("Spike catalog and realized volatility", ["spikes.py"]),
    ("CFTC positioning (legacy and disaggregated)", ["cot.py"]),
    ("US retail gasoline and diesel", ["retail_fuel.py"]),
    ("FRED daily series (needs FRED_API_KEY)", ["fred.py"]),
    ("Geopolitical Risk Index", ["gpr.py"]),
    ("Chokepoint transits (IMF PortWatch)", ["chokepoints.py"]),
    ("Prediction markets", ["fetch_markets.py"]),
    ("Dataset source registry", ["sources.py"]),
    ("Event tables", ["events.py"]),
    ("Showcase data (publishable series, hand-checked events)", ["export_showcase.py"]),
    ("3D page data", ["export_3d.py"]),
    ("3D lanes stay in open water", ["tools/check_lanes.py"]),
    ("Monday read", ["monday_summary.py"]),
    ("Reconcile spot numbers with their sources", ["tools/reconcile.py"]),
]


def main():
    skip_markets = "--skip-markets" in sys.argv
    failed = []
    for name, script in STEPS:
        if skip_markets and script == ["fetch_markets.py"]:
            continue
        print(f"\n=== {name} ===", flush=True)
        t = time.time()
        result = subprocess.run([sys.executable, *script])
        status = "ok" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        print(f"--- {status}, {time.time() - t:.0f}s", flush=True)
        if result.returncode != 0:
            failed.append(name)
    print("\nAll steps finished." if not failed else f"\nFailed steps: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
