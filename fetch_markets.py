"""Download prediction market odds (Polymarket, Kalshi) into DuckDB. Expansion item 3.

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
    """History rows plus today's snapshot row for one market."""
    rows = []
    for day, value in history.items():
        price, volume = value if isinstance(value, tuple) else (value, None)
        rows.append([market["market_key"], day, price, volume, None, now])
    rows.append([market["market_key"], now.date(), market["_price_now"], None, market["total_volume"], now])
    return rows


def run_platform(con, name, markets, history_of):
    now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    print(f"{name}: {len(markets)} markets in scope")
    if not markets:
        return
    save_markets(con, markets)
    readings, failed = [], 0
    for i, m in enumerate(markets, 1):
        try:
            readings.extend(readings_for(m, history_of(m), now))
        except Exception as e:  # one bad market must not stop the run
            failed += 1
            print(f"  skipped {m['market_key']}: {type(e).__name__}")
        if i % 100 == 0:
            print(f"  {i} of {len(markets)}")
    save_readings(con, readings)
    print(f"  saved {len(readings)} daily readings, {failed} markets skipped")


def main():
    con = db.connect()
    run_platform(con, "Polymarket", pm.poly_markets(),
                 lambda m: pm.poly_history(m["_token"]) if m["_token"] else {})
    run_platform(con, "Kalshi", pm.kalshi_markets(),
                 lambda m: pm.kalshi_history(m["_series"], m["market_id"], m["opened"], m["closes"]))
    print(con.execute("""
        SELECT platform, topic, count(DISTINCT m.market_key) AS markets, count(*) AS readings,
               min(reading_date) AS first_day, max(reading_date) AS last_day
        FROM prediction_market m JOIN market_reading r USING (market_key)
        GROUP BY 1, 2 ORDER BY 1, 2""").df().to_string(index=False))


if __name__ == "__main__":
    main()
