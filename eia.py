"""Talk to the EIA API (version 2).

Data source: U.S. Energy Information Administration.
"""

from pathlib import Path

import requests

BASE_URL = "https://api.eia.gov/v2/"
ENV_FILE = Path(__file__).parent / ".env"


def load_api_key():
    """Read EIA_API_KEY from the .env file next to this script."""
    if not ENV_FILE.exists():
        raise RuntimeError(".env not found. Add a line EIA_API_KEY=your_key")
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("EIA_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    raise RuntimeError(".env has no EIA_API_KEY line")


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
