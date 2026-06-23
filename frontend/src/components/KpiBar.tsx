import { useKpis } from "../api/hooks";

export default function KpiBar() {
  const { data } = useKpis();
  const f = (n?: number) => (n ?? 0).toLocaleString();
  const stats = data
    ? [
        { label: "Parking violations", value: f(data.total_parking) },
        { label: "Illegal-parking hotspots", value: f(data.hotspot_count) },
        { label: "Citywide peak", value: data.city_peak.window, sub: data.city_peak.class },
        { label: "#1 hotspot", value: data.top_hotspots?.[0]?.name ?? "—",
          sub: `CIS ${data.top_hotspots?.[0]?.cis ?? ""}` },
      ]
    : [];
  return (
    <div className="kpibar">
      {!data && <div className="muted small">Loading KPIs…</div>}
      {stats.map((s) => (
        <div className="kpi" key={s.label}>
          <div className="kpi-value">{s.value}</div>
          <div className="kpi-label">{s.label}{s.sub ? ` · ${s.sub}` : ""}</div>
        </div>
      ))}
    </div>
  );
}
