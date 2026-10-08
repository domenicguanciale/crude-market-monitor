// Skyline: one bar per week, 1996 to today. Height and colour = US tightness score (-3 loose to +3 tight),
// computed twice by export_3d.py: 2020 left out of the five-year range (default) or kept in.
import { label, signed } from '../data.js';

export function createSkyline({ THREE, addLabel, THEME, data }) {
  const weeks = data.weeks, FIRST_YEAR = weeks[0].y;
  const group = new THREE.Group();
  const DX = 0.15, DZ = 0.2, HU = 0.13;
  const years = weeks[weeks.length - 1].y - FIRST_YEAR + 1;
  const xOf = (w) => (w - 27) * DX, zOf = (y) => (y - FIRST_YEAR - (years - 1) / 2) * DZ;
  const barMat = new THREE.MeshLambertMaterial();
  const bars = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), barMat, weeks.length); group.add(bars);
  bars.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(weeks.length * 3), 3);
  const floor = new THREE.Mesh(new THREE.BoxGeometry(53 * DX + 0.2, 0.01, years * DZ + 0.2),
                               new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.55 }));
  floor.position.set(xOf(27), -0.006, zOf(FIRST_YEAR + (years - 1) / 2)); group.add(floor);
  const cursorBox = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), new THREE.LineBasicMaterial());
  group.add(cursorBox);
  const sliceMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.1, side: THREE.DoubleSide, depthWrite: false });
  const weekSlice = new THREE.Mesh(new THREE.PlaneGeometry(years * DZ, 0.8), sliceMat);
  weekSlice.rotation.y = Math.PI / 2; group.add(weekSlice);
  const tmpM = new THREE.Matrix4(), tmpP = new THREE.Vector3(), tmpS = new THREE.Vector3(), tmpQ = new THREE.Quaternion(), tmpC = new THREE.Color();
  const modeKey = (st) => (st.keep2020 ? 'in' : 'out');
  let laidOut = null;

  function layout(st) {
    const k = modeKey(st);
    weeks.forEach((w, n) => {
      const r = w[k]; const s = r ? r[0] : 0;
      const hgt = Math.max(Math.abs(s) * HU, 0.012);
      tmpP.set(xOf(w.w), s >= 0 ? hgt / 2 : -hgt / 2, zOf(w.y));
      tmpS.set(DX * 0.82, hgt, DZ * 0.78);
      bars.setMatrixAt(n, tmpM.compose(tmpP, tmpQ.identity(), tmpS));
    });
    bars.instanceMatrix.needsUpdate = true; bars.computeBoundingSphere();
    laidOut = k;
  }
  {
    const front = zOf(FIRST_YEAR + years - 1) + 0.28;
    [[1, 'Jan'], [14, 'Apr'], [27, 'Jul'], [40, 'Oct']].forEach(([wk, t]) => addLabel(t, new THREE.Vector3(xOf(wk), 0, front), { dim: true, group: 'sky' }));
    const left = xOf(1) - 0.3;
    for (let y = FIRST_YEAR; y < FIRST_YEAR + years; y++) if (y % 5 === 0 || y === FIRST_YEAR || (y === FIRST_YEAR + years - 1 && y % 5 !== 1))
      addLabel(String(y), new THREE.Vector3(left, 0, zOf(y)), { dim: true, group: 'sky' });
    const rx = xOf(53) + 0.55, rz = zOf(FIRST_YEAR + years - 1);
    addLabel('+3 tight', new THREE.Vector3(rx, 3 * HU, rz), { dim: true, group: 'sky' });
    addLabel('0', new THREE.Vector3(rx, 0, rz), { dim: true, group: 'sky' });
    addLabel('−3 loose', new THREE.Vector3(rx, -3 * HU, rz), { dim: true, group: 'sky' });
  }

  return {
    key: 'sky', group,
    camera: { pos: new THREE.Vector3(1.2, 8.2, 9.6), target: new THREE.Vector3(0, -0.1, 0.1), min: 4, max: 20, maxPolar: 1.52, pan: false },
    hint: () => 'Drag to rotate. Scroll or pinch to zoom. Hover a bar.',
    legend: () => '<span><span class="ramp">' + THEME.ramp.map((c) => '<i style="background:#' + c.getHexString() + '"></i>').join('') +
      '</span>−3 loose &nbsp; 0 &nbsp; +3 tight</span><span>Rows: years, ' + FIRST_YEAR + ' back to ' + (FIRST_YEAR + years - 1) +
      ' front</span><span>Columns: week of the year</span><span>Faded: after the selected date</span>',
    caption: (st) => data.weekIdxAt[st.day] < 0
      ? 'Tightness scores start in November 1995, the first week with five full prior years of data. Move the date later to see the skyline fill in.'
      : 'Each bar is one week. The score adds three points: crude stocks, distillate stocks and refinery use, each against the same week in the prior five years. The highlighted slice shows the same week in every year.',
    applyTheme() { floor.material.color.copy(THEME['surface-2']); cursorBox.material.color.copy(THEME.ink); sliceMat.color.copy(THEME.accent); barMat.color.set(0xffffff); },
    update(st) {
      if (laidOut !== modeKey(st)) layout(st);
      const k = modeKey(st), cut = data.weekIdxAt[st.day];
      weeks.forEach((w, n) => {
        const r = w[k]; const s = r ? r[0] : 0;
        tmpC.copy(THEME.ramp[s + 3]);
        if (n > cut) tmpC.lerp(THEME.surface, 0.82);
        bars.setColorAt(n, tmpC);
      });
      bars.instanceColor.needsUpdate = true;
      cursorBox.visible = weekSlice.visible = cut >= 0;
      if (cut < 0) return;
      const w = weeks[cut], r = w[k], s = r ? r[0] : 0, hgt = Math.max(Math.abs(s) * HU, 0.012);
      cursorBox.position.set(xOf(w.w), s >= 0 ? hgt / 2 : -hgt / 2, zOf(w.y));
      cursorBox.scale.set(DX * 1.1, hgt + 0.03, DZ * 1.05);
      weekSlice.position.set(xOf(w.w), 0, 0);
    },
    pick(ray, camera, st) {
      const hit = ray.intersectObject(bars, false)[0];
      if (!hit || hit.instanceId == null) return null;
      const w = weeks[hit.instanceId], r = w[modeKey(st)];
      if (!r) return null;
      return '<b>Week ending ' + w.d + '</b><br>Score ' + signed(r[0]) + ' (' + label(r[0]) + ')<br>Crude stocks ' + r[1].toFixed(2) +
             ', distillate ' + r[2].toFixed(2) + ', refinery use ' + r[3].toFixed(2) + '<br><span style="color:var(--ink-2)">0 = five-year low, 1 = five-year high</span>';
    },
    aria: (st) => {
      const n = data.weekIdxAt[st.day];
      if (n < 0) return '3D skyline of weekly US tightness scores. Scores start in November 1995.';
      const w = weeks[n], r = w[modeKey(st)];
      return '3D skyline of weekly US tightness scores. Week ending ' + w.d + ' scores ' + (r ? signed(r[0]) + ', ' + label(r[0]) : 'n/a');
    },
  };
}
