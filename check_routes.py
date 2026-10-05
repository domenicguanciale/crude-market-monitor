"""Confirm each series ID exists under its route on the live EIA API, and how current it is.

Run: .venv/bin/python check_routes.py
Nothing is fetched for real until every row here says OK.
"""

import datetime as dt

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
    "RCLC1": "petroleum/pri/fut",       # WTI futures, contract 1 (history only)
    "RCLC4": "petroleum/pri/fut",       # WTI futures, contract 4 (history only)
}

# Series EIA stopped updating. Used for history only, never as a live gauge.
HISTORY_ONLY = {"RCLC1", "RCLC4"}

# A live series whose latest value is older than this is flagged STALE
STALE_AFTER_DAYS = 30


def series_on_route(route):
    """Return {series_id: name} for every series EIA lists under a route."""
    facets = eia.get(f"{route}/facet/series")["facets"]
    return {f["id"]: f.get("name", "") for f in facets}


def latest_date(route, series_id):
    """The most recent date EIA has a value for. Being listed does not mean being current."""
    frequency = "daily" if route.startswith("petroleum/pri") else "weekly"
    resp = eia.get(f"{route}/data/", {
        "frequency": frequency, "data[]": "value", "facets[series][]": series_id,
        "sort[0][column]": "period", "sort[0][direction]": "desc", "length": 1,
    })
    return dt.date.fromisoformat(resp["data"][0]["period"]) if resp["data"] else None


def coverage_status(series_id, last, today):
    """OK if current, HISTORY if a known history-only series, STALE if a live series stopped updating."""
    if series_id in HISTORY_ONLY:
        return "HISTORY"
    if last is None or (today - last).days > STALE_AFTER_DAYS:
        return "STALE"
    return "OK"


def main():
    listed_by_route = {}
    today = dt.date.today()
    all_ok = True
    for series_id, route in SERIES_ROUTES.items():
        if route not in listed_by_route:
            listed_by_route[route] = series_on_route(route)
        listed = listed_by_route[route]
        if series_id not in listed:
            all_ok = False
            print(f"MISSING  {series_id:<9} {route:<20} not listed")
            continue
        last = latest_date(route, series_id)
        status = coverage_status(series_id, last, today)
        all_ok = all_ok and status != "STALE"
        print(f"{status:<8} {series_id:<9} {route:<20} latest {last}  {listed[series_id]}")
    print("\nAll routes confirmed and current." if all_ok else "\nSome series missing or stale. Do not use them as live data.")


if __name__ == "__main__":
    main()
