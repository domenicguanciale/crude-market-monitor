"""Confirm each series ID exists under its route on the live EIA API.

Run: .venv/bin/python check_routes.py
Nothing is fetched for real until every row here says OK.
"""

import eia

# Candidate route for each series, from DATA_SPEC.md section 3
SERIES_ROUTES = {
    "RWTC": "petroleum/pri/spt",       # WTI spot price
    "RBRTE": "petroleum/pri/spt",      # Brent spot price
    "WCESTUS1": "petroleum/stoc/wstk",  # Crude stocks excl. SPR
    "WDISTUS1": "petroleum/stoc/wstk",  # Distillate stocks
    "WPULEUS3": "petroleum/pnp/wiup",   # Refinery utilization
    "WCRFPUS2": "petroleum/sum/sndw",   # Crude production
    "WCREXUS2": "petroleum/move/wkly",  # Crude exports
}


def series_on_route(route):
    """Return {series_id: name} for every series EIA lists under a route."""
    facets = eia.get(f"{route}/facet/series")["facets"]
    return {f["id"]: f.get("name", "") for f in facets}


def frequencies_on_route(route):
    """Return the frequencies (weekly, daily, ...) a route offers."""
    meta = eia.get(route)
    return [f["id"] for f in meta.get("frequency", [])]


def main():
    cache = {}
    all_ok = True
    for series_id, route in SERIES_ROUTES.items():
        if route not in cache:
            cache[route] = (series_on_route(route), frequencies_on_route(route))
        listed, freqs = cache[route]
        if series_id in listed:
            print(f"OK       {series_id:<9} {route:<20} {listed[series_id]}")
        else:
            all_ok = False
            print(f"MISSING  {series_id:<9} {route:<20} not listed")
    print()
    for route, (listed, freqs) in cache.items():
        print(f"{route:<20} frequencies: {', '.join(freqs)}  ({len(listed)} series)")
    print("\nAll routes confirmed." if all_ok else "\nSome series not found. Do not fetch yet.")


if __name__ == "__main__":
    main()
