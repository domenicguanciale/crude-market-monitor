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
    week_ending     DATE              -- links the event to its weekly_reading
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
    benchmark       VARCHAR NOT NULL,      -- 'WTI' or 'Brent'
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
    -- Calculated properties, filled in steps 5 and 6
    tightness_score    INTEGER,  -- -3 to +3
    tightness_label    VARCHAR,  -- tight, normal, loose
    spread             DOUBLE    -- Brent minus WTI, dollars per barrel
);
"""


def connect(path=DB_PATH):
    """Open the database file (created if missing) and make sure all tables exist."""
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    return con


if __name__ == "__main__":
    con = connect()
    for (name,) in con.execute("SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall():
        rows = con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        print(f"{name:<18} {rows} rows")
