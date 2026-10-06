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
    capacity_bpd    DOUBLE,           -- barrels per day
    latitude        DOUBLE,           -- for the showcase map
    longitude       DOUBLE
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
    spr_stocks         DOUBLE,   -- thousand barrels in the Strategic Petroleum Reserve (WCSSTUS1), item 9
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

-- Trader positioning: one CFTC Commitments of Traders report for WTI (expansion item 5).
-- Positions are as of Tuesday and public on Friday: use 'released', never 'report_date', for timing.
CREATE TABLE IF NOT EXISTS trader_positioning (
    report_date       DATE PRIMARY KEY,   -- Tuesday the positions were measured
    released          DATE,               -- Friday the CFTC published them (holidays can delay)
    week_ending       DATE,               -- EIA week holding that Tuesday; joins to weekly_reading
    contract_code     VARCHAR,            -- '067651', NYMEX WTI
    open_interest     DOUBLE,             -- contracts of 1,000 barrels
    spec_long         DOUBLE,             -- noncommercial (large speculator) long
    spec_short        DOUBLE,
    spec_spread       DOUBLE,             -- held long and short at once
    commercial_long   DOUBLE,             -- hedgers
    commercial_short  DOUBLE,
    small_long        DOUBLE,             -- nonreportable (small traders)
    small_short       DOUBLE,
    spec_net          DOUBLE,             -- calculated: spec_long - spec_short
    spec_net_pct_oi   DOUBLE              -- calculated: spec_net / open_interest
);

-- Staged event: a disruption event proposed by the AI news reader (item 8), waiting for review.
-- Only news_reader.approve() copies a row into disruption_event, after the user types "yes".
CREATE TABLE IF NOT EXISTS staged_event (
    staged_id            INTEGER PRIMARY KEY,
    staged_at            TIMESTAMP,
    status               VARCHAR,          -- pending, approved, rejected
    article_url          VARCHAR,
    article_publisher    VARCHAR,
    article_published    DATE,
    is_supply_event      BOOLEAN,
    event_name           VARCHAR,
    event_date           DATE,
    event_date_note      VARCHAR,
    country              VARCHAR,
    facility_or_route    VARCHAR,
    facility_type        VARCHAR,
    cause                VARCHAR,
    product              VARCHAR,
    physical_supply_lost VARCHAR,          -- yes, no, or empty if unclear
    capacity_offline_bpd BIGINT,
    capacity_note        VARCHAR,
    evidence             VARCHAR,          -- JSON list of {field, quote}, quotes 25 words or fewer
    uncertainties        VARCHAR,          -- JSON list of strings
    model                VARCHAR,          -- the model that produced the extraction
    event_id             VARCHAR,          -- set on approval
    reviewed_at          TIMESTAMP
);

-- Chokepoint transit: one chokepoint on one day, from IMF PortWatch (item 9). Ships are counted
-- from satellite AIS signals; capacity is the deadweight tonnage of the ships, in metric tons.
CREATE TABLE IF NOT EXISTS chokepoint_transit (
    facility_id        VARCHAR NOT NULL REFERENCES facility (facility_id),
    transit_date       DATE    NOT NULL,
    tankers            INTEGER,
    all_ships          INTEGER,
    tanker_capacity_t  DOUBLE,
    all_capacity_t     DOUBLE,
    PRIMARY KEY (facility_id, transit_date)
);

-- Daily indicator: one value of one daily market or risk series on one day (items 6, 7, 10),
-- e.g. 'OVX'. Which series may be published outside this machine is recorded in fred.INDICATORS.
CREATE TABLE IF NOT EXISTS daily_indicator (
    indicator   VARCHAR NOT NULL,
    obs_date    DATE    NOT NULL,
    value       DOUBLE  NOT NULL,
    PRIMARY KEY (indicator, obs_date)
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
    "ALTER TABLE facility ADD COLUMN IF NOT EXISTS latitude DOUBLE",
    "ALTER TABLE facility ADD COLUMN IF NOT EXISTS longitude DOUBLE",
    "ALTER TABLE weekly_reading ADD COLUMN IF NOT EXISTS spr_stocks DOUBLE",
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
