"""Prediction market odds from Polymarket and Kalshi public market data (expansion item 3).

Both platforms were confirmed on the live service on Oct 5, 2026: no key needed for market data.
  Polymarket: gamma-api.polymarket.com (search, markets) and clob.polymarket.com/prices-history
  Kalshi:     api.elections.kalshi.com/trade-api/v2 (series, markets, candlesticks)

Privacy rule: only market-level fields in KEEP lists are ever stored. Platform records also contain
addresses (e.g. market maker, resolver); those are never read into our tables. Activity is reported
in aggregate only, never by account or wallet.

This is market monitoring and research, not betting advice.
"""

import datetime as dt
import json
import re
import time

import requests

POLY_GAMMA = "https://gamma-api.polymarket.com"
POLY_CLOB = "https://clob.polymarket.com"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"

# ---------------------------------------------------------------- selection rule (fixed in advance)
ACTIVE_FROM = dt.date(2026, 1, 1)   # market must close on or after this date
MIN_VOLUME = 10_000                 # dollars (Polymarket) or $1 contracts (Kalshi)
MIN_LIFETIME_DAYS = 7               # one-day markets have no history to compare against

OIL_PRICE = re.compile(r"\bwti\b|\bbrent\b|price of oil|oil price|crude oil \(cl\)", re.I)
GULF_CONFLICT = re.compile(
    r"hormuz|bab.al.mandab|ceasefire|peace deal|strategic oil reserve|iea.*reserve"
    r"|\biran\b.*\b(strikes?|attacks?|war|conflict|blockade|agreement|deal|mou|meeting|meet|invade|military)\b"
    r"|\b(strikes?|attacks?|invade|blockade|military action)\b.*\biran\b", re.I)
EXCLUDE = re.compile(
    r"hezbollah|gaza|lebanon|ukraine|russia|world cup|election|pahlavi|leader|democracy|visit|rename"
    r"|mention|truths?\b|embassy|cpi|imports|ofac|outperform|export ban|production", re.I)

KALSHI_SKIP_FREQUENCIES = {"daily", "hourly", "fifteen_min"}
KALSHI_SKIP_CATEGORIES = {"Mentions", "Entertainment", "Sports"}
POLY_QUERIES = ["iran", "hormuz", "ceasefire", "crude oil", "wti", "brent", "oil price"]


def topic_of(title):
    """'oil_price', 'gulf_conflict', or None if the title is out of scope."""
    if not title or EXCLUDE.search(title):
        return None
    if OIL_PRICE.search(title):
        return "oil_price"
    if GULF_CONFLICT.search(title):
        return "gulf_conflict"
    return None


def in_scope(title, volume, opened, closes):
    """The full selection rule: topic, volume floor, active in 2026 or later, open at least a week."""
    return (topic_of(title) is not None
            and volume is not None and volume >= MIN_VOLUME
            and closes is not None and closes >= ACTIVE_FROM
            and opened is not None and (closes - opened).days >= MIN_LIFETIME_DAYS)


# ---------------------------------------------------------------- small helpers
def _date(text):
    """'2026-05-11T13:03:57Z' -> date(2026, 5, 11). None stays None."""
    return dt.date.fromisoformat(text[:10]) if text else None


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get(url, params=None, pause=0.15):
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    time.sleep(pause)  # stay well under both platforms' limits
    return resp.json()


# ---------------------------------------------------------------- Polymarket
def parse_poly_market(m, event_title):
    """Turn one Polymarket market record into our market row. Only these fields are kept."""
    outcomes = json.loads(m.get("outcomes") or "[]")
    prices = json.loads(m.get("outcomePrices") or "[]")
    tokens = json.loads(m.get("clobTokenIds") or "[]")
    title = f"{event_title} | {m.get('question', '')}"
    return {
        "market_key": f"polymarket:{m['id']}",
        "platform": "polymarket",
        "market_id": str(m["id"]),
        "event_title": event_title,
        "question": m.get("question"),
        "outcome": outcomes[0] if outcomes else None,   # price is the chance of this outcome
        "topic": topic_of(event_title) or topic_of(m.get("question", "")),
        "opened": _date(m.get("startDate") or m.get("createdAt")),
        "closes": _date(m.get("endDate")),
        "status": "closed" if m.get("closed") else "open",
        "result": None,
        "total_volume": _num(m.get("volumeNum") or m.get("volume")),
        "volume_unit": "USD",
        "_title": title,
        "_token": tokens[0] if tokens else None,
        "_price_now": _num(prices[0]) if prices else None,
    }


def poly_search_events(query, status, max_pages=20):
    events, page = [], 1
    while page <= max_pages:
        d = _get(f"{POLY_GAMMA}/public-search",
                 {"q": query, "limit_per_type": 50, "page": page, "events_status": status})
        events.extend(d.get("events", []))
        if not d.get("pagination", {}).get("hasMore"):
            break
        page += 1
    return events


def poly_markets():
    """Every Polymarket market in scope, found through the search queries, deduplicated."""
    found = {}
    for query in POLY_QUERIES:
        for status in ["active", "closed"]:
            for event in poly_search_events(query, status):
                title = event.get("title", "")
                if topic_of(title) is None:
                    continue
                for m in event.get("markets") or []:
                    row = parse_poly_market(m, title)
                    if row["topic"] and in_scope(row["_title"], row["total_volume"], row["opened"], row["closes"]):
                        found[row["market_key"]] = row
    return list(found.values())


def parse_poly_history(points):
    """[{t: unix seconds, p: price}] -> {date: last price that day}."""
    by_day = {}
    for point in sorted(points, key=lambda x: x["t"]):
        by_day[dt.datetime.fromtimestamp(point["t"], dt.UTC).date()] = float(point["p"])
    return by_day


def poly_history(token):
    d = _get(f"{POLY_CLOB}/prices-history", {"market": token, "interval": "max", "fidelity": 1440})
    return parse_poly_history(d.get("history", []))


# ---------------------------------------------------------------- Kalshi
def kalshi_series():
    """Kalshi series whose title is in scope, excluding daily/hourly price series."""
    d = _get(f"{KALSHI}/series")
    return [s for s in d.get("series", [])
            if topic_of(s.get("title", "")) is not None
            and s.get("frequency") not in KALSHI_SKIP_FREQUENCIES
            and s.get("category") not in KALSHI_SKIP_CATEGORIES]


def parse_kalshi_market(m, series):
    title = f"{series['title']} | {m.get('title', '')} {m.get('yes_sub_title', '')}".strip()
    status = m.get("status")
    return {
        "market_key": f"kalshi:{m['ticker']}",
        "platform": "kalshi",
        "market_id": m["ticker"],
        "event_title": series["title"],
        "question": f"{m.get('title', '')} {m.get('yes_sub_title', '')}".strip(),
        "outcome": "Yes",
        "topic": topic_of(series["title"]),
        "opened": _date(m.get("open_time")),
        "closes": _date(m.get("close_time")),
        "status": "open" if status == "active" else "closed",
        "result": m.get("result") or None,
        "total_volume": _num(m.get("volume_fp") or m.get("volume")),
        "volume_unit": "contracts",
        "_title": title,
        "_series": series["ticker"],
        "_price_now": _num(m.get("last_price_dollars")),
    }


def kalshi_markets():
    found = {}
    for series in kalshi_series():
        cursor = None
        while True:
            params = {"series_ticker": series["ticker"], "limit": 1000}
            if cursor:
                params["cursor"] = cursor
            d = _get(f"{KALSHI}/markets", params)
            for m in d.get("markets", []):
                row = parse_kalshi_market(m, series)
                if in_scope(series["title"], row["total_volume"], row["opened"], row["closes"]):
                    found[row["market_key"]] = row
            cursor = d.get("cursor")
            if not cursor:
                break
    return list(found.values())


def parse_kalshi_candles(candles):
    """Daily candles -> {date: (closing price, contracts traded that day)}."""
    out = {}
    for c in candles:
        day = dt.datetime.fromtimestamp(c["end_period_ts"], dt.UTC).date()
        price = _num((c.get("price") or {}).get("close_dollars"))
        out[day] = (price, _num(c.get("volume_fp") or c.get("volume")))
    return out


def kalshi_history(series_ticker, ticker, opened, closes):
    start = dt.datetime.combine(opened or ACTIVE_FROM, dt.time(), dt.UTC)
    end = min(dt.datetime.now(dt.UTC), dt.datetime.combine(closes, dt.time(23, 59), dt.UTC))
    d = _get(f"{KALSHI}/series/{series_ticker}/markets/{ticker}/candlesticks",
             {"start_ts": int(start.timestamp()), "end_ts": int(end.timestamp()), "period_interval": 1440})
    return parse_kalshi_candles(d.get("candlesticks", []))
