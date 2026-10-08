// The 3D page: one shared state (state.js) drives three views (scenes/), the readout and the timeline.
// Static page: data comes from docs/data/viz3d.js (window.VIZ3D), written by export_3d.py.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createState, toHash, fromHash, advance, SPEEDS } from './state.js';
import { makeData, label, signed, fmt, clamp } from './data.js';
import { createGlobe, shortName } from './scenes/globe.js';
import { createSkyline } from './scenes/skyline.js';
import { createHormuz } from './scenes/hormuz.js';

const $ = (s) => document.querySelector(s);
const data = makeData(window.VIZ3D);
const { D, N, nice, isoOf, dayOf, val, lastVal, weeks, weekIdxAt, choke, hormuz } = data;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const DISRUPTION_START = dayOf('2026-02-28');               // default opening date: start of the 2026 disruption

$('#generated').textContent = 'Data through ' + isoOf(N - 1);
$('#credits').textContent = 'Data: ' + D.credits.join('; ') + '.';
$('#repo').href = D.repo;
$('#scrub').max = N - 1;

// ---------- theme ----------
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const THEME = {};
function readTheme() {
  const dark = matchMedia('(prefers-color-scheme: dark)').matches && document.documentElement.dataset.theme !== 'light';
  THEME.dark = dark;
  for (const k of ['bg', 'surface', 'surface-2', 'ink', 'ink-2', 'accent', 'warn', 'axis']) THEME[k] = new THREE.Color(css('--' + k));
  THEME.land = new THREE.Color(dark ? '#8d8b83' : '#6f6d67');
  THEME.sea = new THREE.Color(dark ? '#232321' : '#e3e2db');
  THEME.hzSea = new THREE.Color(dark ? '#16202c' : '#dde6f0');
  THEME.hzLand = new THREE.Color(dark ? '#55534d' : '#f2f0e8');
  THEME.ramp = (dark
    ? ['#7db4f5', '#4f8fd8', '#3a5f8f', '#5a5953', '#8f5a43', '#d86b3c', '#ff9264']
    : ['#1d5fb0', '#4a8fd9', '#a9c9ec', '#b8b6ab', '#f2b79c', '#e2764a', '#b8401a']).map((c) => new THREE.Color(c));
}
readTheme();

// ---------- renderer (falls back to the readout and strips if WebGL is unavailable) ----------
const canvas = $('#gl'), viewport = $('#viewport');
let renderer = null;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
} catch (e) { $('#fallback').style.display = 'flex'; }
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 1.6, 0.1, 100);
scene.add(new THREE.AmbientLight(0xffffff, 0.85));
const sun = new THREE.DirectionalLight(0xffffff, 1.1); sun.position.set(3, 6, 4); scene.add(sun);
const controls = renderer ? new OrbitControls(camera, canvas) : null;
if (controls) { controls.enableDamping = true; controls.dampingFactor = 0.08; controls.rotateSpeed = 0.7; controls.enablePan = false; }

const labelsEl = $('#labels'), labels = [];
function addLabel(text, pos, opts = {}) {
  const el = document.createElement('div');
  el.className = 'lbl' + (opts.dim ? ' dim' : '');
  el.innerHTML = text; labelsEl.appendChild(el);
  const l = { el, pos, group: opts.group, globe: !!opts.globe }; labels.push(l); return l;
}

// ---------- the shared state and the three views ----------
const initial = { day: DISRUPTION_START, ...fromHash(location.hash, dayOf, N) };
const state = createState(initial, N);
if (initial.keep2020) $('#in2020').checked = true;
const ctx = { THREE, addLabel, THEME, data, reduceMotion };
const scenes = { globe: createGlobe(ctx), sky: createSkyline(ctx), hz: createHormuz(ctx) };
for (const s of Object.values(scenes)) { s.group.visible = false; scene.add(s.group); s.applyTheme(); }
let dirty = true;

function setCamera(view) {
  if (!controls) return;
  const c = scenes[view].camera;
  camera.position.copy(c.pos); controls.target.copy(c.target);
  controls.enablePan = c.pan; controls.minDistance = c.min; controls.maxDistance = c.max; controls.maxPolarAngle = c.maxPolar;
  controls.update(); dirty = true;
}

function renderView(st, changed) {
  const sc = scenes[st.view];
  if (changed.includes('view')) {
    for (const [k, s] of Object.entries(scenes)) s.group.visible = k === st.view;
    for (const v of Object.keys(scenes)) $('#v' + { globe: 'Globe', sky: 'Sky', hz: 'Hz' }[v]).setAttribute('aria-pressed', v === st.view);
    $('#hzNote').hidden = st.view !== 'hz';
    $('#optWrap').hidden = st.view !== 'sky';
    $('#hint').textContent = sc.hint();
    $('#legend').innerHTML = sc.legend();
    hideTip(); setCamera(st.view);
  }
  sc.update(st);
  $('#caption').textContent = sc.caption(st);
  if (st.view === 'hz') $('#hzNote').innerHTML = sc.note(st);
  canvas.setAttribute('aria-label', sc.aria(st, nice));
}

function renderReadout(st) {
  const i = st.day;
  $('#rDate').textContent = nice(i);
  $('#dateLabel').textContent = nice(i);
  $('#scrub').value = i;
  const P = D.prices, b = val(P.brent, i), w = val(P.wti, i), u = val(P.ust10y, i), g = val(P.gpr, i);
  $('#rBrent').textContent = fmt(b); $('#rWti').textContent = fmt(w);
  $('#rSpread').textContent = b != null && w != null ? fmt(b - w) : 'n/a';
  $('#rUst').textContent = u != null ? fmt(u) + '%' : 'n/a';
  $('#rGpr').textContent = g != null ? String(Math.round(g)) : 'n/a';
  $('#rShip').innerHTML = choke.map((c) => {
    const v = lastVal(c.tankers7, i), pct = v == null ? null : Math.round(100 * v / c.baseline);
    return '<dt>' + shortName(c.id) + '</dt><dd>' + (v == null ? 'n/a' : v.toFixed(1)) +
           (pct == null ? '' : ' <span style="font-weight:400;color:var(--ink-2)">(' + pct + '%)</span>') + '</dd>';
  }).join('');
  const wi = weekIdxAt[i];
  if (wi < 0) {
    $('#rWeekH').textContent = 'US tightness (scores start Nov 1995)';
    for (const id of ['#rScore', '#rCrude', '#rDist', '#rUtil']) $(id).textContent = 'n/a';
  } else {
    const wk = weeks[wi], r = wk[st.keep2020 ? 'in' : 'out'];
    $('#rWeekH').textContent = 'US tightness, week ending ' + wk.d;
    if (r) {
      $('#rScore').innerHTML = signed(r[0]) + '<span class="tag ' + label(r[0]) + '">' + label(r[0]) + '</span>';
      $('#rCrude').textContent = r[1].toFixed(2); $('#rDist').textContent = r[2].toFixed(2); $('#rUtil').textContent = r[3].toFixed(2);
    } else for (const id of ['#rScore', '#rCrude', '#rDist', '#rUtil']) $(id).textContent = 'n/a';
  }
  $('#vBrent').textContent = b != null ? '$' + b.toFixed(2) : '';
  const hv = lastVal(hormuz.tankers7, i);
  $('#vShip').textContent = hv != null ? hv.toFixed(1) + ' (' + Math.round(100 * hv / hormuz.baseline) + '% of usual)' : 'no data before 2019';
  for (const c of cursors) c.style.left = (100 * i / (N - 1)) + '%';
}

// Every change to the state flows through here: the views never keep their own copy of the date.
state.subscribe((st, changed) => {
  if (changed.includes('playing')) { $('#play').textContent = st.playing ? 'Pause' : 'Play'; $('#play').setAttribute('aria-label', st.playing ? 'Pause' : 'Play'); }
  if (changed.some((k) => ['day', 'view', 'keep2020'].includes(k))) { renderReadout(st); renderView(st, changed); }
  if (!st.playing && changed.some((k) => ['day', 'view', 'keep2020'].includes(k))) writeHash();
  dirty = true;
});

function writeHash() { try { history.replaceState(null, '', toHash(state.get(), isoOf)); } catch (e) { /* file:// may refuse */ } }

// ---------- timeline strips ----------
const cursors = [];
function buildStrip(el, series, colorVar, lo, hi) {
  const pts = [], step = Math.max(1, Math.floor(N / 900));
  for (let i = 0; i < N; i += step) { const v = val(series, i); if (v == null) continue; pts.push((1000 * i / (N - 1)).toFixed(1) + ',' + (40 - 34 * (v - lo) / (hi - lo)).toFixed(1)); }
  el.insertAdjacentHTML('beforeend', '<svg viewBox="0 0 1000 44" preserveAspectRatio="none"><polyline points="' + pts.join(' ') +
    '" fill="none" stroke="var(' + colorVar + ')" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg>');
  const cur = document.createElement('div');
  cur.style.cssText = 'position:absolute;top:0;bottom:0;width:0;border-left:1.5px solid var(--ink);pointer-events:none';
  el.appendChild(cur); cursors.push(cur);
}
{
  const bs = data.values(D.prices.brent).concat(data.values(D.prices.wti)), hs = data.values(hormuz.tankers7);
  buildStrip($('#stripBrent'), D.prices.brent, '--accent', Math.min(...bs, 0), Math.max(...bs));
  buildStrip($('#stripShip'), hormuz.tankers7, '--warn', 0, Math.max(...hs));
  const t = $('#ticks'), y0 = Number(D.start.slice(0, 4)), y1 = Number(isoOf(N - 1).slice(0, 4));
  for (let y = Math.ceil(y0 / 5) * 5; y <= y1; y += 5) t.insertAdjacentHTML('beforeend', '<span style="left:' + (100 * dayOf(y + '-01-01') / (N - 1)) + '%">' + y + '</span>');
  for (const id of ['#stripBrent', '#stripShip']) {
    const el = $(id); let down = false;
    const set = (e) => { const r = el.getBoundingClientRect(); state.set({ playing: false, day: clamp((e.clientX - r.left) / r.width, 0, 1) * (N - 1) }); };
    el.addEventListener('pointerdown', (e) => { down = true; el.setPointerCapture(e.pointerId); set(e); });
    el.addEventListener('pointermove', (e) => { if (down) set(e); });
    el.addEventListener('pointerup', () => { down = false; writeHash(); });
  }
}

// ---------- controls ----------
let lowDay = 0;
{ let m = Infinity; for (let i = hormuz.tankers7.s; i < hormuz.tankers7.s + hormuz.tankers7.v.length; i++) { const v = val(hormuz.tankers7, i); if (v != null && v < m) { m = v; lowDay = i; } } }
let carry = 0, lastT = 0;
$('#play').onclick = () => {
  const st = state.get();
  if (st.playing) return state.set({ playing: false });
  carry = 0; lastT = performance.now();
  state.set({ playing: true, day: st.day >= N - 1 ? DISRUPTION_START : st.day });
};
$('#scrub').addEventListener('input', (e) => state.set({ playing: false, day: +e.target.value }));
const jump = (day) => () => state.set({ playing: false, day });
$('#jStart').onclick = jump(0);
$('#j2019').onclick = jump(data.portwatchStart);
$('#jDisruption').onclick = jump(DISRUPTION_START);
$('#jLow').onclick = jump(lowDay);
$('#jNow').onclick = jump(N - 1);
$('#speed').onchange = (e) => state.set({ speed: SPEEDS[e.target.value] || SPEEDS.normal });
$('#vGlobe').onclick = () => state.set({ view: 'globe' });
$('#vSky').onclick = () => state.set({ view: 'sky' });
$('#vHz').onclick = () => state.set({ view: 'hz' });
$('#reset').onclick = () => setCamera(state.get().view);
$('#in2020').onchange = (e) => state.set({ keep2020: e.target.checked });
document.addEventListener('visibilitychange', () => { if (document.hidden) state.set({ playing: false }); });
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  readTheme(); for (const s of Object.values(scenes)) s.applyTheme();
  const st = state.get(); renderView(st, ['view']); dirty = true;
});

// ---------- pointer interaction ----------
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), tip = $('#tip');
function hideTip() { tip.style.display = 'none'; canvas.style.cursor = ''; }
function pick(e) {
  if (!renderer) return;
  const r = canvas.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
  ndc.set((x / r.width) * 2 - 1, -(y / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const st = state.get(), html = scenes[st.view].pick(ray, camera, st);
  if (!html) return hideTip();
  canvas.style.cursor = 'pointer';
  tip.innerHTML = html; tip.style.display = 'block';
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = clamp(x + 14, 4, viewport.clientWidth - w - 4) + 'px';
  tip.style.top = clamp(y + 14, 4, viewport.clientHeight - h - 4) + 'px';
}
canvas.addEventListener('pointermove', (e) => { if (e.buttons === 0) pick(e); else hideTip(); });
canvas.addEventListener('pointerleave', hideTip);
canvas.addEventListener('click', (e) => { if (e.pointerType === 'touch') pick(e); });

// ---------- loop: render only when something changed ----------
function resize() {
  if (!renderer) return;
  const w = viewport.clientWidth, h = viewport.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h;
  camera.zoom = clamp((w / h) / 1.45, 0.4, 1);
  camera.updateProjectionMatrix(); dirty = true;
}
new ResizeObserver(resize).observe(viewport);
if (controls) controls.addEventListener('change', () => { dirty = true; });
const v3 = new THREE.Vector3();
function placeLabels(view) {
  const w = viewport.clientWidth, h = viewport.clientHeight, camDir = camera.position.clone().normalize();
  for (const l of labels) {
    if (l.group !== view) { l.el.style.display = 'none'; continue; }
    const vis = !l.globe || l.pos.clone().normalize().dot(camDir) > 0.12;
    v3.copy(l.pos).project(camera);
    if (v3.z > 1 || !vis) { l.el.style.display = 'none'; continue; }
    l.el.style.display = 'block';
    l.el.style.transform = 'translate(' + ((v3.x * 0.5 + 0.5) * w + (l.globe ? 6 : -l.el.offsetWidth / 2)).toFixed(1) + 'px,' +
                           ((-v3.y * 0.5 + 0.5) * h - (l.globe ? 8 : 6)).toFixed(1) + 'px)';
  }
}
let frames = 0;                                            // frames drawn, read by the browser tests
function frame(now) {
  requestAnimationFrame(frame);                            // browsers throttle this in hidden tabs; playback pauses on visibilitychange
  const st = state.get();
  if (st.playing) {
    const r = advance(st, (now - lastT) / 1000, carry, N); lastT = now; carry = r.carry;
    if (r.day !== st.day || r.playing !== st.playing) state.set({ day: r.day, playing: r.playing });
  }
  if (st.view === 'hz' && !reduceMotion) { scenes.hz.animate(now / 1000); dirty = true; }
  if (controls && controls.update()) dirty = true;
  if (renderer && dirty) { renderer.render(scene, camera); placeLabels(st.view); dirty = false; frames++; }
}
resize();
{ const st = state.get(); renderReadout(st); renderView(st, ['view']); }
requestAnimationFrame(frame);
window.__viz = { state, data, scenes, camera, THREE, webgl: !!renderer, frames: () => frames };   // handle for the browser tests and the console
