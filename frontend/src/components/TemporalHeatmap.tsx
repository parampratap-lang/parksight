import { useTemporal } from "../api/hooks";
import { DOW } from "../util";

export default function TemporalHeatmap({ id }: { id: string }) {
  const { data } = useTemporal(id);
  if (!data) return <div className="card"><div className="card-title">When it flares</div><div className="muted small">Loading…</div></div>;
  const m = data.matrix_rate;
  const max = Math.max(0.0001, ...m.flat());
  return (
    <div className="card">
      <div className="card-title">When it flares · peak {data.peak.class} {data.peak.window}</div>
      <div className="heat">
        <div className="heat-row heat-axis">
          <span className="heat-dow" />
          {Array.from({ length: 24 }).map((_, h) => (
            <span key={h} className="heat-h">{h % 6 === 0 ? h : ""}</span>
          ))}
        </div>
        {m.map((row, d) => (
          <div className="heat-row" key={d}>
            <span className="heat-dow">{DOW[d]}</span>
            {row.map((v, h) => (
              <span key={h} className="heat-cell"
                title={`${DOW[d]} ${h}:00 · ${v.toFixed(2)}/day`}
                style={{ background: `rgba(248,113,113,${Math.min(1, (v / max) * 0.95 + (v > 0 ? 0.05 : 0))})` }} />
            ))}
          </div>
        ))}
      </div>
      <div className="small muted" style={{ marginTop: 4 }}>
        Expected violations per weekday-hour (IST), learned from 151 days.
      </div>
    </div>
  );
}
