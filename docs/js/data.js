// Reading docs/data/viz3d.js (window.VIZ3D, written by export_3d.py). Format 2: every daily series is
// {s: index of its first day, v: values}. Day 0 is D.start. A day outside a series has no value (null).

export function makeData(D) {
  const N = D.days;
  const T0 = Date.parse(D.start + 'T00:00:00Z');
  const isoOf = (i) => new Date(T0 + i * 864e5).toISOString().slice(0, 10);
  const dayOf = (iso) => Math.round((Date.parse(iso + 'T00:00:00Z') - T0) / 864e5);
  const nice = (i) => new Date(T0 + i * 864e5).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' });
  const val = (series, i) => (series && i >= series.s && i < series.s + series.v.length ? series.v[i - series.s] : null);
  // The latest value on or before day i, but never carried more than `maxCarry` days past the series' end.
  const lastVal = (series, i, maxCarry = 7) => {
    if (!series || !series.v.length || i < series.s) return null;
    const end = series.s + series.v.length - 1;
    if (i - end > maxCarry) return null;
    for (let k = Math.min(i, end); k >= series.s; k--) { const v = series.v[k - series.s]; if (v != null) return v; }
    return null;
  };
  const values = (series) => series.v.filter((v) => v != null);
  const weeks = D.weeks;
  const weekIdxAt = new Int32Array(N).fill(-1);          // last scored week on or before each day (-1 before Nov 1995)
  { let p = -1; for (let i = 0; i < N; i++) { const iso = isoOf(i); while (p + 1 < weeks.length && weeks[p + 1].d <= iso) p++; weekIdxAt[i] = p; } }
  const choke = D.chokepoints;
  const hormuz = choke.find((c) => c.id === 'strait-of-hormuz');
  return { D, N, T0, isoOf, dayOf, nice, val, lastVal, values, weeks, weekIdxAt, choke, hormuz,
           portwatchStart: dayOf(D.portwatch_start || '2019-01-01') };
}

export const label = (s) => (s >= 2 ? 'tight' : s <= -2 ? 'loose' : 'normal');
export const signed = (s) => (s > 0 ? '+' + s : s < 0 ? '−' + Math.abs(s) : '0');
export const fmt = (v, d = 2) => (v == null ? 'n/a' : v.toFixed(d));
export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
