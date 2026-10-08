// Globe: a pillar at each of six chokepoints. Height = tankers per day (7-day average, IMF PortWatch).
// Ring = that lane's own 2019 to 2025 median. Before 2019 there is no PortWatch data and the pillars say so.
import { clamp } from '../data.js';

const SHORT = { 'strait-of-hormuz': 'Hormuz', 'bab-el-mandeb-strait': 'Bab el-Mandeb', 'suez-canal': 'Suez',
                'malacca-strait': 'Malacca', 'cape-of-good-hope': 'Cape of Good Hope', 'bosporus-strait': 'Bosporus' };
export const shortName = (id) => SHORT[id] || id;

export function createGlobe({ THREE, addLabel, THEME, data }) {
  const R = 1, SCALE = 0.0058;                               // world units per tanker per day
  const group = new THREE.Group();
  const ll = (lat, lon, r = R) => {
    const phi = (90 - lat) * Math.PI / 180, th = (lon + 180) * Math.PI / 180;
    return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(th), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(th));
  };
  const seaMat = new THREE.MeshBasicMaterial();
  group.add(new THREE.Mesh(new THREE.SphereGeometry(R * 0.994, 64, 48), seaMat));
  const dotTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 32;
    const g = c.getContext('2d'); g.beginPath(); g.arc(16, 16, 14, 0, 6.2832); g.fillStyle = '#fff'; g.fill();
    return new THREE.CanvasTexture(c);
  })();
  const landMat = new THREE.PointsMaterial({ size: 0.021, sizeAttenuation: true, map: dotTex, alphaTest: 0.5, transparent: true });
  {
    const L = data.D.land, bin = atob(L.b64), pts = [];
    for (let r = 0; r < L.h; r++) for (let c = 0; c < L.w; c++) {
      const i = r * L.w + c;
      if (bin.charCodeAt(i >> 3) & (1 << (i & 7))) pts.push(ll(90 - L.step * (r + 0.5), -180 + L.step * (c + 0.5), R));
    }
    group.add(new THREE.Points(new THREE.BufferGeometry().setFromPoints(pts), landMat));
  }
  const pillars = data.choke.map((c) => {
    const g = new THREE.Group();
    const n = ll(c.lat, c.lon, 1).normalize();
    g.position.copy(n.clone().multiplyScalar(R));
    g.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), n);
    const geo = new THREE.CylinderGeometry(0.02, 0.02, 1, 14); geo.translate(0, 0.5, 0);
    const mat = new THREE.MeshLambertMaterial();
    const bar = new THREE.Mesh(geo, mat); g.add(bar);
    const hit = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.7, 8).translate(0, 0.35, 0),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })); hit.userData.choke = c; g.add(hit);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.004, 8, 32), new THREE.MeshBasicMaterial());
    ring.rotation.x = Math.PI / 2; ring.position.y = c.baseline * SCALE; g.add(ring);
    group.add(g);
    const tipPos = new THREE.Vector3();
    const lab = addLabel('', tipPos, { globe: true, group: 'globe' });
    return { c, g, bar, mat, ring, hit, lab, tipPos, n, v: null, ratio: null };
  });
  const start = ll(26.3, 57, 1).normalize().multiplyScalar(4.7).add(new THREE.Vector3(0, 0.3, 0));

  return {
    key: 'globe', group,
    camera: { pos: start, target: new THREE.Vector3(0, 0, 0), min: 2.2, max: 9, maxPolar: Math.PI, pan: false },
    hint: () => 'Drag to rotate. Scroll or pinch to zoom. Hover a pillar.',
    legend: () => '<span><span class="ramp"><i style="background:var(--accent)"></i><i style="background:color-mix(in srgb,var(--accent) 50%,var(--warn))"></i><i style="background:var(--warn)"></i></span>Pillar colour: usual traffic to under 30% of usual</span><span>Pillar height: tankers per day</span><span><span class="sw" style="background:none;border:2px solid var(--ink);border-radius:50%;width:12px;height:12px"></span>Ring: that lane’s 2019 to 2025 median</span>',
    caption: (st) => st.day < data.portwatchStart
      ? 'IMF PortWatch tanker counts start on January 1, 2019. Before that date the pillars show no traffic data.'
      : 'Each pillar is one chokepoint. Counts are the 7-day average of tankers seen by satellite ship signals (IMF PortWatch).',
    applyTheme() { seaMat.color.copy(THEME.sea); landMat.color.copy(THEME.land); },
    update(st) {
      for (const p of pillars) {
        const v = data.lastVal(p.c.tankers7, st.day);
        p.v = v; p.ratio = v == null ? null : v / p.c.baseline;
        const h = v == null ? 0.004 : Math.max(v * SCALE, 0.004);
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
             Math.round(100 * p.ratio) + '% of its 2019 to 2025 median of ' + p.c.baseline + ' a day';
    },
    aria: (st, nice) => '3D globe on ' + nice(st.day) + ': ' + pillars.map((p) => shortName(p.c.id) + ' ' +
      (p.v == null ? 'no data' : p.v.toFixed(1) + ' tankers a day')).join(', '),
  };
}
