"""The project's dataset sources as rows in the source table, so every public number can point to one.

Run: .venv/bin/python sources.py
Each entry mirrors a row of docs/SOURCES.md (a test checks they agree). Event citations are separate
rows written by events.py (kind = 'citation'); these are kind = 'dataset'.
"""

import datetime as dt

import pandas as pd

import chokepoints
import db
import fred
import gpr

D = dt.date
DATASETS = [
    dict(source_id="ds-eia", publisher="U.S. Energy Information Administration", url="https://www.eia.gov/opendata/",
         terms_note="US government data, public domain; credit EIA, no logo", publishable=True, accessed_date=D(2026, 10, 7)),
    dict(source_id="ds-fred-dgs10", publisher="Federal Reserve Board via FRED", url="https://fred.stlouisfed.org/series/DGS10",
         terms_note="H.15, no third-party copyright notice", publishable=fred.INDICATORS["UST10Y"]["publishable"], accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-fred-dtwexbgs", publisher="Federal Reserve Board via FRED", url="https://fred.stlouisfed.org/series/DTWEXBGS",
         terms_note="H.10, no third-party copyright notice", publishable=fred.INDICATORS["USD_BROAD"]["publishable"], accessed_date=D(2026, 10, 7)),
    dict(source_id="ds-fred-ovxcls", publisher="CBOE via FRED", url="https://fred.stlouisfed.org/series/OVXCLS",
         terms_note="Copyright CBOE; personal use only", publishable=fred.INDICATORS["OVX"]["publishable"], accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-fred-nasdaqcom", publisher="Nasdaq via FRED", url="https://fred.stlouisfed.org/series/NASDAQCOM",
         terms_note="Copyright Nasdaq OMX Group", publishable=fred.INDICATORS["NASDAQ"]["publishable"], accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-fred-hy", publisher="ICE Data Indices via FRED", url="https://fred.stlouisfed.org/series/BAMLH0A0HYM2",
         terms_note="Copyright ICE; reproduction prohibited without permission", publishable=fred.INDICATORS["HY_SPREAD"]["publishable"], accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-cftc", publisher="CFTC Commitments of Traders", url="https://publicreporting.cftc.gov/",
         terms_note="US government, public domain; legacy (6dca-aqww) and disaggregated (72hh-3qpy) reports", publishable=True, accessed_date=D(2026, 10, 7)),
    dict(source_id="ds-portwatch", publisher="IMF PortWatch", url="https://portwatch.imf.org/",
         terms_note="IMF data may be published with attribution to the IMF", publishable=chokepoints.PUBLISHABLE, accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-gpr", publisher="Caldara and Iacoviello", url="https://www.matteoiacoviello.com/gpr.htm",
         terms_note="Creative Commons BY; cite the AER 2022 paper", publishable=gpr.PUBLISHABLE, accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-polymarket", publisher="Polymarket", url="https://docs.polymarket.com/",
         terms_note="Public market data, no key; redistribution terms not confirmed", publishable=False, accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-kalshi", publisher="Kalshi", url="https://docs.kalshi.com/",
         terms_note="Public market data, no key; redistribution terms not confirmed", publishable=False, accessed_date=D(2026, 10, 5)),
    dict(source_id="ds-eia-impcus", publisher="U.S. Energy Information Administration", url="https://www.eia.gov/opendata/browser/petroleum/move/impcus",
         terms_note="US government data, public domain", publishable=True, accessed_date=D(2026, 10, 7),
         data_quality="Monthly US crude imports by origin (Tier A); published with about a two-month lag and revised; regional totals dropped"),
    dict(source_id="ds-eia-intl", publisher="U.S. Energy Information Administration", url="https://www.eia.gov/opendata/browser/international",
         terms_note="US government data, public domain", publishable=True, accessed_date=D(2026, 10, 7),
         data_quality="Monthly crude production by country (Tier B), to June 2026; estimates revised later; no exports by country, imports annual to 2020 only"),
    dict(source_id="ds-naturalearth", publisher="Natural Earth", url="https://www.naturalearthdata.com/about/terms-of-use/",
         terms_note="Public domain", publishable=True, accessed_date=D(2026, 10, 7)),
]


def store(con):
    df = pd.DataFrame(DATASETS)
    if "data_quality" not in df:
        df["data_quality"] = None
    con.execute("""INSERT INTO source (source_id, event_id, publisher, url, published_date, accessed_date, terms_note, publishable, kind, data_quality)
                   SELECT source_id, NULL, publisher, url, NULL, accessed_date, terms_note, publishable, 'dataset', data_quality FROM df
                   ON CONFLICT (source_id) DO UPDATE SET publisher = EXCLUDED.publisher, url = EXCLUDED.url,
                       accessed_date = EXCLUDED.accessed_date, terms_note = EXCLUDED.terms_note,
                       publishable = EXCLUDED.publishable, kind = 'dataset', data_quality = EXCLUDED.data_quality""")


def main():
    con = db.connect()
    store(con)
    print(f"Stored {len(DATASETS)} dataset sources ({sum(d['publishable'] for d in DATASETS)} publishable)")


if __name__ == "__main__":
    main()
