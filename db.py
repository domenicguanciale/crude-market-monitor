"""The DuckDB database: one table per object type in ONTOLOGY.md."""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "crude_monitor.duckdb"

SCHEMA = """
-- Facility: a field, pipeline, terminal, refinery or shipping route (filled in version 2)
CREATE TABLE IF NOT EXISTS facility (
    facility_id     VARCHAR PRIMARY KEY,
    name            VARCHAR NOT NULL,
    type            VARCHAR,          -- field, pipeline, terminal, refinery, route
    country         VARCHAR,
    capacity_bpd    DOUBLE            -- barrels per day
);

-- Disruption event: something that took supply offline or threatened to (filled in version 2)
CREATE TABLE IF NOT EXISTS disruption_event (
    event_id        VARCHAR PRIMARY KEY,   -- E01, E02, ... as in EVENTS_STARTER.csv
    event_name      VARCHAR NOT NULL,
    event_date      DATE,
    day_zero        DATE,             -- first trading day on or after the event
    cause           VARCHAR,
    bpd_offline     DOUBLE,           -- barrels per day offline
    physical_loss   BOOLEAN,          -- were barrels actually lost, or only at risk?
    facility_id     VARCHAR REFERENCES facility (facility_id),
    week_ending     DATE,             -- links the event to its weekly_reading
    hand_checked    BOOLEAN DEFAULT FALSE,  -- only the user sets this; unchecked rows are never used downstream
    episode         VARCHAR           -- e.g. 'iran_war_2026' for sub-events of one episode
);

-- Source: one citation backing one disruption event (filled in version 2)
CREATE TABLE IF NOT EXISTS source (
    source_id       VARCHAR PRIMARY KEY,
    event_id        VARCHAR REFERENCES disruption_event (event_id),
    publisher       VARCHAR,
    url             VARCHAR NOT NULL,
    published_date  DATE
);

-- Price series: daily spot prices, one row per benchmark per day
CREATE TABLE IF NOT EXISTS price_series (
    benchmark       VARCHAR NOT NULL,      -- 'WTI', 'Brent', 'WTI future 1', 'WTI future 4'
    price_date      DATE    NOT NULL,
    price           DOUBLE  NOT NULL,      -- dollars per barrel
    PRIMARY KEY (benchmark, price_date)
);

-- Weekly reading: one row per EIA week (weeks end on Friday)
CREATE TABLE IF NOT EXISTS weekly_reading (
    week_ending        DATE PRIMARY KEY,
    crude_stocks       DOUBLE,   -- thousand barrels, excluding the SPR (WCESTUS1)
    distillate_stocks  DOUBLE,   -- thousand barrels (WDISTUS1)
    utilization        DOUBLE,   -- percent of operable capacity (WPULEUS3)
    production         DOUBLE,   -- thousand barrels per day (WCRFPUS2)
    exports            DOUBLE,   -- thousand barrels per day (WCREXUS2)
    -- ISO week of the week-ending date (METHODS.md section 1)
    week_year          INTEGER,
    week_number        INTEGER,  -- 1 to 53
    -- Five-year comparison for each score input: same week, prior five years
    crude_low          DOUBLE,
    crude_high         DOUBLE,
    crude_avg          DOUBLE,
    crude_position     DOUBLE,   -- 0 at the five-year low, 1 at the high
    crude_pct_vs_avg   DOUBLE,   -- -0.056 means 5.6% below the five-year average
    distillate_low         DOUBLE,
    distillate_high        DOUBLE,
    distillate_avg         DOUBLE,
    distillate_position    DOUBLE,
    distillate_pct_vs_avg  DOUBLE,
    utilization_low         DOUBLE,
    utilization_high        DOUBLE,
    utilization_avg         DOUBLE,
    utilization_position    DOUBLE,
    utilization_pct_vs_avg  DOUBLE,
    -- Calculated properties, filled in step 6
    tightness_score    INTEGER,  -- -3 to +3
    tightness_label    VARCHAR,  -- tight, normal, loose
    spread             DOUBLE,   -- Brent minus WTI, dollars per barrel
    -- Futures curve, HISTORY ONLY: EIA futures data ends April 5, 2024
    futures_gap        DOUBLE,   -- contract 1 minus contract 4, dollars per barrel (weekly average)
    futures_gap_pct    DOUBLE,   -- the same gap as a share of contract 4
    curve_state        VARCHAR   -- backwardation (tight), contango (loose), flat
);

-- Prediction market: one market on Polymarket or Kalshi (expansion item 3). Market-level only:
-- no account, wallet or address fields are ever stored.
CREATE TABLE IF NOT EXISTS prediction_market (
    market_key      VARCHAR PRIMARY KEY,   -- 'polymarket:<id>' or 'kalshi:<ticker>'
    platform        VARCHAR NOT NULL,
    market_id       VARCHAR NOT NULL,
    event_title     VARCHAR,
    question        VARCHAR,
    outcome         VARCHAR,               -- the outcome whose chance 'price' measures, usually 'Yes'
    topic           VARCHAR,               -- 'gulf_conflict' or 'oil_price'
    opened          DATE,
    closes          DATE,
    status          VARCHAR,               -- open or closed
    result          VARCHAR,               -- settlement result where the platform gives it
    total_volume    DOUBLE,                -- all-time volume at last fetch
    volume_unit     VARCHAR,               -- 'USD' (Polymarket) or 'contracts' (Kalshi, $1 each)
    last_fetched    TIMESTAMP
);

-- Market reading: one market on one day. Rows are added or updated, never deleted,
-- so markets that close and drop off the platforms' lists keep their history here.
CREATE TABLE IF NOT EXISTS market_reading (
    market_key      VARCHAR NOT NULL REFERENCES prediction_market (market_key),
    reading_date    DATE    NOT NULL,      -- UTC date
    price           DOUBLE,                -- 0 to 1, the market's implied chance of the outcome
    volume          DOUBLE,                -- traded that day (Kalshi history); empty if not published
    total_volume    DOUBLE,                -- all-time volume seen on this date (snapshots)
    fetched_at      TIMESTAMP,
    PRIMARY KEY (market_key, reading_date)
);
"""


# Columns added after a table was first created. CREATE TABLE IF NOT EXISTS does not add columns
# to an existing table, so these are added here, once, without touching existing rows.
UPGRADES = [
    "ALTER TABLE disruption_event ADD COLUMN IF NOT EXISTS hand_checked BOOLEAN DEFAULT FALSE",
    "ALTER TABLE disruption_event ADD COLUMN IF NOT EXISTS episode VARCHAR",
]


def connect(path=DB_PATH):
    """Open the database file (created if missing) and make sure all tables and columns exist."""
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    for statement in UPGRADES:
        con.execute(statement)
    return con


if __name__ == "__main__":
    con = connect()
    for (name,) in con.execute("SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall():
        rows = con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        print(f"{name:<18} {rows} rows")
