// Run once: npm i world-atlas@2.0.2 topojson-client@3.1.0 polygon-clipping@0.15.7  then  node tools/make_region_land.mjs  (writes region_land.json)
import fs from 'fs';
import {feature} from 'topojson-client';
import pc from 'polygon-clipping';
const topo = JSON.parse(fs.readFileSync('node_modules/world-atlas/land-10m.json'));
const land = feature(topo, topo.objects.land);
const BOX = [47.0, 23.0, 61.5, 31.0];                       // lon min, lat min, lon max, lat max
const clip = [[[BOX[0],BOX[1]],[BOX[2],BOX[1]],[BOX[2],BOX[3]],[BOX[0],BOX[3]],[BOX[0],BOX[1]]]];
const geoms = land.features ? land.features.map(f=>f.geometry) : [land.geometry];
let out = [];
for (const g of geoms) {
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
  for (const p of polys) {
    // quick bbox reject
    const xs = p[0].map(c=>c[0]), ys = p[0].map(c=>c[1]);
    if (Math.max(...xs) < BOX[0] || Math.min(...xs) > BOX[2] || Math.max(...ys) < BOX[1] || Math.min(...ys) > BOX[3]) continue;
    const r = pc.intersection(p, clip);
    for (const poly of r) out.push(poly.map(ring => ring.map(c => [Math.round(c[0]*1000)/1000, Math.round(c[1]*1000)/1000])));
  }
}
const pts = out.reduce((a,p)=>a+p.reduce((b,r)=>b+r.length,0),0);
fs.writeFileSync('../region_land.json', JSON.stringify({box: BOX, polygons: out}));
console.log('polygons', out.length, 'points', pts, 'bytes', fs.statSync('../region_land.json').size);
