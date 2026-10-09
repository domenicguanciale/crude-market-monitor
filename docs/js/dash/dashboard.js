// The 2D dashboard (World Oil Simulation, M7): linked Plotly charts that read the same shared date as the 3D views.
// - Every chart draws a cursor line at the selected date; clicking a chart moves the date.
// - Every chart has a one-sentence text summary for the date (also its aria-label) and a CSV download.
// - Plotly and docs/data/dash.json load only when the dashboard scrolls near the screen.
// - The headline strip and the spike table need neither, so they are built at once.
import { label, signed, pct } from '../data.js';

const PLOTLY = 'https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js';   // same version as index.html
const OKABE = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9', '#8C8C8C'];   // colour-blind safe
const DASHES = ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot', 'solid'];
const KIND = { daily: 'One-day move', surge: 'Surge', crash: 'Crash', drawdown: 'Drawdown', spread: 'Brent minus WTI blowout' };
const GROUPS = ['North America', 'Latin America and Caribbean', 'Western Asia (incl. the Gulf)', 'Russia', 'Europe (excl. Russia)', 'Africa', 'Asia-Pacific'];
const RANGES = { all: 'All, since 1986', since2019: 'Since 2019', y2026: 'The 2026 disruption', around: 'Two years around the date' };

export function createDashboard({ data, state, fetchJSON, goTo3D }) {
  const { D, N, isoOf, dayOf, nice, val, lastVal } = data;
  const $ = (s, el = document) => el.querySelector(s);
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const root = $('#dash'), grid = $('#dgrid');
  const LAST = isoOf(N - 1), DISRUPTION = '2026-02-28';
  let X = null, F = null, Plotly = null, range = 'all';
  const setDay = (iso) => state.set({ playing: false, day: dayOf(String(iso).length === 7 ? iso + '-01' : String(iso).slice(0, 10)) });

  // ---------- small helpers ----------
  const money = (v, d = 2) => (v == null ? 'n/a' : (v < 0 ? '−$' : '$') + Math.abs(v).toFixed(d));
  const sgnPct = (v, d = 0) => (v == null ? 'n/a' : (v >= 0 ? '+' : '−') + Math.abs(100 * v).toFixed(d) + '%');
  const xy = (ser, scale = 1) => {
    const x = [], y = [];
    for (let k = 0; k < ser.v.length; k++) { const v = ser.v[k]; if (v != null) { x.push(isoOf(ser.s + k)); y.push(v * scale); } }
    return { x, y };
  };
  const onOrBefore = (dates, iso) => { let lo = 0, hi = dates.length; while (lo < hi) { const m = (lo + hi) >> 1; if (dates[m] <= iso) lo = m + 1; else hi = m; } return lo - 1; };
  const sortedRank = (vals) => { const a = Float64Array.from(vals.filter((v) => v != null)).sort();
    return (v) => { if (v == null) return null; let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < v) lo = m + 1; else hi = m; } return lo / a.length; }; };
  function download(name, source, rows) {
    const cell = (v) => (v == null ? '' : typeof v === 'string' && /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : String(v));
    const text = ['# Source: ' + source, '# Crude Market Monitor, research tool, not trading advice. Exported ' + new Date().toISOString().slice(0, 10)]
      .concat(rows.map((r) => r.map(cell).join(','))).join('\n') + '\n';
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' })); a.download = name;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  // ---------- headline strip: latest readings, each with its as-of date (no Plotly needed) ----------
  function headline() {
    const w = data.weeks[data.weeks.length - 1], s = w.out;
    let sd = N - 1; while (sd > 0 && (val(D.prices.brent, sd) == null || val(D.prices.wti, sd) == null)) sd--;
    const rv = data.market.rv20.brent; const rvEnd = rv.s + rv.v.length - 1;
    const h = data.hormuz.tankers7, hEnd = h.s + h.v.length - 1, hv = val(h, hEnd), hBase = data.hormuz.baseline;
    const items = [
      ['US tightness', s ? signed(s[0]) + ' ' + label(s[0]) : 'n/a', 'week ending ' + w.d],
      ['Brent minus WTI', money(val(D.prices.brent, sd) - val(D.prices.wti, sd)) + ' a barrel', isoOf(sd)],
      ['Brent 20-day volatility', pct(val(rv, rvEnd)) + ', higher than ' + pct(data.volRank('brent', val(rv, rvEnd))) + ' of trading days since 1987', isoOf(rvEnd)],
      ['Hormuz tanker traffic', hv == null ? 'n/a' : Math.round(100 * hv / hBase) + '% of usual (' + hv.toFixed(1) + ' a day, 7-day average)', isoOf(hEnd)],
    ];
    $('#headline').innerHTML = items.map(([k, v, d]) => '<div class="hl"><div class="k">' + k + '</div><div class="v">' + v + '</div><div class="d">Latest: ' + d + '</div></div>').join('');
  }

  // ---------- spike table (no Plotly needed) ----------
  const T = { sort: 'd1', dir: -1, filter: 'episodes' };
  function spikeRows() {
    return data.spikes.filter((s) => T.filter === 'all' || s.k !== 'daily');
  }
  function spikeTable() {
    const rows = spikeRows().slice().sort((a, b) => {
      const va = T.sort === 'pct' ? (a.pct ?? -Infinity) : a[T.sort], vb = T.sort === 'pct' ? (b.pct ?? -Infinity) : b[T.sort];
      return (va < vb ? -1 : va > vb ? 1 : 0) * T.dir;
    });
    const th = (key, txt) => '<th scope="col" aria-sort="' + (T.sort === key ? (T.dir > 0 ? 'ascending' : 'descending') : 'none') + '"><button data-sort="' + key + '">' + txt +
      (T.sort === key ? (T.dir > 0 ? ' ▲' : ' ▼') : '') + '</button></th>';
    const size = (s) => (s.k === 'spread' ? 'widest ' + money(s.p1) : s.pct == null ? 'n/a (price at or below zero)' : sgnPct(s.pct, 1));
    $('#spikeBody').innerHTML = '<table><thead><tr>' + th('d1', 'Extreme date') + th('b', 'Benchmark') + th('k', 'Kind') + th('pct', 'Move') +
      '<th scope="col">Rule</th><th scope="col">Hand-checked</th><th scope="col">Source</th></tr></thead><tbody>' +
      rows.map((s) => '<tr><td><button class="link" data-day="' + s.d1 + '" title="Show this date in the 3D price terrain">' + s.d1 + '</button>' + (s.d0 !== s.d1 ? '<br><span class="note">from ' + s.d0 + '</span>' : '') + '</td><td>' + s.b +
        '</td><td>' + KIND[s.k] + (s.unconfirmed ? '<br><span class="note">unconfirmed print</span>' : '') + '</td><td class="n">' + size(s) + '</td><td>' + s.rule + '</td><td>' +
        (s.checked ? 'Yes' : 'Not yet') + '</td><td>' + (s.checked && s.sources ? s.sources.map((q) => '<a href="' + q[1] + '" rel="noopener">' + q[0] + '</a>').join('<br>') : 'EIA spot prices (rule-detected); no explanation until hand-checked') +
        '</td></tr>').join('') + '</tbody></table>';
    $('#spikeCount').textContent = rows.length + ' of ' + data.spikes.length + ' spikes shown, ' + data.spikes.filter((s) => s.checked).length + ' hand-checked so far.';
  }
  $('#spikeBody').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.sort) { T.dir = T.sort === b.dataset.sort ? -T.dir : (b.dataset.sort === 'd1' || b.dataset.sort === 'pct' ? -1 : 1); T.sort = b.dataset.sort; spikeTable(); $('[data-sort="' + T.sort + '"]').focus(); }
    if (b.dataset.day) goTo3D(dayOf(b.dataset.day));
  });
  $('#spikeFilter').onchange = (e) => { T.filter = e.target.value; spikeTable(); };
  $('#spikeCsv').onclick = () => download('spike_catalog.csv', 'Rule-detected from EIA daily spot prices (spikes.py)',
    [['spike_id', 'benchmark', 'kind', 'rule', 'direction', 'start_date', 'extreme_date', 'start_value', 'extreme_value', 'size_usd', 'size_pct', 'hand_checked', 'unconfirmed_print']]
      .concat(spikeRows().map((s) => [s.id, s.b, s.k, s.rule, s.dir, s.d0, s.d1, s.p0, s.p1, s.usd, s.pct, s.checked ? 'yes' : 'no', s.unconfirmed ? 'yes' : 'no'])));
  headline(); spikeTable();

  // ---------- chart panels ----------
  const panels = [];
  const shade2026 = () => ({ type: 'rect', xref: 'x', yref: 'paper', x0: DISRUPTION, x1: LAST, y0: 0, y1: 1, fillcolor: css('--accent-soft'), line: { width: 0 }, layer: 'below' });
  function xrange(st) {
    if (range === 'since2019') return ['2019-01-01', LAST];
    if (range === 'y2026') return ['2025-12-01', LAST];
    if (range === 'around') return [isoOf(Math.max(0, st.day - 365)), isoOf(Math.min(N - 1, st.day + 365))];
    return [D.start, LAST];
  }
  function baseLayout(p, st) {
    const lay = {
      height: p.height || 260, margin: { l: 54, r: 14, t: 6, b: 30 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: 'system-ui, -apple-system, Segoe UI, sans-serif', size: 12, color: css('--ink-2') },
      xaxis: { type: 'date', range: p.monthly ? undefined : xrange(st), gridcolor: css('--grid'), linecolor: css('--axis'), zeroline: false },
      yaxis: { gridcolor: css('--grid'), zerolinecolor: css('--axis'), automargin: true },
      showlegend: true, legend: { orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom', font: { size: 11 } },
      hovermode: 'x unified', hoverlabel: { bgcolor: css('--surface'), bordercolor: css('--axis'), font: { color: css('--ink') } },
      shapes: [{ type: 'line', xref: 'x', yref: 'paper', x0: isoOf(st.day), x1: isoOf(st.day), y0: 0, y1: 1, line: { color: css('--ink'), width: 1.5 } }],
    };
    if (p.monthly) lay.xaxis.range = range === 'all' ? undefined : xrange(st);
    const extra = p.layout ? p.layout(st) : {};
    for (const [k, v] of Object.entries(extra)) if (k !== 'shapes') lay[k] = typeof v === 'object' && !Array.isArray(v) && lay[k] ? { ...lay[k], ...v } : v;
    lay.shapes = lay.shapes.concat(p.shade ? [shade2026()] : [], extra.shapes || []);
    return lay;
  }
  function panel(spec) {
    const el = document.createElement('article');
    el.className = 'panel' + (spec.wide ? ' wide' : ''); el.id = 'p-' + spec.id;
    el.innerHTML = '<header><h3>' + spec.title + '</h3><div class="tools">' + (spec.tools || '') + '<button class="csv">Download CSV</button></div></header>' +
      '<div class="chart" role="img" aria-label="' + spec.title + '"></div><p class="summary"></p><p class="src">Source: ' + spec.source + '</p>';
    grid.appendChild(el);
    const p = { ...spec, el, chart: $('.chart', el), sum: $('.summary', el), built: false, visible: false };
    $('.csv', el).onclick = () => { const c = p.csv(); download(c.name, p.source, c.rows); };
    if (spec.bind) spec.bind(el, () => render(p));
    panels.push(p);
    return p;
  }
  const cfg = { displayModeBar: false, responsive: true };
  function render(p) {
    if (!Plotly || !X) return;
    const st = state.get();
    Plotly.react(p.chart, p.traces(st), baseLayout(p, st), cfg);
    if (!p.built) { p.chart.on('plotly_click', (e) => { if (e.points && e.points[0]) setDay(e.points[0].x); }); p.built = true; }
    say(p, st);
  }
  function say(p, st) { const t = p.summary(st); p.sum.textContent = t; p.chart.setAttribute('aria-label', p.title + '. ' + t); }
  const line = (x, y, name, color, extra = {}) => ({ type: 'scatter', mode: 'lines', x, y, name, line: { color, width: 1.6, ...(extra.line || {}) }, hovertemplate: extra.ht || '%{y:.2f}', ...extra.more });

  // Cached series, built on first use.
  const cache = {};
  const once = (k, f) => (cache[k] ??= f());

  function buildPanels() {
    const W = X.weekly;
    const rv20b = data.market.rv20.brent, rv60b = X.rv60.brent;
    const rank60 = sortedRank(rv60b.v);
    const lastBefore = (ser, iso) => { let d = dayOf(iso) - 1; while (d > ser.s && val(ser, d) == null) d--; return d; };
    const preDay = lastBefore(X.brent, DISRUPTION);

    // 1. Prices
    let logScale = false;
    panel({
      id: 'price', title: 'Prices: Brent and WTI, daily spot', shade: true, source: X.sources.prices,
      tools: '<button class="tog" aria-pressed="false" data-k="log">Log scale</button>',
      bind: (el, rr) => { $('[data-k=log]', el).onclick = (e) => { logScale = !logScale; e.target.setAttribute('aria-pressed', logScale); rr(); }; },
      traces: () => {
        const b = once('brent', () => xy(X.brent)), w = once('wti', () => xy(X.wti));
        const ep = data.spikes.filter((s) => (s.k === 'surge' || s.k === 'crash' || s.k === 'drawdown'));
        const mk = (dir) => { const pts = ep.filter((s) => s.dir === dir); const ser = (s) => (s.b === 'WTI' ? X.wti : X.brent);
          return { type: 'scatter', mode: 'markers', name: dir === 'up' ? 'Surge (rule)' : 'Crash or drawdown (rule)', x: pts.map((s) => s.d1), y: pts.map((s) => val(ser(s), dayOf(s.d1))),
            marker: { symbol: dir === 'up' ? 'triangle-up' : 'triangle-down', size: 9, color: dir === 'up' ? css('--accent') : css('--warn'), line: { width: 1, color: css('--surface') } },
            text: pts.map((s) => KIND[s.k] + ', ' + s.b + ', ' + s.d0 + ' to ' + s.d1 + (s.pct != null ? ', ' + sgnPct(s.pct, 1) : '')), hovertemplate: '%{text}<extra></extra>' }; };
        return [line(b.x, b.y, 'Brent', css('--accent')), line(w.x, w.y, 'WTI', css('--warn'), { line: { dash: 'dot' } }), mk('up'), mk('down')];
      },
      layout: () => ({ yaxis: { title: { text: '$ per barrel', font: { size: 11 } }, type: logScale ? 'log' : 'linear', zeroline: true, zerolinewidth: 1.5 } }),
      summary: (st) => {
        const b = lastVal(X.brent, st.day, 5), w = lastVal(X.wti, st.day, 5);
        if (b == null && w == null) return 'No Brent or WTI price on or near ' + nice(st.day) + '.';
        let t = 'On ' + nice(st.day) + ', Brent was ' + money(b) + ' and WTI ' + money(w) + ' a barrel (EIA spot, latest trading day).';
        let td = st.day; while (td > preDay && val(X.brent, td) == null) td--;      // latest trading day on or before the date
        if (isoOf(st.day) >= DISRUPTION && b != null && td > preDay) t += ' Brent is ' + sgnPct(b / val(X.brent, preDay) - 1) + ' from ' + money(val(X.brent, preDay)) + ' on ' + nice(preDay) + ', the last trading day before the 2026 disruption.';
        if (logScale) t += ' The log scale cannot show prices at or below zero, so the April 2020 WTI print is hidden.';
        return t;
      },
      csv: () => { const rows = [['date', 'brent_usd_bbl', 'wti_usd_bbl']];
        for (let i = 0; i < N; i++) { const b = val(X.brent, i), w = val(X.wti, i); if (b != null || w != null) rows.push([isoOf(i), b, w]); }
        return { name: 'prices_brent_wti_daily.csv', rows }; },
    });

    // 2. Volatility
    panel({
      id: 'vol', title: 'Volatility: Brent, 20-day and 60-day realized', shade: true, source: X.sources.volatility,
      traces: () => {
        const a = once('rv20', () => xy(rv20b, 100)), b = once('rv60', () => xy(rv60b, 100));
        return [line(a.x, a.y, '20-day', css('--accent'), { ht: '%{y:.0f}%' }), line(b.x, b.y, '60-day', css('--ink-2'), { ht: '%{y:.0f}%', line: { dash: 'dash' } })];
      },
      layout: () => ({ yaxis: { title: { text: '% a year (annualized)', font: { size: 11 } }, rangemode: 'tozero' } }),
      summary: (st) => {
        const a = lastVal(rv20b, st.day, 7), b = lastVal(rv60b, st.day, 7);
        if (a == null) return 'No volatility reading on or near ' + nice(st.day) + '. Brent prices start in May 1987.';
        return 'On ' + nice(st.day) + ', Brent’s 20-day realized volatility was ' + pct(a) + ', higher than ' + pct(data.volRank('brent', a)) + ' of trading days since 1987, and its 60-day volatility was ' +
          pct(b) + ', higher than ' + pct(rank60(b)) + '.';
      },
      csv: () => { const rows = [['date', 'brent_rv20', 'brent_rv60']];
        for (let i = 0; i < N; i++) { const a = val(rv20b, i), b = val(rv60b, i); if (a != null || b != null) rows.push([isoOf(i), a, b]); }
        return { name: 'brent_realized_volatility.csv', rows }; },
    });

    // 3. Spread and futures curve
    panel({
      id: 'spread', title: 'Brent minus WTI, and the WTI futures curve', shade: true, height: 300,
      source: X.sources.prices + '; ' + X.sources.curve,
      traces: () => {
        const s = once('spread', () => { const x = [], y = []; for (let i = 0; i < N; i++) { const b = val(X.brent, i), w = val(X.wti, i); if (b != null && w != null) { x.push(isoOf(i)); y.push(+(b - w).toFixed(2)); } } return { x, y }; });
        const c = once('curve', () => { const x = [], y = [], col = [], txt = [];
          W.d.forEach((d, k) => { const g = W.futures_gap_pct[k]; if (g == null) return; x.push(d); y.push(100 * g); txt.push(W.curve[k]); col.push(W.curve[k] === 'backwardation' ? css('--accent') : W.curve[k] === 'contango' ? css('--warn') : css('--axis')); });
          return { x, y, col, txt }; });
        return [line(s.x, s.y, 'Brent minus WTI, $/bbl', css('--accent'), { ht: '$%{y:.2f}' }),
          { type: 'bar', x: c.x, y: c.y, yaxis: 'y2', name: 'Contract 1 vs 4, % (weekly)', marker: { color: c.col }, text: c.txt, hovertemplate: '%{y:.1f}% (%{text})<extra></extra>', textposition: 'none' }];
      },
      layout: () => ({ yaxis: { domain: [0.45, 1], title: { text: '$ per barrel', font: { size: 11 } } },
        yaxis2: { domain: [0, 0.36], gridcolor: css('--grid'), zerolinecolor: css('--axis'), title: { text: 'Curve, %', font: { size: 11 } } } }),
      summary: (st) => {
        const b = lastVal(X.brent, st.day, 5), w = lastVal(X.wti, st.day, 5);
        let t = b != null && w != null ? 'On ' + nice(st.day) + ', Brent minus WTI was ' + money(b - w) + ' a barrel.' : 'No spread on or near ' + nice(st.day) + '.';
        const k = onOrBefore(W.d, isoOf(st.day));
        let j = k; while (j >= 0 && W.futures_gap_pct[j] == null) j--;
        if (j >= 0 && dayOf(W.d[j]) >= st.day - 14) t += ' In the week ending ' + W.d[j] + ', the WTI futures curve was in ' + W.curve[j] + ': the first contract was ' +
          Math.abs(100 * W.futures_gap_pct[j]).toFixed(1) + '% ' + (W.futures_gap_pct[j] >= 0 ? 'above' : 'below') + ' the fourth.';
        else t += ' The futures curve series ends on April 5, 2024, because no free live source was found, so there is no curve reading for this date.';
        return t + ' Bars above zero are backwardation (beyond +1%), below zero contango (beyond −1%).';
      },
      csv: () => { const rows = [['date', 'series', 'value']];
        for (let i = 0; i < N; i++) { const b = val(X.brent, i), w = val(X.wti, i); if (b != null && w != null) rows.push([isoOf(i), 'brent_minus_wti_usd', +(b - w).toFixed(2)]); }
        W.d.forEach((d, k) => { if (W.futures_gap_pct[k] != null) rows.push([d, 'wti_contract1_vs_4_pct_' + W.curve[k], W.futures_gap_pct[k]]); });
        return { name: 'spread_and_futures_curve.csv', rows }; },
    });

    // 4. Shipping
    const choke = data.choke.slice().sort((a, b) => (a.id === 'strait-of-hormuz' ? -1 : b.id === 'strait-of-hormuz' ? 1 : a.name.localeCompare(b.name)));
    panel({
      id: 'ship', title: 'Shipping: tankers at six chokepoints, share of each lane’s usual traffic', shade: true, source: X.sources.shipping,
      layout: () => ({ xaxis: { range: range === 'all' ? ['2019-01-01', LAST] : xrange(state.get()) }, yaxis: { title: { text: '% of 2019 to 2025 median', font: { size: 11 } }, rangemode: 'tozero' },
        shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: 100, y1: 100, line: { color: css('--axis'), width: 1, dash: 'dot' } }] }),
      traces: () => choke.map((c, k) => { const s = once('ship' + c.id, () => xy(c.tankers7, 100 / c.baseline));
        return line(s.x, s.y, c.name.replace(' Strait', '').replace('Strait of ', ''), OKABE[k], { ht: '%{y:.0f}%', line: { dash: DASHES[k], width: c.id === 'strait-of-hormuz' ? 2.6 : 1.4 } }); }),
      summary: (st) => {
        if (st.day < data.portwatchStart) return 'IMF PortWatch tanker counts start on January 1, 2019, so there is no shipping reading for ' + nice(st.day) + '.';
        return '7-day averages on ' + nice(st.day) + ', as a share of each lane’s 2019 to 2025 median: ' +
          choke.map((c) => { const v = lastVal(c.tankers7, st.day); return c.name.replace('Strait of ', '') + ' ' + (v == null ? 'n/a' : Math.round(100 * v / c.baseline) + '%'); }).join(', ') + '.';
      },
      csv: () => { const rows = [['date'].concat(choke.map((c) => c.id + '_tankers_7d_avg'))];
        for (let i = data.portwatchStart; i < N; i++) rows.push([isoOf(i)].concat(choke.map((c) => val(c.tankers7, i))));
        rows.push(['median_2019_2025'].concat(choke.map((c) => c.baseline)));
        return { name: 'chokepoint_tankers.csv', rows }; },
    });

    // 5. Sellers and buyers (monthly, from flows.json)
    const groupOf = (iso) => {
      const c = F.countries[iso], sub = F.subregions[iso];
      if (iso === 'RUS') return GROUPS[3];
      if (sub === 'Northern America') return GROUPS[0];
      if (c[1] === 'Americas') return GROUPS[1];
      if (sub === 'Western Asia') return GROUPS[2];
      if (c[1] === 'Europe') return GROUPS[4];
      if (c[1] === 'Africa') return GROUPS[5];
      return GROUPS[6];
    };
    const byGroup = (dict) => { const out = Object.fromEntries(GROUPS.map((g) => [g, new Array(F.months.length).fill(0)]));
      for (const [iso, s] of Object.entries(dict)) s.v.forEach((v, k) => { if (v != null) out[groupOf(iso)][s.s + k] += v; });
      return out; };
    const monthAt = (st) => { const iso = isoOf(st.day), [y0, m0] = F.months[0].split('-').map(Number);
      return Math.min((Number(iso.slice(0, 4)) - y0) * 12 + Number(iso.slice(5, 7)) - m0, F.months.length - 1); };
    const base2025 = (series) => { const ks = F.months.map((m, k) => (m.startsWith(String(F.baseline_year)) ? k : -1)).filter((k) => k >= 0); return ks.reduce((a, k) => a + series[k], 0) / ks.length; };
    let flowsLayer = 'production';
    const lastMonthOf = (dict) => Math.max(...Object.values(dict).map((s) => s.s + s.v.length - 1));
    panel({
      id: 'flows', title: 'Sellers and buyers: crude production and US imports by region, monthly', monthly: true, wide: true, height: 300,
      source: X.sources.flows + '. Measured only (Tier A and B); production includes lease condensate',
      tools: '<span class="seg"><button class="tog" aria-pressed="true" data-k="production">Production</button><button class="tog" aria-pressed="false" data-k="imports">US imports</button></span>',
      bind: (el, rr) => el.querySelectorAll('[data-k=production],[data-k=imports]').forEach((b) => { b.onclick = () => { flowsLayer = b.dataset.k;
        el.querySelectorAll('[data-k=production],[data-k=imports]').forEach((q) => q.setAttribute('aria-pressed', q === b)); rr(); }; }),
      traces: () => {
        const dict = flowsLayer === 'production' ? F.production : F.us_imports, last = lastMonthOf(dict);
        const g = once('grp' + flowsLayer, () => byGroup(dict)), x = F.months.slice(0, last + 1);
        return GROUPS.map((name, k) => ({ type: 'scatter', mode: 'lines', stackgroup: 'one', name, x, y: g[name].slice(0, last + 1).map((v) => +v.toFixed(0)),
          line: { width: 0.5, color: OKABE[k] }, fillcolor: OKABE[k] + 'B3', hovertemplate: '%{y:,.0f}' }));
      },
      layout: () => ({ yaxis: { title: { text: 'Thousand b/d', font: { size: 11 } } }, shapes: [{ type: 'rect', xref: 'x', yref: 'paper', x0: '2026-03', x1: F.months[F.months.length - 1], y0: 0, y1: 1, fillcolor: css('--accent-soft'), line: { width: 0 }, layer: 'above' }] }),
      summary: (st) => {
        if (!F) return 'Loading the monthly flow data.';
        const m = monthAt(st);
        if (m < 0) return 'Monthly country data starts in January 2010.';
        const P = once('grpproduction', () => byGroup(F.production)), I = once('grpimports', () => byGroup(F.us_imports));
        const mp = Math.min(m, lastMonthOf(F.production)), mi = Math.min(m, lastMonthOf(F.us_imports));
        const totP = GROUPS.reduce((a, g) => a + P[g][mp], 0), totI = GROUPS.reduce((a, g) => a + I[g][mi], 0);
        const wa = P[GROUPS[2]][mp], waB = base2025(P[GROUPS[2]]);
        const mname = (k) => { const [y, mo] = F.months[k].split('-'); return new Date(Date.UTC(+y, +mo - 1, 1)).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' }); };
        return 'In ' + mname(mp) + ', countries in EIA’s data produced ' + (totP / 1000).toFixed(1) + ' million b/d of crude oil, including lease condensate; Western Asia, which includes the Gulf, produced ' + (wa / 1000).toFixed(1) +
          ' million b/d, ' + sgnPct(wa / waB - 1) + ' against its ' + F.baseline_year + ' monthly average. US crude imports in ' + mname(mi) + ' were ' + Math.round(totI).toLocaleString('en-US') +
          ' thousand b/d, ' + Math.round(100 * I[GROUPS[0]][mi] / totI) + '% of it from North America. The shaded months are from March 2026.';
      },
      csv: () => { const rows = [['month', 'region_group', 'crude_production_kbd', 'us_crude_imports_kbd']];
        const P = once('grpproduction', () => byGroup(F.production)), I = once('grpimports', () => byGroup(F.us_imports));
        F.months.forEach((m, k) => GROUPS.forEach((g) => rows.push([m, g, +P[g][k].toFixed(1), +I[g][k].toFixed(1)])));
        return { name: 'production_and_us_imports_by_region.csv', rows }; },
    });

    // 6. Inventories and policy
    const INV = {
      crude: { name: 'US commercial crude stocks', unit: 'million barrels', k: 'crude_stocks', lo: 'crude_low', avg: 'crude_avg', hi: 'crude_high', pos: 'crude_position', scale: 0.001 },
      distillate: { name: 'US distillate stocks', unit: 'million barrels', k: 'distillate_stocks', lo: 'distillate_low', avg: 'distillate_avg', hi: 'distillate_high', pos: 'distillate_position', scale: 0.001 },
      utilization: { name: 'US refinery utilization', unit: '%', k: 'utilization', lo: 'utilization_low', avg: 'utilization_avg', hi: 'utilization_high', pos: 'utilization_position', scale: 1 },
      spr: { name: 'Strategic Petroleum Reserve', unit: 'million barrels', k: 'spr_stocks', scale: 0.001 },
    };
    let inv = 'crude';
    panel({
      id: 'inv', title: 'Inventories and policy: against the five-year range', shade: true, source: X.sources.weekly,
      tools: '<select class="sel" aria-label="Series"><option value="crude">Commercial crude</option><option value="distillate">Distillates</option><option value="utilization">Refinery use</option><option value="spr">SPR</option></select>',
      bind: (el, rr) => { $('.sel', el).onchange = (e) => { inv = e.target.value; rr(); }; },
      traces: () => {
        const S = INV[inv], f = (key) => W[key].map((v) => (v == null ? null : +(v * S.scale).toFixed(2)));
        const t = [];
        if (S.lo) {
          t.push({ type: 'scatter', mode: 'lines', x: W.d, y: f(S.lo), line: { width: 0 }, hoverinfo: 'skip', showlegend: false, connectgaps: false });
          t.push({ type: 'scatter', mode: 'lines', x: W.d, y: f(S.hi), fill: 'tonexty', fillcolor: css('--accent-soft'), line: { width: 0 }, name: 'Five-year range', hovertemplate: 'high %{y:.1f}' });
          t.push(line(W.d, f(S.avg), 'Five-year average', css('--ink-2'), { line: { dash: 'dash', width: 1.2 }, ht: 'avg %{y:.1f}' }));
        }
        t.push(line(W.d, f(S.k), S.name, css('--accent'), { ht: '%{y:.1f}', line: { width: 2 } }));
        return t;
      },
      layout: () => ({ yaxis: { title: { text: INV[inv].unit, font: { size: 11 } } } }),
      summary: (st) => {
        const S = INV[inv], k = onOrBefore(W.d, isoOf(st.day));
        if (k < 0 || W[S.k][k] == null) return 'No weekly reading on or before ' + nice(st.day) + '.';
        const v = W[S.k][k] * S.scale, fmtv = S.unit === '%' ? v.toFixed(1) + '%' : v.toFixed(1) + ' million barrels';
        if (!S.lo) return 'Week ending ' + W.d[k] + ': ' + S.name + ' ' + fmtv + '. Context only; the SPR is not part of the tightness score.';
        if (W[S.avg][k] == null) return 'Week ending ' + W.d[k] + ': ' + S.name + ' ' + fmtv + '. No five-year range yet for this week.';
        return 'Week ending ' + W.d[k] + ': ' + S.name + ' ' + fmtv + ', ' + sgnPct(W[S.k][k] / W[S.avg][k] - 1, 1) + ' against the five-year average, at position ' + W[S.pos][k].toFixed(2) +
          ' (0 = five-year low, 1 = five-year high). The range leaves out 2020 and 2026, the project default.';
      },
      csv: () => { const S = INV[inv], rows = [['week_ending', S.k].concat(S.lo ? [S.lo, S.avg, S.hi, S.pos] : [])];
        W.d.forEach((d, k) => rows.push([d, W[S.k][k]].concat(S.lo ? [W[S.lo][k], W[S.avg][k], W[S.hi][k], W[S.pos][k]] : [])));
        return { name: 'weekly_' + inv + '.csv', rows }; },
    });

    // 7. Positioning
    const C = X.cot;
    panel({
      id: 'cot', title: 'Positioning: net futures positions in WTI, share of open interest', shade: true, source: X.sources.cot,
      traces: () => [line(C.d, C.mm.map((v) => (v == null ? null : 100 * v)), 'Managed money (from June 2006)', css('--accent'), { ht: '%{y:.1f}%' }),
        line(C.d, C.comm.map((v) => (v == null ? null : 100 * v)), 'Commercials (legacy report)', css('--warn'), { ht: '%{y:.1f}%', line: { dash: 'dot' } })],
      layout: () => ({ yaxis: { title: { text: '% of open interest', font: { size: 11 } }, zeroline: true } }),
      summary: (st) => {
        const k = onOrBefore(C.released, isoOf(st.day));
        if (k < 0) return 'No Commitments of Traders report had been released by ' + nice(st.day) + '.';
        const side = (v) => (v >= 0 ? 'net long ' : 'net short ') + Math.abs(100 * v).toFixed(1) + '%';
        return 'In the report measured on ' + C.d[k] + ' (released ' + C.released[k] + ', the latest public by ' + nice(st.day) + '), ' +
          (C.mm[k] == null ? 'managed money was not yet reported separately (it starts in June 2006); ' : 'managed money was ' + side(C.mm[k]) + ' of open interest; ') +
          'commercials were ' + side(C.comm[k]) + '.';
      },
      csv: () => ({ name: 'wti_positioning.csv', rows: [['report_date', 'released', 'managed_money_net_pct_oi', 'commercial_net_pct_oi']].concat(C.d.map((d, k) => [d, C.released[k], C.mm[k], C.comm[k]])) }),
    });

    // 8. Money
    const G = X.gasoline, Ds = X.diesel;
    panel({
      id: 'money', title: 'Money: 10-year yield, the dollar and US retail fuel', shade: true, height: 330, wide: true,
      source: X.sources.ust10y + '; ' + X.sources.usd + '; ' + X.sources.retail,
      traces: () => {
        const u = once('ust', () => xy(D.prices.ust10y)), d = once('usd', () => xy(X.usd));
        return [line(u.x, u.y, '10-year Treasury, %', OKABE[0], { ht: '%{y:.2f}%' }),
          line(d.x, d.y, 'Dollar index (Jan 2006 = 100)', OKABE[1], { ht: '%{y:.1f}', more: { yaxis: 'y2' }, line: { dash: 'dash' } }),
          line(G.d, G.v, 'Retail gasoline, $/gal', OKABE[2], { ht: '$%{y:.2f}', more: { yaxis: 'y3' } }),
          line(Ds.d, Ds.v, 'Retail diesel, $/gal', OKABE[3], { ht: '$%{y:.2f}', more: { yaxis: 'y3' }, line: { dash: 'dot' } })];
      },
      layout: () => ({ yaxis: { domain: [0.7, 1], title: { text: '%', font: { size: 11 } } },
        yaxis2: { domain: [0.37, 0.63], gridcolor: css('--grid'), title: { text: 'Index', font: { size: 11 } } },
        yaxis3: { domain: [0, 0.3], gridcolor: css('--grid'), title: { text: '$/gal', font: { size: 11 } } } }),
      summary: (st) => {
        const iso = isoOf(st.day), u = lastVal(D.prices.ust10y, st.day, 7), d = lastVal(X.usd, st.day, 7);
        const g = onOrBefore(G.d, iso), ds = onOrBefore(Ds.d, iso);
        return 'On ' + nice(st.day) + ': 10-year Treasury yield ' + (u == null ? 'n/a' : u.toFixed(2) + '%') + ', broad dollar index ' + (d == null ? 'n/a (starts January 2006)' : d.toFixed(1)) + '. ' +
          (g >= 0 ? 'US retail gasoline ' + money(G.v[g]) + ' a gallon (week of ' + G.d[g] + ')' : 'Retail gasoline data starts in August 1990') +
          (ds >= 0 ? ', diesel ' + money(Ds.v[ds]) + ' (week of ' + Ds.d[ds] + ').' : '; diesel starts in March 1994.');
      },
      csv: () => { const rows = [['date', 'series', 'value']], u = D.prices.ust10y;
        for (let i = 0; i < N; i++) { const v = val(u, i); if (v != null) rows.push([isoOf(i), 'ust10y_pct_carried_over_weekends', v]); }
        for (let i = 0; i < N; i++) { const v = val(X.usd, i); if (v != null) rows.push([isoOf(i), 'usd_broad_index', v]); }
        G.d.forEach((d, k) => rows.push([d, 'retail_gasoline_usd_gal', G.v[k]])); Ds.d.forEach((d, k) => rows.push([d, 'retail_diesel_usd_gal', Ds.v[k]]));
        return { name: 'money_rates_dollar_fuel.csv', rows }; },
    });

    const io = new IntersectionObserver((es) => es.forEach((e) => {
      const p = panels.find((q) => q.el === e.target); p.visible = e.isIntersecting;
      if (p.visible && !p.built) render(p); else if (p.visible) sync(p, state.get());
    }), { rootMargin: '200px' });
    panels.forEach((p) => io.observe(p.el));
  }

  // ---------- keeping charts on the shared date ----------
  function sync(p, st) {
    if (!p.built) return;
    const iso = isoOf(st.day), upd = { 'shapes[0].x0': iso, 'shapes[0].x1': iso };
    if (range === 'around' && !p.monthly) upd['xaxis.range'] = xrange(st);
    Plotly.relayout(p.chart, upd);
    say(p, st);
  }
  let pending = null, timer = 0;
  function flush() { timer = 0; for (const p of panels) if (p.visible) sync(p, pending); }

  // ---------- lazy start: Plotly and dash.json load when the dashboard nears the screen ----------
  let started = false;
  function start() {
    if (started) return; started = true;
    $('#dashStatus').textContent = 'Loading charts...';
    const load = new Promise((res, rej) => { if (window.Plotly) return res(); const s = document.createElement('script'); s.src = PLOTLY; s.onload = res; s.onerror = () => rej(new Error('Plotly could not load (it needs internet)')); document.head.appendChild(s); });
    Promise.all([load, fetchJSON('data/dash.json'), fetchJSON('data/flows.json')]).then(([, x, f]) => {
      Plotly = window.Plotly; X = x; F = f; buildPanels(); $('#dashStatus').textContent = '';
    }).catch((e) => { $('#dashStatus').textContent = 'The charts could not load: ' + e.message + '. The headline and the spike table still work.'; });
  }
  new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) start(); }, { rootMargin: '600px' }).observe(root);
  $('#dashRange').innerHTML = Object.entries(RANGES).map(([k, v]) => '<option value="' + k + '">' + v + '</option>').join('');
  $('#dashRange').onchange = (e) => { range = e.target.value; panels.forEach((p) => { if (p.built) render(p); }); };

  return {
    start,
    get ready() { return !!X && panels.length > 0; },
    panels,
    update(st) { pending = st; if (!timer && X) timer = setTimeout(flush, st.playing ? 160 : 0); },
    applyTheme() { headline(); panels.forEach((p) => { if (p.built) render(p); }); },
  };
}
