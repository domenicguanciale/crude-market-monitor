"""Download prediction market odds (Polymarket, Kalshi) into DuckDB. Expansion item 3.

All dates are US Eastern days: a reading dated D is the market as of the end of D, New York time.

Run: .venv/bin/python fetch_markets.py
Safe to re-run, and meant to be re-run: rows are added or updated, never deleted, so a market
that closes and drops off a platform's list keeps its history here. Each run also saves today's
all-time volume, so daily Polymarket volume can be measured from the day this starts running.
"""

import datetime as dt

import pandas as pd

import db
import prediction_markets as pm

MARKET_COLUMNS = ["market_key", "platform", "market_id", "event_title", "question", "outcome", "topic",
                  "opened", "closes", "status", "result", "total_volume", "volume_unit", "last_fetched"]
READING_COLUMNS = ["market_key", "reading_date", "price", "volume", "total_volume", "fetched_at"]


def save_markets(con, markets):
    """Add new markets; update status, result and volume of known ones."""
    df = pd.DataFrame(markets)[[c for c in MARKET_COLUMNS if c != "last_fetched"]]
    df["last_fetched"] = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    con.execute(f"""
        INSERT INTO prediction_market SELECT {', '.join(MARKET_COLUMNS)} FROM df
        ON CONFLICT (market_key) DO UPDATE SET
            event_title = EXCLUDED.event_title, question = EXCLUDED.question, topic = EXCLUDED.topic,
            closes = EXCLUDED.closes, status = EXCLUDED.status,
            result = COALESCE(EXCLUDED.result, result),
            total_volume = COALESCE(EXCLUDED.total_volume, total_volume),
            last_fetched = EXCLUDED.last_fetched
    """)


def save_readings(con, readings):
    """Add new daily readings; fill in values on existing ones without erasing what is there."""
    if not readings:
        return
    df = pd.DataFrame(readings, columns=READING_COLUMNS)
    con.execute(f"""
        INSERT INTO market_reading SELECT {', '.join(READING_COLUMNS)} FROM df
        ON CONFLICT (market_key, reading_date) DO UPDATE SET
            price = COALESCE(EXCLUDED.price, price),
            volume = COALESCE(EXCLUDED.volume, volume),
            total_volume = COALESCE(EXCLUDED.total_volume, total_volume),
            fetched_at = EXCLUDED.fetched_at
    """)


def readings_for(market, history, now):
    """History rows plus today's snapshot, merged so each day appears exactly once.

    Today usually appears in both the history and the snapshot. Two rows for one day in a single
    save would collide and one would be lost, so the snapshot is folded into today's row: the
    snapshot price is the more recent one, and only the snapshot has the all-time volume.
    """
    by_day = {}
    for day, value in history.items():
        price, volume = value if isinstance(value, tuple) else (value, None)
        by_day[day] = [price, volume, None]
    today = pm.today_eastern()
    price, volume, _ = by_day.get(today, [None, None, None])
    by_day[today] = [market["_price_now"] if market["_price_now"] is not None else price,
                     volume, market["total_volume"]]
    return [[market["market_key"], day, p, v, t, now] for day, (p, v, t) in sorted(by_day.items())]


RECHECK_DAYS = 3  # re-fetch the last few saved days so late trades and today's partial day get updated


def resume_from(con, markets):
    """For each market, fetch history from a few days before its last saved reading (or from its open)."""
    last = dict(con.execute("SELECT market_key, max(reading_date) FROM market_reading GROUP BY 1").fetchall())
    for m in markets:
        if m["market_key"] in last:
            m["opened"] = max(m["opened"] or last[m["market_key"]],
                              last[m["market_key"]] - dt.timedelta(days=RECHECK_DAYS))
    return markets


def run_platform(con, name, markets, history_of):
    now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    print(f"{name}: {len(markets)} markets in scope", flush=True)
    if not markets:
        return
    save_markets(con, markets)   # saves the real open date before resume_from shortens the fetch
    markets = resume_from(con, markets)
    readings, failed = [], 0
    for i, m in enumerate(markets, 1):
        try:
            readings.extend(readings_for(m, history_of(m), now))
        except Exception as e:  # one bad market must not stop the run
            failed += 1
            status = getattr(getattr(e, "response", None), "status_code", "")
            print(f"  skipped {m['market_key']}: {type(e).__name__} {status}")
        if i % 100 == 0:
            print(f"  {i} of {len(markets)}", flush=True)
    save_readings(con, readings)
    print(f"  saved {len(readings)} daily readings, {failed} markets skipped")


def main():
    con = db.connect()
    run_platform(con, "Polymarket", pm.poly_markets(),
                 lambda m: pm.poly_history(m["_token"], m["opened"], m["closes"]) if m["_token"] else {})
    run_platform(con, "Kalshi", pm.kalshi_markets(),
                 lambda m: pm.kalshi_history(m["_series"], m["market_id"], m["opened"], m["closes"]))
    print(con.execute("""
        SELECT platform, topic, count(DISTINCT m.market_key) AS markets, count(*) AS readings,
               min(reading_date) AS first_day, max(reading_date) AS last_day
        FROM prediction_market m JOIN market_reading r USING (market_key)
        GROUP BY 1, 2 ORDER BY 1, 2""").df().to_string(index=False))


if __name__ == "__main__":
    main()
