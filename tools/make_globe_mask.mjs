// Run once: npm i world-atlas@2.0.2 topojson-client@3.1.0 d3-geo@3.1.1  then  node tools/make_globe_mask.mjs  (writes land_mask.json)
import fs from 'fs';
import {feature} from 'topojson-client';
import {geoContains} from 'd3-geo';
const topo = JSON.parse(fs.readFileSync('node_modules/world-atlas/land-110m.json'));
const land = feature(topo, topo.objects.land);
const STEP=1.5, W=360/STEP, H=180/STEP;
const bits = new Uint8Array(Math.ceil(W*H/8));
let n=0;
for (let r=0;r<H;r++){ const lat=90-STEP*(r+0.5);
  for (let c=0;c<W;c++){ const lon=-180+STEP*(c+0.5);
    if (geoContains(land,[lon,lat])) { const i=r*W+c; bits[i>>3]|=1<<(i&7); n++; } } }
fs.writeFileSync('../land_mask.json', JSON.stringify({step:STEP,w:W,h:H,count:n,b64:Buffer.from(bits).toString('base64')}));
console.log(W,H,n,Buffer.from(bits).toString('base64').length);
