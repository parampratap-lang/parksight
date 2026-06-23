import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Hotspot } from "../types";

const LABELS: Record<string, string> = {
  severity: "Road criticality", volume: "Violation volume",
  persistence: "Recurrence", junction: "Junction proximity", footprint: "Vehicle footprint",
};
const COLORS: Record<string, string> = {
  severity: "#f87171", volume: "#fb923c", persistence: "#fbbf24",
  junction: "#38bdf8", footprint: "#a78bfa",
};
const ORDER = ["severity", "volume", "persistence", "junction", "footprint"];

export default function CISBreakdownChart({ h }: { h: Hotspot }) {
  const data = ORDER.filter((k) => h.cis_breakdown[k]).map((k) => ({
    key: k, name: LABELS[k] ?? k,
    points: Math.round((h.cis_breakdown[k].points ?? 0) * 10) / 10,
  }));
  return (
    <div className="card">
      <div className="card-title">Why this score · CIS {h.cis}/100</div>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 2, bottom: 2 }}>
          <XAxis type="number" domain={[0, 35]} tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="name" width={108} tick={{ fill: "#cbd5e1", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip cursor={{ fill: "#1e293b55" }}
            contentStyle={{ background: "#0b1220", border: "1px solid #1e293b", borderRadius: 8, fontSize: 12 }}
            formatter={(v: any) => [`${v} pts`, "contribution"]} />
          <Bar dataKey="points" radius={[0, 4, 4, 0]}>
            {data.map((d) => <Cell key={d.key} fill={COLORS[d.key] ?? "#64748b"} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="small muted" style={{ marginTop: 4 }}>
        Transparent index — capacity removed × volume × recurrence × footprint × junction.
      </div>
    </div>
  );
}
