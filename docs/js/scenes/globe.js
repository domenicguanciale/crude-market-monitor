// Globe: a pillar at each of six chokepoints. Height = tankers per day (7-day average, IMF PortWatch).
// Ring = that lane's own 2019 to 2025 median. Before 2019 there is no PortWatch data and the pillars say so.
import { makeEarth, makePillars, latLon, shortName } from './earth.js';
export { shortName };

export function createGlobe(ctx) {
  const { THREE } = ctx;
  const group = new THREE.Group();
  const earth = makeEarth(ctx); group.add(earth.group);
  const pil = makePillars(ctx, group, 'globe');
  const start = latLon(THREE)(26.3, 57, 1).normalize().multiplyScalar(4.7).add(new THREE.Vector3(0, 0.3, 0));

  return {
    key: 'globe', group,
    camera: { pos: start, target: new THREE.Vector3(0, 0, 0), min: 2.2, max: 9, maxPolar: Math.PI, pan: false },
    hint: () => 'Drag to rotate. Scroll or pinch to zoom. Hover a pillar.',
    legend: () => '<span><span class="ramp"><i style="background:var(--accent)"></i><i style="background:color-mix(in srgb,var(--accent) 50%,var(--warn))"></i><i style="background:var(--warn)"></i></span>Pillar colour: usual traffic to under 30% of usual</span><span>Pillar height: tankers per day</span><span><span class="sw" style="background:none;border:2px solid var(--ink);border-radius:50%;width:12px;height:12px"></span>Ring: that lane’s 2019 to 2025 median</span>',
    caption: (st) => st.day < ctx.data.portwatchStart
      ? 'IMF PortWatch tanker counts start on January 1, 2019. Before that date the pillars show no traffic data.'
      : 'Each pillar is one chokepoint. Counts are the 7-day average of tankers seen by satellite ship signals (IMF PortWatch).',
    explain: () => '<p>A globe with a pillar at each of six shipping chokepoints: the narrow sea lanes most oil tankers must pass. ' +
      'The pillar is as tall as the number of tankers that passed per day (7-day average), measured from satellite ship signals by IMF PortWatch. ' +
      'The ring on each pillar is that lane’s own median from 2019 to 2025, so a pillar that ends below its ring is running under its usual traffic.</p>' +
      '<p>Counts miss ships that switch their signals off, and they start on January 1, 2019. Units: tankers per day.</p>',
    applyTheme() { earth.applyTheme(ctx.THEME); },
    update: (st) => pil.update(st),
    pick: (ray, camera) => pil.pick(ray, camera),
    probe: () => pil.probe(),
    aria: (st, nice) => '3D globe on ' + nice(st.day) + ': ' + pil.pillars.map((p) => shortName(p.c.id) + ' ' +
      (p.v == null ? 'no data' : p.v.toFixed(1) + ' tankers a day')).join(', '),
  };
}
