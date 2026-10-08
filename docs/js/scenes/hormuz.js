// Hormuz close-up: a real coastline (Natural Earth) with one moving ship per daily tanker transit
// (Hormuz, 7-day average, IMF PortWatch). The count is real; positions, lanes, routes and directions are a
// display choice, because the data has daily counts, not vessel tracks or origins. Ships are one colour.
import { clamp } from '../data.js';

const FAC_SHORT = { 'basra-oil-company-fields': 'Basra fields', 'kuwait-oilfields-kpc': 'Kuwait fields',
                    'safaniya-and-zuluf-offshore-fields': 'Safaniya and Zuluf', 'adnoc-oilfields': 'ADNOC fields', 'iranian-ports': 'Iranian ports' };

export function createHormuz({ THREE, addLabel, THEME, data, reduceMotion }) {
  const REG = data.D.region, LON0 = 54.25, LAT0 = 27.0, KX = 0.891;
  const px = (lon) => (lon - LON0) * KX, pz = (lat) => -(lat - LAT0);
  const group = new THREE.Group();
  const seaMat = new THREE.MeshBasicMaterial(), landMat = new THREE.MeshLambertMaterial({ side: THREE.DoubleSide });
  const edgeMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 });
  const laneMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.45 });
  const markMat = new THREE.MeshLambertMaterial();
  {
    const b = REG.land.box;
    const sea = new THREE.Mesh(new THREE.PlaneGeometry(px(b[2]) - px(b[0]), pz(b[1]) - pz(b[3])), seaMat);
    sea.rotation.x = -Math.PI / 2; sea.position.set((px(b[0]) + px(b[2])) / 2, -0.004, (pz(b[1]) + pz(b[3])) / 2); group.add(sea);
    const ring = (r) => r.map(([lo, la]) => new THREE.Vector2(px(lo), -pz(la)));
    for (const poly of REG.land.polygons) {
      const shape = new THREE.Shape(ring(poly[0]));
      for (const h of poly.slice(1)) shape.holes.push(new THREE.Path(ring(h)));
      const m = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: 0.05, bevelEnabled: false }), landMat);
      m.rotation.x = -Math.PI / 2; group.add(m);
      for (const r of poly) group.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(r.map(([lo, la]) => new THREE.Vector3(px(lo), 0.053, pz(la)))), edgeMat));
    }
  }
  const lanes = REG.lanes.map((l) => {
    const pts = l.pts.map(([lo, la]) => new THREE.Vector3(px(lo), 0.012, pz(la)));
    const seg = []; let len = 0;
    for (let i = 1; i < pts.length; i++) { const d = pts[i].distanceTo(pts[i - 1]); seg.push(d); len += d; }
    group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), laneMat));
    return { ...l, pts, seg, len };
  });
  const cycle = [];                                         // slot k -> lane, by display weight
  { const maxW = Math.max(...lanes.map((l) => l.weight)); for (let r = 0; r < maxW; r++) lanes.forEach((l, i) => { if (r < l.weight) cycle.push(i); }); }
  const MAXSHIPS = 120, SHIP_SPEED = 0.5;
  const hull = new THREE.Shape([[-0.1, -0.03], [0.06, -0.03], [0.11, 0], [0.06, 0.03], [-0.1, 0.03]].map(([x, y]) => new THREE.Vector2(x, y)));
  const hullGeo = new THREE.ExtrudeGeometry(hull, { depth: 0.04, bevelEnabled: false }); hullGeo.rotateX(-Math.PI / 2);
  const shipMat = new THREE.MeshLambertMaterial();
  const ships = new THREE.InstancedMesh(hullGeo, shipMat, MAXSHIPS); ships.count = 0; ships.frustumCulled = false; group.add(ships);
  let n = 0, v = null;
  const _p = new THREE.Vector3(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(1.4, 1.4, 1.4), _m = new THREE.Matrix4(), _y = new THREE.Vector3(0, 1, 0);
  const counts = new Array(lanes.length).fill(0), idx = new Array(lanes.length).fill(0);   // reused, no per-frame allocation

  function animate(t) {
    counts.fill(0); idx.fill(0);
    for (let k = 0; k < n; k++) counts[cycle[k % cycle.length]]++;
    for (let k = 0; k < n; k++) {
      const li = cycle[k % cycle.length], L = lanes[li], j = idx[li]++;
      const inbound = j % 2 === 1;                         // display only: alternate directions so lanes look two-way
      let u = (j / counts[li] + li * 0.19 + t * SHIP_SPEED / L.len) % 1;  // fixed phase per slot: same date, same picture
      if (inbound) u = 1 - u;
      let d = u * L.len, i = 0;
      while (i < L.seg.length - 1 && d > L.seg[i]) { d -= L.seg[i]; i++; }
      const a = L.pts[i], b = L.pts[i + 1], f = clamp(d / L.seg[i], 0, 1);
      let dx = b.x - a.x, dz = b.z - a.z; const m = Math.hypot(dx, dz) || 1;
      dx /= m; dz /= m;
      const side = inbound ? 0.04 : -0.04;
      _p.set(a.x + (b.x - a.x) * f - dz * side, 0.012, a.z + (b.z - a.z) * f + dx * side);
      if (inbound) { dx = -dx; dz = -dz; }
      _q.setFromAxisAngle(_y, Math.atan2(-dz, dx));
      ships.setMatrixAt(k, _m.compose(_p, _q, _s));
    }
    ships.instanceMatrix.needsUpdate = true;
  }
  const facMarks = REG.facilities.map((f) => {
    const g = new THREE.Group(); g.position.set(px(f.lon), 0.05, pz(f.lat));
    g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.32, 6).translate(0, 0.16, 0), markMat));
    const head = new THREE.Mesh(new THREE.OctahedronGeometry(0.065), markMat); head.position.y = 0.36; g.add(head);
    const hit = new THREE.Mesh(new THREE.SphereGeometry(0.17), new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }));
    hit.position.y = 0.3; hit.userData.fac = f; g.add(hit); group.add(g);
    addLabel('<b>' + (FAC_SHORT[f.id] || f.name) + '</b>', new THREE.Vector3(g.position.x, 0.5, g.position.z), { group: 'hz' });
    return { f, hit };
  });
  const gateMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.2, side: THREE.DoubleSide, depthWrite: false });
  {
    const gate = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.32), gateMat);
    gate.rotation.y = Math.PI / 2; gate.position.set(px(56.4), 0.16, pz(26.58)); group.add(gate);
    addLabel('<b>Strait of Hormuz</b>', new THREE.Vector3(px(56.4), 0.4, pz(26.58)), { group: 'hz' });
    [['Persian Gulf', 28.7, 50.6], ['Gulf of Oman', 24.25, 58.3]].forEach(([t, la, lo]) => addLabel(t, new THREE.Vector3(px(lo), 0.02, pz(la)), { dim: true, group: 'hz' }));
    [['IRAN', 28.7, 54.0], ['SAUDI ARABIA', 25.9, 48.7], ['UAE', 24.2, 54.9], ['OMAN', 23.5, 57.4]].forEach(([t, la, lo]) => addLabel(t, new THREE.Vector3(px(lo), 0.06, pz(la)), { dim: true, group: 'hz' }));
  }
  const H = data.hormuz;

  return {
    key: 'hz', group, animated: true,
    camera: { pos: new THREE.Vector3(-0.3, 10.6, 9.6), target: new THREE.Vector3(-0.5, 0, 0.1), min: 2.5, max: 18, maxPolar: 1.42, pan: true },
    hint: () => 'Drag to rotate, right-drag to pan, scroll to zoom.' + (REG.facilities.length ? ' Hover a pin.' : ''),
    legend: () => '<span><span class="sw" style="background:var(--accent)"></span>Ship: one per daily tanker transit (no direction or origin in the data)</span><span><span class="sw" style="background:none;border:0;border-top:2px solid var(--accent);height:0;vertical-align:4px"></span>Schematic lane</span>' + (REG.facilities.length ? '<span>Diamond pin: facility tied to a hand-checked event</span>' : ''),
    caption: () => 'Each moving ship stands for one tanker transit a day (Hormuz, 7-day average, IMF PortWatch). The count is real. Positions, lanes, which route each ship takes and which way it sails are a display choice, because the data has daily counts, not vessel tracks or origins. ' +
      (REG.facilities.length ? 'Pins use approximate coordinates and appear only for facilities tied to hand-checked events.' : 'Facility pins appear once the event rows behind them have been hand-checked.'),
    note: (st) => v == null
      ? '<b>No ships drawn</b> &middot; IMF PortWatch tanker counts start on January 1, 2019'
      : '<b>' + n + (n === 1 ? ' ship' : ' ships') + ' drawn</b> &middot; Hormuz tanker transits ' + v.toFixed(1) + ' a day (7-day average), ' +
        Math.round(100 * v / H.baseline) + '% of the usual ' + H.baseline + ' a day',
    applyTheme() { seaMat.color.copy(THEME.hzSea); landMat.color.copy(THEME.hzLand); edgeMat.color.copy(THEME.axis); laneMat.color.copy(THEME.accent);
                   markMat.color.copy(THEME.ink); shipMat.color.copy(THEME.accent); gateMat.color.copy(THEME.accent); },
    update(st) {
      v = data.lastVal(H.tankers7, st.day);
      n = v == null ? 0 : clamp(Math.round(v), 0, MAXSHIPS);
      ships.count = n;
      animate(reduceMotion ? 0 : performance.now() / 1000);
    },
    animate,
    pick(ray) {
      const hit = ray.intersectObjects(facMarks.map((m) => m.hit), false)[0];
      if (!hit) return null;
      const f = hit.object.userData.fac;
      return '<b>' + f.name + '</b><br>' + f.type + (f.country ? ', ' + f.country : '') + '<br><span style="color:var(--ink-2)">From the project’s facility table. Location approximate.</span>';
    },
    aria: (st, nice) => '3D map of the Persian Gulf and Strait of Hormuz on ' + nice(st.day) + ' with ' + n + ' ships drawn, one for each tanker transit a day',
  };
}
