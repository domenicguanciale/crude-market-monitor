// Price terrain: Brent and WTI daily spot (EIA) as two walls that run through time, 1986 (far) to today (near).
// Wall height = price in $/bbl. Wall colour = that benchmark's 20-day realized volatility, in sevenths of all
// trading days (spikes.py). A price below zero hangs under the floor as a trench (WTI, April 20, 2020).
// Pins mark the spikes found by the rules in spikes.py. Their tooltips give rule facts only; an explanation
// appears only once the user has hand-checked that spike.
import { fmt, pct } from '../data.js';

const XS = 0.0075, YS = 0.025;                               // world units per day, per dollar
const KIND = { daily: 'One-day move', surge: 'Surge', crash: 'Crash', drawdown: 'Drawdown, peak to trough', spread: 'Brent minus WTI blowout' };
const EPISODES = new Set(['surge', 'crash', 'drawdown', 'spread']);

export function createPrice({ THREE, addLabel, THEME, data }) {
  const { N, D, val, lastVal, dayOf, nice, isoOf } = data;
  const L = (N - 1) * XS, x = (i) => (i - (N - 1)) * XS;
  const group = new THREE.Group();
  const benches = [
    { key: 'brent', name: 'Brent', z: -0.35, ser: D.prices.brent, rv: data.market.rv20.brent },
    { key: 'wti', name: 'WTI', z: 0.35, ser: D.prices.wti, rv: data.market.rv20.wti },
  ];
  const sevenths = (ser) => { const a = Float64Array.from(data.values(ser)).sort(); return [1, 2, 3, 4, 5, 6].map((k) => a[Math.floor(k * a.length / 7)]); };
  const binOf = (cuts, v) => { if (v == null) return -1; let b = 0; while (b < 6 && v >= cuts[b]) b++; return b; };

  // ---------- the walls ----------
  const wallMat = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide });
  const edgeMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.75 });
  for (const b of benches) {
    b.cuts = sevenths(b.rv);
    const pos = [], bins = [], idx = [], edge = [];
    let prev = -1;
    for (let i = 0; i < N; i++) {
      const p = val(b.ser, i);
      if (p == null) { prev = -1; continue; }
      const k = pos.length / 3;
      pos.push(x(i), p * YS, b.z, x(i), 0, b.z);
      bins.push(binOf(b.cuts, lastVal(b.rv, i, 7)));
      if (prev >= 0) { idx.push(prev, prev + 1, k, k, prev + 1, k + 1); edge.push(x(i - 1), val(b.ser, i - 1) * YS, b.z, x(i), p * YS, b.z); }
      prev = k;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(new Float32Array(pos.length), 3));
    geo.setIndex(idx);
    b.geo = geo; b.bins = bins;
    group.add(new THREE.Mesh(geo, wallMat));
    const eg = new THREE.BufferGeometry(); eg.setAttribute('position', new THREE.Float32BufferAttribute(edge, 3));
    group.add(new THREE.LineSegments(eg, edgeMat));
  }
  const tmpC = new THREE.Color(), lowC = new THREE.Color();
  function recolor() {
    for (const b of benches) {
      const col = b.geo.getAttribute('color');
      b.bins.forEach((bin, k) => {
        tmpC.copy(bin < 0 ? THEME.axis : THEME.ramp[bin]);
        lowC.copy(tmpC).lerp(THEME.surface, 0.55);
        col.setXYZ(2 * k, tmpC.r, tmpC.g, tmpC.b); col.setXYZ(2 * k + 1, lowC.r, lowC.g, lowC.b);
      });
      col.needsUpdate = true;
    }
  }

  // ---------- floor, price grid, year ticks ----------
  const floorMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.35, depthWrite: false, side: THREE.DoubleSide });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(L + 1, 2.2), floorMat);
  floor.rotation.x = -Math.PI / 2; floor.position.set(-L / 2, 0, 0); group.add(floor);
  const gridMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 });
  {
    const g = [];
    for (const usd of [50, 100, 150]) g.push(-L - 0.5, usd * YS, -1.1, 0.5, usd * YS, -1.1);
    const y0 = data.firstYear, y1 = Number(isoOf(N - 1).slice(0, 4));
    for (let y = y0 + 1; y <= y1; y++) { const xx = x(dayOf(y + '-01-01')); g.push(xx, 0.001, -1.1, xx, 0.001, 1.1); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(g, 3));
    group.add(new THREE.LineSegments(geo, gridMat));
    for (let y = Math.ceil(y0 / 5) * 5; y <= y1; y += 5) addLabel(String(y), new THREE.Vector3(x(dayOf(y + '-01-01')), 0, 1.25), { dim: true, group: 'price' });
  }
  const axisLabels = [0, 50, 100, 150].map((usd) => ({ usd, l: addLabel('$' + usd, new THREE.Vector3(0, usd * YS, -1.15), { dim: true, group: 'price' }) }));

  // The lowest print on either wall, labelled where it is (the trench, if below zero).
  {
    let lo = { v: Infinity };
    for (const b of benches) for (let i = b.ser.s; i < b.ser.s + b.ser.v.length; i++) { const v = val(b.ser, i); if (v != null && v < lo.v) lo = { v, i, b }; }
    if (lo.v < 0) addLabel('<b>' + lo.b.name + ' ' + (lo.v < 0 ? '−$' + Math.abs(lo.v).toFixed(2) : '$' + lo.v.toFixed(2)) + '</b> on ' + nice(lo.i),
                           new THREE.Vector3(x(lo.i), lo.v * YS - 0.12, lo.b.z + 0.3), { group: 'price' });
  }

  // ---------- the date cursor ----------
  const curMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.1, side: THREE.DoubleSide, depthWrite: false });
  const cursor = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 5.6), curMat);
  cursor.rotation.y = Math.PI / 2; group.add(cursor);
  const dotMat = new THREE.MeshBasicMaterial();
  const dots = benches.map((b) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.05, 16, 12), dotMat); group.add(m);
    return { b, m, l: addLabel('', new THREE.Vector3(), { group: 'price' }) }; });

  // ---------- spike pins ----------
  const spikes = data.spikes.map((s) => {
    const b = benches.find((q) => q.name === s.b) || benches[0];            // spread blowouts sit on the Brent wall
    const day = dayOf(s.d1), p = val(b.ser, day);
    return { s, day, z: b.z, y: Math.max(p == null ? 0 : p, 0) * YS };
  });
  const stickGeo = new THREE.BoxGeometry(0.008, 1, 0.008).translate(0, 0.5, 0);
  const headGeo = new THREE.ConeGeometry(0.04, 0.09, 10);
  const pinMat = new THREE.MeshBasicMaterial(), stickMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.6 });
  const sticks = new THREE.InstancedMesh(stickGeo, stickMat, spikes.length);
  const heads = new THREE.InstancedMesh(headGeo, pinMat, spikes.length);
  const hits = new THREE.InstancedMesh(new THREE.SphereGeometry(0.07, 8, 6), new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }), spikes.length);
  heads.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(spikes.length * 3), 3);
  for (const m of [sticks, heads, hits]) { m.frustumCulled = false; group.add(m); }
  let pinMode = 'episodes', shown = [];
  const STICK = 0.32, _m = new THREE.Matrix4(), _p = new THREE.Vector3(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(), _x = new THREE.Vector3(1, 0, 0);
  function layoutPins() {
    shown = spikes.filter((k) => pinMode === 'all' || (pinMode === 'episodes' && EPISODES.has(k.s.k)));
    shown.forEach((k, n) => {
      const top = k.y + STICK;
      sticks.setMatrixAt(n, _m.compose(_p.set(x(k.day), k.y, k.z), _q.identity(), _s.set(1, STICK, 1)));
      _q.setFromAxisAngle(_x, k.s.dir === 'down' ? Math.PI : 0);
      heads.setMatrixAt(n, _m.compose(_p.set(x(k.day), top + 0.045, k.z), _q, _s.set(1, 1, 1)));
      hits.setMatrixAt(n, _m.compose(_p, _q.identity(), _s));
    });
    for (const m of [sticks, heads, hits]) { m.count = shown.length; m.instanceMatrix.needsUpdate = true; }
    pinColors();
  }
  function pinColors() {
    shown.forEach((k, n) => heads.setColorAt(n, k.s.dir === 'down' ? THEME.warn : THEME.accent));
    heads.instanceColor.needsUpdate = true;
  }
  layoutPins();

  const money = (v) => (v == null ? 'n/a' : (v < 0 ? '−$' : '$') + Math.abs(v).toFixed(2));
  function pinHtml(s) {
    const usd = s.usd == null ? '' : ' (' + (s.usd > 0 ? '+' : '−') + '$' + Math.abs(s.usd).toFixed(2) + ')';
    const size = s.k === 'spread' ? '' : s.pct != null ? (s.pct > 0 ? '+' : '−') + Math.abs(100 * s.pct).toFixed(1) + '%' + usd + '<br>'
      : s.neg ? 'Percent change not defined, because a price was at or below zero' + usd + '<br>' : '';
    const what = s.k === 'spread' ? 'Brent minus WTI ' + money(s.p0) + ' at the start, ' + money(s.p1) + ' at the widest' : s.b + ' ' + money(s.p0) + ' to ' + money(s.p1);
    let h = '<b>' + KIND[s.k] + (s.k === 'spread' ? '' : ', ' + s.b) + '</b><br>' + (s.d0 === s.d1 ? s.d1 : s.d0 + ' to ' + s.d1) + '<br>' + what + '<br>' + size +
            'Rule: ' + s.rule;
    if (s.unconfirmed) h += '<br><b>Unconfirmed print:</b> kept as published, see docs/SPIKES.md';
    if (s.checked && s.note) h += '<br><br>' + s.note + '<br><span style="color:var(--ink-2)">Sources: ' + s.sources.map((q) => q[0]).join('; ') + '</span>';
    else h += '<br><span style="color:var(--ink-2)">Explanation not yet hand-checked, so none is shown.</span>';
    return h + '<br><span style="color:var(--ink-2)">Found by rule from EIA daily spot prices (spikes.py). Click to jump to this date.</span>';
  }
  const pickPin = (ray) => { const hit = ray.intersectObject(hits, false)[0]; return hit && hit.instanceId != null ? shown[hit.instanceId] : null; };

  return {
    key: 'price', group,
    camera: { relative: true, pos: new THREE.Vector3(6.5, 4.0, 4.6), target: new THREE.Vector3(-10, 1.5, 0), min: 1.5, max: 60, maxPolar: 1.55, pan: true },
    follow: (st) => new THREE.Vector3(x(st.day), 0, 0),
    options: () => ({ pins: pinMode }),
    setOption(k, v) { if (k === 'pins') { pinMode = v; layoutPins(); } },
    hint: () => 'Drag to rotate, right-drag to pan, scroll to zoom. The camera follows the date. Hover or click a pin.',
    legend: () => '<span><span class="ramp">' + THEME.ramp.map((c) => '<i style="background:#' + c.getHexString() + '"></i>').join('') +
      '</span>Wall colour: 20-day volatility, calmest to most turbulent seventh of all trading days</span>' +
      '<span>Back wall: Brent. Front wall: WTI. Height: $ per barrel</span>' +
      '<span><b style="color:var(--accent)">▲</b> pin: rise &nbsp; <b style="color:var(--warn)">▼</b> pin: fall</span>',
    caption: (st) => 'Daily spot prices from EIA, ' + nice(0) + ' to ' + nice(N - 1) + '. Today is nearest the camera and 1986 is farthest. ' +
      'Pins mark ' + shown.length + ' of the ' + spikes.length + ' spikes found by fixed rules (' +
      (pinMode === 'episodes' ? 'surges, crashes, drawdowns and spread blowouts; choose "All" to add one-day moves' : pinMode === 'all' ? 'all kinds' : 'pins hidden') +
      '). Rules found them, not judgement, and the page gives no cause for any spike that has not been hand-checked.',
    explain: () => '<p>Two walls run through time. The back wall is Brent and the front wall is WTI. Each wall’s top edge is that day’s spot price in dollars per barrel (EIA). ' +
      'The camera follows the selected date, so pressing play flies you along the price history. The far end is 1986.</p>' +
      '<p>Colour shows how violently the price was moving: the 20-day realized volatility, split into sevenths of all trading days. Blue is the calmest seventh, orange the most turbulent. ' +
      'On April 20, 2020 WTI settled below zero, and its wall drops under the floor as a trench.</p>' +
      '<p>Pins mark moves found by the fixed rules in spikes.py: one-day shocks, surges, crashes, drawdowns and Brent minus WTI blowouts. Hover for the dates, size and rule; click to jump there. ' +
      'This shows what happened to the price, not why.</p>',
    applyTheme() {
      recolor(); pinColors();
      floorMat.color.copy(THEME['surface-2']); gridMat.color.copy(THEME.axis); edgeMat.color.copy(THEME.ink);
      curMat.color.copy(THEME.accent); dotMat.color.copy(THEME.ink); stickMat.color.copy(THEME.ink);
    },
    update(st) {
      const cx = x(st.day);
      cursor.position.set(cx, 1.6, 0);
      for (const a of axisLabels) a.l.pos.x = cx - 0.15;
      for (const d of dots) {
        const p = val(d.b.ser, st.day);
        d.m.visible = p != null;
        d.m.position.set(cx, (p ?? 0) * YS, d.b.z);
        d.l.pos.set(cx, (p ?? 0) * YS + 0.18, d.b.z);
        d.l.el.innerHTML = '<b>' + d.b.name + '</b> ' + (p == null ? 'no price' : money(p));
      }
    },
    pick(ray) { const k = pickPin(ray); return k ? pinHtml(k.s) : null; },
    select(ray) { const k = pickPin(ray); return k ? k.day : null; },
    probe(st, id) {                                          // the given pin, or the pin nearest the selected date
      const k = id ? shown.find((q) => q.s.id === id)
        : shown.reduce((best, q) => (!best || Math.abs(q.day - st.day) < Math.abs(best.day - st.day) ? q : best), null);
      return k ? new THREE.Vector3(x(k.day), k.y + STICK + 0.045, k.z) : null;
    },
    aria: (st) => '3D price walls for Brent and WTI from 1986 to today. On ' + nice(st.day) + ': Brent ' + fmt(val(D.prices.brent, st.day)) +
      ', WTI ' + fmt(val(D.prices.wti, st.day)) + ' dollars a barrel. Brent 20-day volatility ' + pct(lastVal(data.market.rv20.brent, st.day, 7)) + '.',
  };
}
