// Shared by the globe and the world flows view: a dotted Earth (Natural Earth land mask) and the six chokepoint
// pillars. Pillar height = tankers per day (7-day average, IMF PortWatch); ring = that lane's 2019 to 2025 median.
import { clamp } from '../data.js';

const SHORT = { 'strait-of-hormuz': 'Hormuz', 'bab-el-mandeb-strait': 'Bab el-Mandeb', 'suez-canal': 'Suez',
                'malacca-strait': 'Malacca', 'cape-of-good-hope': 'Cape of Good Hope', 'bosporus-strait': 'Bosporus' };
export const shortName = (id) => SHORT[id] || id;

export function latLon(THREE, R = 1) {
  return (lat, lon, r = R) => {
    const phi = (90 - lat) * Math.PI / 180, th = (lon + 180) * Math.PI / 180;
    return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(th), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(th));
  };
}

export function makeEarth({ THREE, data }, R = 1) {
  const ll = latLon(THREE, R);
  const group = new THREE.Group();
  const seaMat = new THREE.MeshBasicMaterial();
  group.add(new THREE.Mesh(new THREE.SphereGeometry(R * 0.994, 64, 48), seaMat));
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const g = c.getContext('2d'); g.beginPath(); g.arc(16, 16, 14, 0, 6.2832); g.fillStyle = '#fff'; g.fill();
  const landMat = new THREE.PointsMaterial({ size: 0.021, sizeAttenuation: true, map: new THREE.CanvasTexture(c), alphaTest: 0.5, transparent: true });
  const L = data.D.land, bin = atob(L.b64), pts = [];
  for (let r = 0; r < L.h; r++) for (let col = 0; col < L.w; col++) {
    const i = r * L.w + col;
    if (bin.charCodeAt(i >> 3) & (1 << (i & 7))) pts.push(ll(90 - L.step * (r + 0.5), -180 + L.step * (col + 0.5), R));
  }
  group.add(new THREE.Points(new THREE.BufferGeometry().setFromPoints(pts), landMat));
  return { group, ll, applyTheme(THEME) { seaMat.color.copy(THEME.sea); landMat.color.copy(THEME.land); } };
}

export function makePillars({ THREE, addLabel, THEME, data }, parent, labelGroup, { R = 1, scale = 0.0058, radius = 0.02 } = {}) {
  const ll = latLon(THREE, R);
  const pillars = data.choke.map((c) => {
    const g = new THREE.Group();
    const n = ll(c.lat, c.lon, 1).normalize();
    g.position.copy(n.clone().multiplyScalar(R));
    g.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), n);
    const geo = new THREE.CylinderGeometry(radius, radius, 1, 14); geo.translate(0, 0.5, 0);
    const mat = new THREE.MeshLambertMaterial();
    const bar = new THREE.Mesh(geo, mat); g.add(bar);
    const hit = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.7, 8).translate(0, 0.35, 0),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })); hit.userData.choke = c; g.add(hit);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(radius * 2, 0.004, 8, 32), new THREE.MeshBasicMaterial());
    ring.rotation.x = Math.PI / 2; ring.position.y = c.baseline * scale; g.add(ring);
    parent.add(g);
    const tipPos = new THREE.Vector3();
    const lab = addLabel('', tipPos, { globe: true, group: labelGroup });
    return { c, g, bar, mat, ring, hit, lab, tipPos, n, v: null, ratio: null };
  });
  return {
    pillars,
    update(st) {
      for (const p of pillars) {
        const v = data.lastVal(p.c.tankers7, st.day);
        p.v = v; p.ratio = v == null ? null : v / p.c.baseline;
        const h = v == null ? 0.004 : Math.max(v * scale, 0.004);
        p.bar.scale.y = h;
        p.hit.scale.y = Math.max(1, h / 0.7);
        if (v == null) p.mat.color.copy(THEME.axis);
        else p.mat.color.copy(THEME.accent).lerp(THEME.warn, clamp((1 - p.ratio) / 0.7, 0, 1));
        p.ring.material.color.copy(THEME.ink);
        p.tipPos.copy(p.n).multiplyScalar(R + h + 0.02);
        p.lab.el.innerHTML = '<b>' + shortName(p.c.id) + '</b> ' + (v == null ? 'no data' : (v < 10 ? v.toFixed(1) : Math.round(v)) + '/day');
      }
    },
    pick(ray, camera) {
      const hit = ray.intersectObjects(pillars.map((p) => p.hit), false)[0];
      if (!hit) return null;
      const p = pillars.find((q) => q.hit === hit.object);
      if (p.n.dot(camera.position.clone().normalize()) < 0.05) return null;   // far side of the globe
      if (p.v == null) return '<b>' + p.c.name + '</b><br>No PortWatch data for this date (counts start January 1, 2019)';
      return '<b>' + p.c.name + '</b><br>' + p.v.toFixed(1) + ' tankers a day (7-day average)<br>' +
             Math.round(100 * p.ratio) + '% of its 2019 to 2025 median of ' + p.c.baseline + ' a day' +
             '<br><span style="color:var(--ink-2)">Source: IMF PortWatch, satellite ship signals (measured)</span>';
    },
    probe: (id = 'strait-of-hormuz') => { const p = pillars.find((q) => q.c.id === id); return p.n.clone().multiplyScalar(R + 0.08); },
  };
}
