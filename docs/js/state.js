// One shared state for the whole page (World Oil Simulation, M5).
// Every view subscribes to it. No view keeps its own copy of the date, so they cannot disagree.
// Pure functions only: no DOM, no Three.js, so the browser tests can check it directly.

export const VIEWS = ['globe', 'sky', 'hz'];
export const SPEEDS = { slow: 14, normal: 35, fast: 120, year: 365 };   // days per second

export function createState(initial, days) {
  const s = { day: days - 1, playing: false, speed: SPEEDS.normal, view: 'globe', keep2020: false, ...initial };
  s.day = clampDay(s.day, days);
  const subs = new Set();
  return {
    days,
    get: () => ({ ...s }),
    set(patch) {
      const changed = [];
      for (const [k, v0] of Object.entries(patch)) {
        let v = v0;
        if (k === 'day') v = clampDay(v, days);
        if (k === 'view' && !VIEWS.includes(v)) continue;
        if (s[k] !== v) { s[k] = v; changed.push(k); }
      }
      if (changed.length) for (const fn of subs) fn({ ...s }, changed);
      return changed;
    },
    subscribe(fn) { subs.add(fn); return () => subs.delete(fn); },
  };
}

export function clampDay(day, days) {
  const d = Math.round(Number(day));
  return Number.isFinite(d) ? Math.min(days - 1, Math.max(0, d)) : days - 1;
}

// The URL hash holds the view, date and 2020 switch, so a link opens where it was shared.
export function toHash(st, isoOf) {
  return '#v=' + st.view + '&d=' + isoOf(st.day) + (st.keep2020 ? '&k=1' : '');
}

export function fromHash(hash, dayOf, days) {
  const h = new URLSearchParams(String(hash || '').replace(/^#/, ''));
  const out = {};
  const d = h.get('d');
  if (d && /^\d{4}-\d{2}-\d{2}$/.test(d)) out.day = clampDay(dayOf(d), days);
  if (VIEWS.includes(h.get('v'))) out.view = h.get('v');
  if (h.get('k') === '1') out.keep2020 = true;
  return out;
}

// Playback: advance the date by `speed` days per second of real time. Deterministic for a given sequence
// of frame times. Stops at the last day.
export function advance(st, elapsedSeconds, carry, days) {
  const total = carry + elapsedSeconds * st.speed;
  const step = Math.floor(total);
  if (step < 1) return { day: st.day, carry: total, playing: st.playing };
  const day = Math.min(days - 1, st.day + step);
  return { day, carry: total - step, playing: day < days - 1 };
}
