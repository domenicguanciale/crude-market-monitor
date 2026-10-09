"""Browser tests for the public pages (docs/index.html and docs/3d.html), run in headless Chromium.

What they check, in plain language:
- Both pages load with no console errors, in light and dark mode, at desktop width and at phone width (390 px),
  and never scroll sideways.
- The 3D page draws real frames (the canvas is not blank) in each of the five views, and hovering one item in
  each view shows a tooltip with its source. The world flows data loads only when that view opens.
- Moving to a fixed date shows the same Brent, WTI, tightness and volatility numbers that are stored in the database.
- Dates before a series starts say "n/a" instead of inventing a value.
- The 2D dashboard loads when scrolled to, every panel draws, its sentence matches the database, the cursor follows
  the date, the CSV downloads carry a source line, and a spike table date opens the 3D price terrain.
- The shared state module (docs/js/state.js) clamps dates, round-trips the URL hash and plays back deterministically.

The tests skip if Playwright or its Chromium is missing. Set QA_SHOTS=1 to also save screenshots in docs/qa/.
Run: .venv/bin/python -m unittest tests.browser.test_pages
"""
import functools
import http.server
import io
import os
import re
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
DB = ROOT / "crude_monitor.duckdb"
QA = DOCS / "qa"
SIZES = {"desktop": (1280, 860), "phone": (390, 844)}

try:
    from playwright.sync_api import sync_playwright
except ImportError:                                    # pragma: no cover
    sync_playwright = None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@unittest.skipIf(sync_playwright is None, "playwright not installed")
class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(_Quiet, directory=str(DOCS))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base = "http://127.0.0.1:%d/" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        except Exception as e:                         # pragma: no cover
            cls.pw.stop(); cls.server.shutdown()
            raise unittest.SkipTest("Chromium not available: %s" % e)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close()

    def open(self, path, size="desktop", scheme="light"):
        w, h = SIZES[size]
        ctx = self.browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, reduced_motion="reduce")
        self.addCleanup(ctx.close)
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(self.base + path)
        page.wait_for_load_state("networkidle")
        return page, errors

    def open_3d(self, hash_="", **kw):
        page, errors = self.open("3d.html" + hash_, **kw)
        page.wait_for_function("window.__viz && window.__viz.frames() > 0", timeout=20000)
        return page, errors

    def open_dashboard(self, page, all_panels=True):
        """Scroll to the dashboard, wait for Plotly and the data, then scroll each panel in so it draws."""
        page.evaluate("document.getElementById('dash').scrollIntoView()")
        page.wait_for_function("window.__viz.dash.ready", timeout=30000)
        ids = page.evaluate("window.__viz.dash.panels.map((p) => p.id)")
        for pid in (ids if all_panels else ids[:2]):
            page.evaluate("document.getElementById('p-%s').scrollIntoView()" % pid)
            page.wait_for_function("window.__viz.dash.panels.find((p) => p.id === '%s').built" % pid, timeout=15000)
        return ids

    def summary(self, page, pid):
        return page.evaluate("window.__viz.dash.panels.find((p) => p.id === '%s').sum.textContent" % pid)

    def shot(self, page, name):
        if os.environ.get("QA_SHOTS") == "1":
            QA.mkdir(exist_ok=True)
            page.screenshot(path=str(QA / (name + ".png")))

    def no_sideways_scroll(self, page):
        over = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        self.assertLessEqual(over, 1, "page scrolls sideways by %d px" % over)

    def text(self, page, sel):
        return page.inner_text(sel).strip()

    # ---------- both pages, every size and theme ----------
    def test_pages_load_clean_everywhere(self):
        for path in ("index.html", "3d.html"):
            for size in SIZES:
                for scheme in ("light", "dark"):
                    with self.subTest(page=path, size=size, scheme=scheme):
                        if path == "3d.html":
                            page, errors = self.open_3d(size=size, scheme=scheme)
                            self.open_dashboard(page, all_panels=False)
                            self.shot(page, "3d_dashboard_%s_%s" % (size, scheme))
                            page.evaluate("window.scrollTo(0, 0)"); page.evaluate("window.__viz.redraw()"); page.wait_for_timeout(300)
                        else:
                            page, errors = self.open(path, size=size, scheme=scheme)
                            page.wait_for_timeout(1500)        # Plotly charts draw after the JSON arrives
                        self.assertEqual(errors, [])
                        self.no_sideways_scroll(page)
                        self.shot(page, "%s_%s_%s" % (path.split(".")[0], size, scheme))

    # ---------- 3D page draws something in every view ----------
    BUTTON = {"price": "#vPrice", "sky": "#vSky", "globe": "#vGlobe", "hz": "#vHz", "flows": "#vFlows"}

    def settle(self, page):
        """Wait until the flows file (if needed) has loaded and two more frames have been drawn."""
        page.wait_for_function("window.__viz.state.get().view !== 'flows' || window.__viz.scenes.flows.loaded", timeout=15000)
        n = page.evaluate("window.__viz.frames()")
        page.evaluate("window.__viz.redraw()")                 # the page draws only on change, so ask for one frame
        page.wait_for_function("window.__viz.frames() > %d" % n, timeout=10000)

    def test_each_view_draws_a_non_blank_canvas(self):
        from PIL import Image
        page, errors = self.open_3d("#v=globe&d=2026-04-17")
        self.assertTrue(page.evaluate("window.__viz.webgl"), "WebGL renderer did not start")
        self.assertFalse(page.evaluate("window.__viz.scenes.flows.loaded"), "flows.json should load only when its view opens")
        for view in ("price", "sky", "hz", "flows", "globe"):
            with self.subTest(view=view):
                page.click(self.BUTTON[view])
                self.settle(page)
                img = Image.open(io.BytesIO(page.locator("#gl").screenshot())).convert("RGB").resize((160, 100))
                px = img.tobytes()
                colours = len({px[i:i + 3] for i in range(0, len(px), 3)})
                self.assertGreater(colours, 40, "canvas looks blank in %s view (%d colours)" % (view, colours))
                self.assertIn("v=" + view, page.evaluate("location.hash"))
        self.assertIn("Who sold", page.evaluate("document.getElementById('flowLists').innerText"))
        self.assertEqual(errors, [])

    def test_tooltip_in_each_view(self):
        expect = {"price": "Rule:", "sky": "Week ending", "globe": "Strait of Hormuz", "hz": "Strait of Hormuz", "flows": "Saudi Arabia"}
        source = {"price": "spikes.py", "sky": "EIA", "globe": "PortWatch", "hz": "PortWatch", "flows": "EIA"}
        page, errors = self.open_3d("#v=price&d=2026-04-17")
        for view, word in expect.items():
            with self.subTest(view=view):
                page.evaluate("window.__viz.state.set({view: '%s'})" % view)
                self.settle(page)
                box = page.locator("#gl").bounding_box()       # the option row above the canvas changes height per view
                p = page.evaluate("window.__viz.probe()")
                self.assertIsNotNone(p, "nothing to hover in " + view)
                self.assertTrue(0 <= p["x"] <= box["width"] and 0 <= p["y"] <= box["height"], "probe off screen in %s: %s" % (view, p))
                page.mouse.move(box["x"] + p["x"], box["y"] + p["y"])
                page.wait_for_selector("#tip", state="visible", timeout=5000)
                tip = self.text(page, "#tip")
                self.assertIn(word, tip)
                self.assertIn(source[view], tip)
                page.mouse.move(box["x"] + 5, box["y"] + 5)
        self.assertEqual(errors, [])

    def test_clicking_a_spike_pin_jumps_to_its_date(self):
        page, errors = self.open_3d("#v=price&d=2026-02-28")
        self.settle(page)
        pin = {"id": "WTI-SURGE-2026-04-07", "d1": "2026-04-07"}     # front wall, near the opening date
        p = page.evaluate("(() => { const v = window.__viz; v.camera.updateMatrixWorld(); const q = v.scenes.price.probe(v.state.get(), '%s'); if (!q) return null; q.project(v.camera); return {x: (q.x * 0.5 + 0.5) * document.getElementById('viewport').clientWidth, y: (-q.y * 0.5 + 0.5) * document.getElementById('viewport').clientHeight}; })()" % pin["id"])
        self.assertIsNotNone(p)
        box = page.locator("#gl").bounding_box()
        page.mouse.click(box["x"] + p["x"], box["y"] + p["y"])
        page.wait_for_function("location.hash.includes('d=%s')" % pin["d1"], timeout=5000)
        self.assertEqual(errors, [])

    # ---------- readouts match the database ----------
    @unittest.skipUnless(DB.exists(), "database not built")
    def test_readouts_match_database(self):
        import duckdb
        con = duckdb.connect(str(DB), read_only=True)
        self.addCleanup(con.close)
        for iso in ("2008-07-03", "2020-04-21", "2026-04-17"):
            with self.subTest(date=iso):
                page, errors = self.open_3d("#v=globe&d=" + iso)
                rows = dict(con.execute("SELECT benchmark, price FROM price_series WHERE price_date = ? "
                                        "AND benchmark IN ('Brent', 'WTI')", [iso]).fetchall())
                for bench, sel in (("Brent", "#rBrent"), ("WTI", "#rWti")):
                    if bench in rows:
                        self.assertEqual(self.text(page, sel), "%.2f" % rows[bench])
                wk = con.execute("SELECT week_ending, tightness_score FROM weekly_reading WHERE week_ending <= ? "
                                 "AND tightness_score IS NOT NULL ORDER BY week_ending DESC LIMIT 1", [iso]).fetchone()
                self.assertIn(wk[0].isoformat(), self.text(page, "#rWeekH"))
                rv = con.execute("SELECT value FROM daily_indicator WHERE indicator = 'RV20_BRENT' AND obs_date <= ? "
                                 "ORDER BY obs_date DESC LIMIT 1", [iso]).fetchone()[0]
                rank = con.execute("SELECT avg(CASE WHEN value < ? THEN 1 ELSE 0 END) FROM daily_indicator "
                                   "WHERE indicator = 'RV20_BRENT' AND value IS NOT NULL", [rv]).fetchone()[0]
                self.assertEqual(self.text(page, "#rVol"), "%.0f%%" % (100 * rv))
                self.assertLessEqual(abs(float(self.text(page, "#rVolRank").rstrip("%")) - 100 * rank), 1)
                score = int(wk[1])
                shown = re.match(r"[+\u2212-]?\d", self.text(page, "#rScore")).group(0)
                self.assertEqual(int(shown.replace("\u2212", "-")), score)
                self.assertEqual(errors, [])

    def test_dates_before_the_data_say_na(self):
        page, errors = self.open_3d("#v=hz&d=1990-06-01")
        self.assertIn("Jun 1, 1990", self.text(page, "#rDate"))
        self.assertIn("scores start", self.text(page, "#rWeekH").lower())
        self.assertEqual(self.text(page, "#rScore"), "n/a")
        ship = self.text(page, "#rShip")
        self.assertEqual(ship.count("n/a"), 6, ship)
        self.assertIn("No ships drawn", self.text(page, "#hzNote"))
        self.assertEqual(errors, [])

    def test_opens_at_the_2026_disruption_and_plays(self):
        page, errors = self.open_3d()
        self.assertEqual(self.text(page, "#rDate"), "Feb 28, 2026")
        self.assertEqual(page.evaluate("window.__viz.state.get().view"), "price")
        start = page.evaluate("window.__viz.state.get().day")
        page.click("#play")
        page.wait_for_function("window.__viz.state.get().day > %d" % start, timeout=10000)
        page.click("#play")
        self.assertFalse(page.evaluate("window.__viz.state.get().playing"))
        page.click("#jStart")
        self.assertEqual(self.text(page, "#rDate"), "Jan 2, 1986")
        self.assertEqual(page.evaluate("location.hash"), "#v=price&d=1986-01-02")
        self.assertEqual(errors, [])

    # ---------- the 2D dashboard ----------
    @unittest.skipUnless(DB.exists(), "database not built")
    def test_dashboard_panels_match_database(self):
        import duckdb
        con = duckdb.connect(str(DB), read_only=True)
        self.addCleanup(con.close)
        page, errors = self.open_3d("#v=price&d=2026-04-17")
        ids = self.open_dashboard(page)
        self.assertEqual(ids, ["price", "vol", "spread", "ship", "flows", "inv", "cot", "money"])
        for pid in ids:
            with self.subTest(panel=pid):
                self.assertTrue(page.evaluate("!!document.querySelector('#p-%s .main-svg')" % pid), "no chart drawn")
                self.assertTrue(self.summary(page, pid).strip())
        brent = con.execute("SELECT price FROM price_series WHERE benchmark = 'Brent' AND price_date = '2026-04-17'").fetchone()[0]
        self.assertIn("Brent was $%.2f" % brent, self.summary(page, "price"))
        crude = con.execute("SELECT crude_stocks FROM weekly_reading WHERE week_ending = '2026-04-17'").fetchone()[0]
        self.assertIn("%.1f million barrels" % (crude / 1000), self.summary(page, "inv"))
        rep_date, rel = con.execute("SELECT report_date, released FROM trader_positioning WHERE released <= '2026-04-17' "
                                    "ORDER BY report_date DESC LIMIT 1").fetchone()
        self.assertIn("measured on %s (released %s" % (rep_date.isoformat(), rel.isoformat()), self.summary(page, "cot"))
        imports = con.execute("SELECT sum(volume_kbd) FROM trade_flow WHERE tier = 'A' AND importer = 'USA' AND period = '2026-04-01'").fetchone()[0]
        self.assertIn("were {:,} thousand b/d".format(round(imports)), self.summary(page, "flows"))
        # the cursor follows the shared date
        page.evaluate("document.getElementById('p-price').scrollIntoView()")
        page.evaluate("window.__viz.state.set({day: window.__viz.data.dayOf('2008-07-03')})")
        page.wait_for_function("document.querySelector('#p-price .chart').layout.shapes[0].x0 === '2008-07-03'", timeout=5000)
        self.assertIn("Jul 3, 2008", self.summary(page, "price"))
        self.assertEqual(errors, [])

    def test_dashboard_csv_and_spike_table(self):
        page, errors = self.open_3d("#v=globe&d=2026-04-17")
        self.open_dashboard(page, all_panels=False)
        page.evaluate("document.getElementById('p-price').scrollIntoView()")
        with page.expect_download() as dl:
            page.click("#p-price .csv")
        text = Path(dl.value.path()).read_text()
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("# Source: U.S. Energy Information Administration"))
        self.assertEqual(lines[2], "date,brent_usd_bbl,wti_usd_bbl")
        self.assertTrue(any(l.startswith("2026-04-17,") for l in lines))
        with page.expect_download() as dl:
            page.click("#spikeCsv")
        self.assertIn("spike_id,benchmark,kind", Path(dl.value.path()).read_text())
        # pressing a date in the spike table opens the 3D price terrain on that date
        first = page.locator("#spikeBody button.link").first
        day = first.get_attribute("data-day")
        first.click()
        page.wait_for_function("location.hash === '#v=price&d=%s'" % day, timeout=5000)
        # sorting by move puts the largest rise first
        page.click("[data-sort=pct]")
        top = page.locator("#spikeBody tbody tr").first.locator("td.n").inner_text()
        self.assertTrue(top.startswith("+"), top)
        self.assertEqual(errors, [])

    # ---------- the shared state module ----------
    def test_state_module(self):
        page, errors = self.open_3d()
        r = page.evaluate("""async () => {
          const S = await import('./js/state.js');
          const T0 = Date.parse('1986-01-02T00:00:00Z');
          const isoOf = (i) => new Date(T0 + i * 864e5).toISOString().slice(0, 10);
          const dayOf = (s) => Math.round((Date.parse(s + 'T00:00:00Z') - T0) / 864e5);
          const N = 1000, st = S.createState({ day: 10 }, N), seen = [];
          st.subscribe((s, changed) => seen.push(changed.join(',')));
          st.set({ day: 5000 }); const clampedHigh = st.get().day;
          st.set({ day: -3 }); const clampedLow = st.get().day;
          st.set({ view: 'nonsense' }); const viewKept = st.get().view;
          const nothing = st.set({ day: 0 }).length;
          const hash = S.toHash({ view: 'hz', day: 400, keep2020: true }, isoOf);
          const hashM = S.toHash({ view: 'sky', day: 400, measure: 'vol' }, isoOf);
          const backM = S.fromHash(hashM + '&m2=x', dayOf, N);
          st.set({ measure: 'nonsense' }); const measureKept = st.get().measure;
          const back = S.fromHash(hash, dayOf, N);
          const bad = S.fromHash('#v=moon&d=1999-99', dayOf, N);
          const run = () => { let s = { day: 0, speed: 35, playing: true }, c = 0;
            for (const dt of [0.016, 0.017, 0.016, 0.5, 0.033]) { const a = S.advance(s, dt, c, N); s = { ...s, day: a.day, playing: a.playing }; c = a.carry; }
            return s.day; };
          const end = S.advance({ day: N - 3, speed: 365, playing: true }, 1, 0, N);
          return { clampedHigh, clampedLow, viewKept, nothing, seen, hash, back, bad, run1: run(), run2: run(), end, hashM, backM, measureKept };
        }""")
        self.assertEqual(r["clampedHigh"], 999)
        self.assertEqual(r["clampedLow"], 0)
        self.assertEqual(r["viewKept"], "price")
        self.assertEqual(r["measureKept"], "score")
        self.assertEqual(r["hashM"], "#v=sky&d=1987-02-06&m=vol")
        self.assertEqual(r["backM"], {"day": 400, "view": "sky", "measure": "vol"})
        self.assertEqual(r["nothing"], 0)                 # setting the same value notifies nobody
        self.assertEqual(r["seen"], ["day", "day"])
        self.assertEqual(r["hash"], "#v=hz&d=1987-02-06&k=1")
        self.assertEqual(r["back"], {"day": 400, "view": "hz", "keep2020": True})
        self.assertEqual(r["bad"], {})
        self.assertEqual(r["run1"], r["run2"])             # same frame times, same date
        self.assertEqual(r["run1"], 20)                    # 0.582 s at 35 days a second = 20.37 days
        self.assertEqual(r["end"], {"day": 999, "carry": 0, "playing": False})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
