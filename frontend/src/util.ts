// CIS color ramp: teal (low) -> amber (mid) -> red (high)
export function cisColor(cis: number): [number, number, number] {
  const t = Math.max(0, Math.min(1, cis / 100));
  const lerp = (a: number, b: number, f: number) => Math.round(a + (b - a) * f);
  if (t < 0.5) {
    const f = t / 0.5;
    return [lerp(45, 245, f), lerp(212, 180, f), lerp(191, 60, f)];
  }
  const f = (t - 0.5) / 0.5;
  return [lerp(245, 239, f), lerp(180, 68, f), lerp(60, 68, f)];
}
export const cssRgb = (c: number[]) => `rgb(${c[0]},${c[1]},${c[2]})`;
export const cisCss = (cis: number) => cssRgb(cisColor(cis));

export function parseWindow(w?: string): [number, number] | null {
  if (!w) return null;
  const m = w.match(/(\d{1,2}):00-(\d{1,2}):00/);
  if (!m) return null;
  return [parseInt(m[1]), parseInt(m[2])];
}
export function hourInWindow(h: number, w?: string): boolean {
  const r = parseWindow(w);
  if (!r) return true;
  let [s, e] = r;
  if (e === 0) e = 24;
  return s <= e ? h >= s && h < e : h >= s || h < e;
}
export const fmtHour = (h: number) => `${String(h % 24).padStart(2, "0")}:00`;
export const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
