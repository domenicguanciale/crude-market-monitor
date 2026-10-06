"""Talk to the EIA API (version 2).

Data source: U.S. Energy Information Administration.
"""

import time
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.eia.gov/v2/"
ENV_FILE = Path(__file__).parent / ".env"
PAGE_SIZE = 5000  # EIA's maximum rows per response


def load_api_key(name="EIA_API_KEY"):
    """Read a key (EIA_API_KEY by default, or e.g. FRED_API_KEY) from the .env file next to this script."""
    if not ENV_FILE.exists():
        raise RuntimeError(f".env not found. Add a line {name}=your_key")
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{name}="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    raise RuntimeError(f".env has no {name} line")


def get(route, params=None):
    """Request one route from the API and return the 'response' part of the JSON.

    The key is added here and kept out of any error message.
    """
    key = load_api_key()
    query = dict(params or {})
    query["api_key"] = key
    resp = requests.get(BASE_URL + route, params=query, timeout=30)
    if resp.status_code != 200:
        # Report the route, not the full URL, so the key is never printed
        body = resp.text[:300].replace(key, "***")
        raise RuntimeError(f"EIA returned {resp.status_code} for route '{route}': {body}")
    return resp.json()["response"]


def fetch_series(route, series_id, frequency):
    """Download every row of one series, page by page, as a two-column table: period, value."""
    rows, offset = [], 0
    while True:
        resp = get(f"{route}/data/", {
            "frequency": frequency,
            "data[]": "value",
            "facets[series][]": series_id,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": PAGE_SIZE,
        })
        rows.extend(resp["data"])
        offset += PAGE_SIZE
        if offset >= int(resp["total"]):
            break
        time.sleep(0.3)  # stay well under EIA's informal limit of 5 requests a second
    df = pd.DataFrame(rows, columns=["period", "value"])
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # EIA sends numbers as text
    return df.dropna(subset=["value"]).reset_index(drop=True)
