// Skyline: one bar per week. Rows are years (1986 at the back, this year at the front), columns are weeks of the year.
// Three measures share the same grid, so they can be compared at a glance:
// - score: the US tightness score (-3 loose to +3 tight), computed twice by export_3d.py (2020 out by default, or kept in)
// - vol:   20-day realized volatility of Brent or WTI on the last trading day of the week (spikes.py)
// - price: average spot price over the week's trading days (EIA)
import { label, signed, pct } from '../data.js';

export const MEASURES = { score: 'Tightness score', vol: 'Volatility, 20-day', price: 'Price level' };

export function createSkyline({ THREE, addLabel, THEME, data }) {
  const { weeks, isoOf, dayOf } = data;
  const FIRST_YEAR = data.firstYear;
  const LAST_YEAR = Number(isoOf(data.N - 1).slice(0, 4));
  const years = LAST_YEAR - FIRST_YEAR + 1;
  const group = new THREE.Group();
  const DX = 0.15, DZ = 0.2;
  const xOf = (w) => (w - 27) * DX, zOf = (y) => (y - FIRST_YEAR - (years - 1) / 2) * DZ;
  const floor = new THREE.Mesh(new THREE.BoxGeometry(53 * DX + 0.2, 0.01, years * DZ + 0.2),
                               new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.55 }));
  floor.position.set(xOf(27), -0.006, 0); group.add(floor);
  const cursorBox = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), new THREE.LineBasicMaterial());
  group.add(cursorBox);
  const sliceMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.1, side: THREE.DoubleSide, depthWrite: false });
  const weekSlice = new THREE.Mesh(new THREE.PlaneGeometry(years * DZ, 1.6), sliceMat);
  weekSlice.rotation.y = Math.PI / 2; group.add(weekSlice);
  const barMat = new THREE.MeshLambertMaterial();
  const tmpM = new THREE.Matrix4(), tmpP = new THREE.Vector3(), tmpS = new THREE.Vector3(), tmpQ = new THREE.Quaternion(), tmpC = new THREE.Color();

  // ---------- one layer per measure (and benchmark), built the first time it is shown ----------
  const sevenths = (vals) => { const a = Float64Array.from(vals).sort(); return [1, 2, 3, 4, 5, 6].map((k) => a[Math.floor(k * a.length / 7)]); };
  const binOf = (cuts, v) => { let b = 0; while (b < 6 && v >= cuts[b]) b++; return b; };
  const layers = {};
  function rowsFor(measure, bench) {
    if (measure === 'score') return weeks.map((w) => ({ y: w.y, w: w.w, d: w.d, src: w }));
    return (data.market.weekly[bench] || []).filter((r) => (measure === 'vol' ? r[4] : r[3]) != null)
      .map((r) => ({ y: r[0], w: r[1], d: r[2], price: r[3], vol: r[4] }));
  }
  function layer(st, bench) {
    const key = st.measure === 'score' ? 'score' : st.measure + ':' + bench;
    if (layers[key]) return layers[key];
    const rows = rowsFor(st.measure, bench).filter((r) => r.y >= FIRST_YEAR && r.y <= LAST_YEAR);
    const day = Int32Array.from(rows.map((r) => dayOf(r.d)));
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), barMat, Math.max(rows.length, 1));
    mesh.count = rows.length;
    mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(Math.max(rows.length, 1) * 3), 3);
    group.add(mesh);
    const L = { key, measure: st.measure, bench, rows, day, mesh, laidOut: null };
    if (st.measure !== 'score') {
      const vals = rows.map((r) => r[st.measure]);
      L.cuts = sevenths(vals);
      L.max = Math.max(...vals);
    }
    layers[key] = L;
    return L;
  }
  const HU = { score: 0.13, vol: 0.4, price: 0.009 };        // world units per score point, per 100% volatility, per dollar
  const value = (L, r, st) => {
    if (L.measure === 'score') { const s = r.src[st.keep2020 ? 'in' : 'out']; return s ? s[0] : null; }
    return r[L.measure];
  };
  const heightOf = (L, v) => Math.max(Math.abs(v == null ? 0 : v) * HU[L.measure], 0.012);
  const colourOf = (L, v) => (L.measure === 'score' ? THEME.ramp[(v ?? 0) + 3] : THEME.ramp[binOf(L.cuts, v)]);
  function layout(L, st) {
    const mode = L.measure === 'score' ? (st.keep2020 ? 'in' : 'out') : 'one';
    if (L.laidOut === mode) return;
    L.rows.forEach((r, n) => {
      const v = value(L, r, st), h = heightOf(L, v);
      tmpP.set(xOf(r.w), (v ?? 0) >= 0 ? h / 2 : -h / 2, zOf(r.y));
      L.mesh.setMatrixAt(n, tmpM.compose(tmpP, tmpQ.identity(), tmpS.set(DX * 0.82, h, DZ * 0.78)));
    });
    L.mesh.instanceMatrix.needsUpdate = true; L.mesh.computeBoundingSphere();
    L.laidOut = mode;
  }
  const cutAt = (L, d) => { let lo = 0, hi = L.day.length; while (lo < hi) { const m = (lo + hi) >> 1; if (L.day[m] <= d) lo = m + 1; else hi = m; } return lo - 1; };

  // ---------- labels ----------
  {
    const front = zOf(LAST_YEAR) + 0.28;
    [[1, 'Jan'], [14, 'Apr'], [27, 'Jul'], [40, 'Oct']].forEach(([wk, t]) => addLabel(t, new THREE.Vector3(xOf(wk), 0, front), { dim: true, group: 'sky' }));
    const left = xOf(1) - 0.3;
    for (let y = FIRST_YEAR; y <= LAST_YEAR; y++) if (y % 5 === 0 || y === FIRST_YEAR || (y === LAST_YEAR && y % 5 > 1))
      addLabel(String(y), new THREE.Vector3(left, 0, zOf(y)), { dim: true, group: 'sky' });
  }
  const rx = xOf(53) + 0.55, rz = zOf(LAST_YEAR);
  const axis = [0, 1, 2].map(() => addLabel('', new THREE.Vector3(rx, 0, rz), { dim: true, group: 'sky' }));
  const AXIS = {
    score: [['+3 tight', 3 * HU.score], ['0', 0], ['−3 loose', -3 * HU.score]],
    vol: [['200%', 2 * HU.vol], ['100%', HU.vol], ['0', 0]],
    price: [['$100', 100 * HU.price], ['$50', 50 * HU.price], ['$0', 0]],
  };

  let bench = 'brent', active = null, shownKey = null;
  const benchName = () => (bench === 'wti' ? 'WTI' : 'Brent');

  return {
    key: 'sky', group,
    camera: { pos: new THREE.Vector3(1.2, 9.6, 11.6), target: new THREE.Vector3(0, -0.1, 0.1), min: 4, max: 24, maxPolar: 1.52, pan: false },
    options: () => ({ bench }),
    setOption(k, v) { if (k === 'bench') bench = v; },
    hint: () => 'Drag to rotate. Scroll or pinch to zoom. Hover a bar.',
    legend: (st) => {
      const ramp = '<span class="ramp">' + THEME.ramp.map((c) => '<i style="background:#' + c.getHexString() + '"></i>').join('') + '</span>';
      const key = st.measure === 'score' ? ramp + '−3 loose &nbsp; 0 &nbsp; +3 tight'
        : ramp + (st.measure === 'vol' ? 'Calmest to most turbulent seventh of all weeks' : 'Cheapest to dearest seventh of all weeks');
      return '<span>' + key + '</span><span>Rows: years, ' + FIRST_YEAR + ' back to ' + LAST_YEAR + ' front</span><span>Columns: week of the year</span><span>Faded: after the selected date</span>';
    },
    caption: (st) => {
      if (st.measure === 'vol') return 'Each bar is one week: ' + benchName() + '’s 20-day realized volatility on the last trading day of the week, annualized, computed from EIA daily spot prices. Height is the volatility (100% means a typical yearly swing as large as the price itself). Rows before ' + benchName() + ' prices start are empty.';
      if (st.measure === 'price') return 'Each bar is one week: the average ' + benchName() + ' spot price over that week’s trading days (EIA), in dollars per barrel.';
      return data.weekIdxAt[st.day] < 0
        ? 'Tightness scores start in November 1995, the first week with five full prior years of data. Move the date later to see the skyline fill in.'
        : 'Each bar is one week. The score adds three points: crude stocks, distillate stocks and refinery use, each against the same week in the prior five years. Rows before 1996 are empty because scores start in November 1995.';
    },
    explain: (st) => st.measure === 'score'
      ? '<p>One bar per week, with years in rows and weeks of the year in columns. Height and colour show the US tightness score, from −3 (loose) to +3 (tight). ' +
        'It adds one point for each of crude stocks, distillate stocks and refinery use that sits at an extreme against the same week in the prior five years. ' +
        'The switch keeps 2020 in the five-year range; the default leaves it out because the pandemic swelled stocks.</p>'
      : '<p>The same grid of years and weeks, now showing ' + (st.measure === 'vol' ? 'how violently the ' + benchName() + ' price moved: its 20-day realized volatility, annualized. A tall row is a turbulent year, so 2026 can be compared with 1990, 2008 and 2020 at a glance.'
        : 'the ' + benchName() + ' price level: the average spot price of each week.') +
        ' Colour splits all weeks into sevenths. Data: EIA daily spot prices; volatility computed in spikes.py.</p>',
    applyTheme() { floor.material.color.copy(THEME['surface-2']); cursorBox.material.color.copy(THEME.ink); sliceMat.color.copy(THEME.accent); barMat.color.set(0xffffff); shownKey = null; },
    update(st) {
      active = layer(st, bench);
      for (const L of Object.values(layers)) L.mesh.visible = L === active;
      layout(active, st);
      AXIS[st.measure].forEach(([t, y], k) => { axis[k].el.textContent = t; axis[k].pos.y = y; });
      const cut = st.measure === 'score' ? data.weekIdxAt[st.day] : cutAt(active, st.day);
      const stamp = active.key + (st.keep2020 ? 'k' : '') + ':' + cut;
      if (stamp !== shownKey) {
        active.rows.forEach((r, n) => {
          tmpC.copy(colourOf(active, value(active, r, st)));
          if (n > cut) tmpC.lerp(THEME.surface, 0.82);
          active.mesh.setColorAt(n, tmpC);
        });
        active.mesh.instanceColor.needsUpdate = true;
        shownKey = stamp;
      }
      cursorBox.visible = weekSlice.visible = cut >= 0;
      if (cut < 0) return;
      const r = active.rows[cut], v = value(active, r, st), h = heightOf(active, v);
      cursorBox.position.set(xOf(r.w), (v ?? 0) >= 0 ? h / 2 : -h / 2, zOf(r.y));
      cursorBox.scale.set(DX * 1.1, h + 0.03, DZ * 1.05);
      weekSlice.position.set(xOf(r.w), 0, 0);
    },
    pick(ray, camera, st) {
      if (!active) return null;
      const hit = ray.intersectObject(active.mesh, false)[0];
      if (!hit || hit.instanceId == null) return null;
      const r = active.rows[hit.instanceId];
      if (active.measure === 'score') {
        const s = r.src[st.keep2020 ? 'in' : 'out'];
        if (!s) return null;
        return '<b>Week ending ' + r.d + '</b><br>Score ' + signed(s[0]) + ' (' + label(s[0]) + ')<br>Crude stocks ' + s[1].toFixed(2) +
               ', distillate ' + s[2].toFixed(2) + ', refinery use ' + s[3].toFixed(2) + '<br><span style="color:var(--ink-2)">0 = five-year low, 1 = five-year high. Source: EIA weekly data</span>';
      }
      return '<b>Week ending ' + r.d + '</b><br>' + benchName() + ' 20-day volatility ' + pct(r.vol) + ' (annualized)<br>Average price $' + r.price.toFixed(2) +
             '<br><span style="color:var(--ink-2)">Computed from EIA daily spot prices (spikes.py)</span>';
    },
    probe(st) {
      if (!active) return null;
      const cut = st.measure === 'score' ? data.weekIdxAt[st.day] : cutAt(active, st.day);
      if (cut < 0) return null;
      const r = active.rows[cut], v = value(active, r, st), h = heightOf(active, v);
      return new THREE.Vector3(xOf(r.w), (v ?? 0) >= 0 ? h * 0.75 : -h * 0.25, zOf(r.y));
    },
    aria: (st) => {
      if (st.measure !== 'score') return '3D skyline of weekly ' + benchName() + ' ' + (st.measure === 'vol' ? 'volatility' : 'prices') + ', ' + FIRST_YEAR + ' to ' + LAST_YEAR;
      const n = data.weekIdxAt[st.day];
      if (n < 0) return '3D skyline of weekly US tightness scores. Scores start in November 1995.';
      const w = weeks[n], r = w[st.keep2020 ? 'in' : 'out'];
      return '3D skyline of weekly US tightness scores. Week ending ' + w.d + ' scores ' + (r ? signed(r[0]) + ', ' + label(r[0]) : 'n/a');
    },
  };
}
