// World flows: measured data only, by month (docs/data/flows.json, loaded the first time this view opens).
// - Tier B columns: crude oil production by country (EIA international data), height = thousand b/d,
//   colour = change from that country's 2025 monthly average.
// - Tier A arcs: US crude oil imports by country of origin (EIA), thickness = thousand b/d. Solid, because measured.
// - Chokepoint pillars as on the globe.
// Tier C (modeled worldwide allocation, ipf.py) is never drawn: there are no publishable totals or prior for it.
import { makeEarth, makePillars, latLon } from './earth.js';

const PSCALE = 0.42 / 14000;                                   // world units per thousand b/d of production
const CARRY_MONTHS = 6;                                        // show the latest month for up to 6 months past it, labelled
export const REGIONS = ['All', 'Africa', 'Americas', 'Asia', 'Europe', 'Oceania'];

export function createFlows(ctx) {
  const { THREE, addLabel, THEME, data } = ctx;
  const R = 1, ll = latLon(THREE, R);
  const group = new THREE.Group();
  const earth = makeEarth(ctx, R); group.add(earth.group);
  const pil = makePillars(ctx, group, 'flows', { scale: 0.0035, radius: 0.012 });
  const colMat = new THREE.MeshLambertMaterial(), arcMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.85 });
  const hitMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
  let F = null, cols = null, arcs = [], usa = null, region = 'All', showA = true, showB = true;
  let month = -1, monthProd = -1, monthImp = -1;
  const status = { loading: true, error: null };

  const monthIdxOfDay = (day) => {
    if (!F) return -1;
    const iso = data.isoOf(day), [y0, m0] = F.months[0].split('-').map(Number);
    return (Number(iso.slice(0, 4)) - y0) * 12 + Number(iso.slice(5, 7)) - m0;
  };
  const at = (ser, m) => (ser && m >= ser.s && m < ser.s + ser.v.length ? ser.v[m - ser.s] : null);
  const lastMonth = (dict) => Math.max(...Object.values(dict).map((s) => s.s + s.v.length - 1));
  const inRegion = (iso) => region === 'All' || (F.countries[iso] && F.countries[iso][1] === region);
  const change = (v, base) => (v == null || !base || !base[0] ? null : v / base[0] - 1);
  const changeBin = (c) => (c == null ? -1 : c <= -0.5 ? 6 : c <= -0.2 ? 5 : c <= -0.05 ? 4 : c < 0.05 ? 3 : c < 0.2 ? 2 : c < 0.5 ? 1 : 0);
  const mlabel = (m) => { const [y, mo] = F.months[m].split('-'); return new Date(Date.UTC(+y, +mo - 1, 1)).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' }); };

  function setData(json) {
    F = json; status.loading = false;
    F.lastProd = lastMonth(F.production); F.lastImp = lastMonth(F.us_imports);
    const isos = Object.keys(F.production);
    const geo = new THREE.CylinderGeometry(0.018, 0.018, 1, 10).translate(0, 0.5, 0);
    cols = { isos, mesh: new THREE.InstancedMesh(geo, colMat, isos.length), hit: new THREE.InstancedMesh(new THREE.CylinderGeometry(0.03, 0.03, 1, 6).translate(0, 0.5, 0), hitMat, isos.length), h: new Float32Array(isos.length) };
    cols.mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(isos.length * 3), 3);
    cols.normals = isos.map((iso) => ll(F.countries[iso][2], F.countries[iso][3], 1).normalize());
    group.add(cols.mesh, cols.hit);
    const u = F.countries.USA; usa = ll(u[2], u[3], 1).normalize();
    arcs = Object.keys(F.us_imports).map((iso) => {
      const a = ll(F.countries[iso][2], F.countries[iso][3], 1).normalize();
      const ang = a.angleTo(usa), lift = 0.04 + 0.22 * ang / Math.PI;
      const pts = [];
      for (let k = 0; k <= 40; k++) {
        const t = k / 40, v = new THREE.Vector3().copy(a).lerp(usa, t).normalize();
        if (ang > 1e-3) { const s = Math.sin(ang); v.copy(a).multiplyScalar(Math.sin((1 - t) * ang) / s).add(usa.clone().multiplyScalar(Math.sin(t * ang) / s)); }
        pts.push(v.multiplyScalar(R + 0.005 + lift * Math.sin(Math.PI * t)));
      }
      const mesh = new THREE.Mesh(undefined, arcMat); mesh.visible = false; mesh.userData.iso = iso; group.add(mesh);
      return { iso, curve: new THREE.CatmullRomCurve3(pts), mesh, cache: new Map(), v: null };
    });
    month = -2;
  }

  const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), _up = new THREE.Vector3(0, 1, 0), _c = new THREE.Color();
  function draw(m) {
    monthProd = Math.min(m, F.lastProd); monthImp = Math.min(m, F.lastImp);
    const okProd = m >= 0 && m - F.lastProd <= CARRY_MONTHS, okImp = m >= 0 && m - F.lastImp <= CARRY_MONTHS;
    cols.isos.forEach((iso, n) => {
      const v = okProd && showB && inRegion(iso) ? at(F.production[iso], monthProd) : null;
      const h = v == null || v <= 0 ? 0 : v * PSCALE;
      cols.h[n] = h;
      _q.setFromUnitVectors(_up, cols.normals[n]);
      _p.copy(cols.normals[n]).multiplyScalar(R);
      cols.mesh.setMatrixAt(n, _m.compose(_p, _q, _s.set(1, Math.max(h, 1e-4), 1)));
      cols.hit.setMatrixAt(n, _m.compose(_p, _q, _s.set(1, Math.max(h, 0.02), 1)));
      const bin = changeBin(change(v, F.production_base[iso]));
      cols.mesh.setColorAt(n, _c.copy(bin < 0 ? THEME.axis : THEME.ramp[bin]));
    });
    cols.mesh.instanceMatrix.needsUpdate = cols.hit.instanceMatrix.needsUpdate = cols.mesh.instanceColor.needsUpdate = true;
    const vals = arcs.map((a) => (okImp ? at(F.us_imports[a.iso], monthImp) : null));
    const max = Math.max(1, ...Object.values(F.us_imports).map((s) => Math.max(0, ...s.v.filter((v) => v != null))));
    arcs.forEach((a, k) => {
      const v = vals[k]; a.v = v;
      a.mesh.visible = showA && v != null && v > 0 && inRegion(a.iso);
      if (!a.mesh.visible) return;
      const bucket = Math.max(1, Math.round(10 * Math.sqrt(v / max)));          // 10 thickness steps, area grows with volume
      if (!a.cache.has(bucket)) a.cache.set(bucket, new THREE.TubeGeometry(a.curve, 48, 0.0012 + 0.0011 * bucket, 6, false));
      a.mesh.geometry = a.cache.get(bucket);
    });
  }

  function lists() {
    if (!F || month < 0) return '';
    const okProd = month - F.lastProd <= CARRY_MONTHS, okImp = month - F.lastImp <= CARRY_MONTHS;
    const row = (iso, v, base) => {
      const c = change(v, base);
      return '<tr><td>' + F.countries[iso][0] + '</td><td class="n">' + Math.round(v).toLocaleString('en-US') + '</td><td class="n">' +
        (c == null ? 'n/a' : (c >= 0 ? '+' : '−') + Math.abs(100 * c).toFixed(0) + '%') + '</td></tr>';
    };
    const top = (dict, m, baseDict) => Object.entries(dict).map(([iso, s]) => [iso, at(s, m)]).filter(([iso, v]) => v != null && v > 0 && inRegion(iso))
      .sort((a, b) => b[1] - a[1]).slice(0, 10).map(([iso, v]) => row(iso, v, baseDict[iso])).join('');
    const head = '<thead><tr><th>Country</th><th class="n">Thousand b/d</th><th class="n">vs ' + F.baseline_year + ' avg</th></tr></thead>';
    const regionNote = region === 'All' ? '' : ' (' + region + ')';
    return '<div class="flowcol"><h3>Who sold: largest crude producers' + regionNote + ', ' + (okProd ? mlabel(monthProd) : 'no data') + '</h3>' +
      (okProd && showB ? '<table>' + head + '<tbody>' + top(F.production, monthProd, F.production_base) + '</tbody></table>' : '<p class="note">' + (showB ? 'No production data for this month.' : 'Tier B layer is off.') + '</p>') +
      '<p class="note">Tier B, measured: EIA international data, crude oil production. Production, not exports.</p></div>' +
      '<div class="flowcol"><h3>Who bought: sources of US crude imports' + regionNote + ', ' + (okImp ? mlabel(monthImp) : 'no data') + '</h3>' +
      (okImp && showA ? '<table>' + head + '<tbody>' + top(F.us_imports, monthImp, F.us_imports_base) + '</tbody></table>' : '<p class="note">' + (showA ? 'No import data for this month.' : 'Tier A layer is off.') + '</p>') +
      '<p class="note">Tier A, measured: EIA US crude oil imports by country of origin. Only US imports are measured in a source this page can publish, so other buyers are not shown. Modeled worldwide arcs (Tier C) are kept off the page.</p></div>';
  }

  return {
    key: 'flows', group, lazy: 'data/flows.json',
    get loaded() { return !!F; }, status, setData,
    camera: { pos: ll(28, 5, 1).normalize().multiplyScalar(4.4).add(new THREE.Vector3(0, 0.4, 0)), target: new THREE.Vector3(0, 0, 0), min: 2.2, max: 9, maxPolar: Math.PI, pan: false },
    options: () => ({ region, showA, showB }),
    setOption(k, v) { if (k === 'region') region = v; if (k === 'showA') showA = v; if (k === 'showB') showB = v; month = -2; },
    hint: () => 'Drag to rotate. Scroll or pinch to zoom. Hover a column or an arc.',
    legend: () => '<span><span class="ramp">' + THEME.ramp.slice().reverse().map((c) => '<i style="background:#' + c.getHexString() + '"></i>').join('') +
      '</span>Column colour: production down 50% or more, to up 50% or more, against its ' + (F ? F.baseline_year : 2025) + ' average</span>' +
      '<span>Column height: crude production, thousand b/d (Tier B)</span><span><span class="sw" style="background:var(--accent)"></span>Solid arc: measured US imports by origin (Tier A), thickness = volume</span>',
    caption: (st) => {
      if (status.error) return 'Could not load the flow data: ' + status.error;
      if (!F) return 'Loading the measured flow data...';
      const m = monthIdxOfDay(st.day);
      if (m < 0) return 'Country flow data in this view starts in ' + mlabel(0) + '. Move the date later to see it.';
      const notes = [];
      if (m > F.lastProd) notes.push('production is shown for ' + mlabel(F.lastProd) + ', the latest month published');
      if (m > F.lastImp) notes.push('US imports are shown for ' + mlabel(F.lastImp) + ', the latest month published');
      return 'Monthly data for ' + mlabel(Math.min(m, F.months.length - 1)) + (notes.length ? ': ' + notes.join('; ') : '') +
        '. Columns are measured production (Tier B). Arcs are measured US imports by origin (Tier A). The change is against each country’s ' + F.baseline_year +
        ' monthly average, the last full year before the 2026 disruption. ' + F.unmapped_producers.length + ' small producers with no map point are left off. Crude oil only.';
    },
    explain: () => '<p>Who produced crude oil, and where the United States bought it, month by month. Each column stands on a country and is as tall as its crude production that month (EIA international data). ' +
      'Its colour compares that month with the country’s 2025 monthly average, the last full year before the 2026 disruption: orange is down, blue is up, grey is no change or no baseline.</p>' +
      '<p>Arcs run from each country that sold crude oil to the United States, as thick as the volume (EIA US imports by country of origin). Both layers are measured. ' +
      'Worldwide trade between other countries is not published in a source this page may republish, so it is not drawn. A modeled version exists in the project but stays off the page.</p>',
    lists,
    applyTheme() { earth.applyTheme(THEME); colMat.color.set(0xffffff); arcMat.color.copy(THEME.accent); month = -2; },
    update(st) {
      pil.update(st);
      if (!F) return;
      const m = monthIdxOfDay(st.day);
      if (m !== month) { month = m; draw(m); }
    },
    pick(ray, camera) {
      const p = pil.pick(ray, camera); if (p) return p;
      if (!F) return null;
      const camDir = camera.position.clone().normalize();
      const hc = ray.intersectObject(cols.hit, false).find((h) => cols.h[h.instanceId] > 0 && cols.normals[h.instanceId].dot(camDir) > 0.05);
      const ha = ray.intersectObjects(arcs.filter((a) => a.mesh.visible).map((a) => a.mesh), false)[0];
      if (ha && (!hc || ha.distance < hc.distance)) {
        const iso = ha.object.userData.iso, a = arcs.find((q) => q.iso === iso), base = F.us_imports_base[iso];
        return '<b>' + F.countries[iso][0] + ' to the United States</b><br>' + a.v.toFixed(0) + ' thousand b/d of crude oil, ' + mlabel(monthImp) +
          (base ? '<br>' + F.baseline_year + ' average ' + base[0].toFixed(0) + ' thousand b/d (' + base[1] + ' months reported)' : '') +
          '<br><span style="color:var(--ink-2)">Measured (Tier A). Source: EIA, US crude oil imports by country of origin</span>';
      }
      if (hc) {
        const iso = cols.isos[hc.instanceId], v = at(F.production[iso], monthProd), base = F.production_base[iso], c = change(v, base);
        return '<b>' + F.countries[iso][0] + '</b><br>Crude production ' + v.toFixed(0) + ' thousand b/d, ' + mlabel(monthProd) +
          (base ? '<br>' + F.baseline_year + ' average ' + base[0].toFixed(0) + ' (' + (c >= 0 ? '+' : '−') + Math.abs(100 * c).toFixed(0) + '%)' : '') +
          '<br><span style="color:var(--ink-2)">Measured (Tier B). Source: EIA international data</span>';
      }
      return null;
    },
    probe() {
      if (!F) return null;
      const n = cols.isos.indexOf('SAU');
      return n < 0 || !cols.h[n] ? null : cols.normals[n].clone().multiplyScalar(R + cols.h[n] * 0.6);
    },
    aria: (st, nice) => '3D globe of measured crude oil flows on ' + nice(st.day) + (F && month >= 0 ? ': production by country and US imports by origin for ' + mlabel(Math.min(month, F.months.length - 1)) : ''),
  };
}
