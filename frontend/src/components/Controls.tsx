import { useApp } from "../context/AppContext";
import { cisCss, fmtHour } from "../util";
import type { LayerMode } from "../types";

const MODES: { id: LayerMode; label: string }[] = [
  { id: "hex", label: "Hotspots 3D" },
  { id: "heatmap", label: "Heatmap" },
  { id: "routes", label: "Patrol routes" },
];

export default function Controls() {
  const { hourFilter, setHourFilter, layerMode, setLayerMode } = useApp();
  return (
    <div className="controls">
      <div className="seg">
        {MODES.map((m) => (
          <button
            key={m.id}
            className={layerMode === m.id ? "seg-btn active" : "seg-btn"}
            onClick={() => setLayerMode(m.id)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="timeslider">
        <div className="ts-head">
          <span>Time of day</span>
          <span className="ts-val">{hourFilter === null ? "All hours" : fmtHour(hourFilter)}</span>
        </div>
        <input
          type="range" min={0} max={23} step={1}
          value={hourFilter ?? 0}
          onChange={(e) => setHourFilter(Number(e.target.value))}
        />
        <button className="ts-reset" onClick={() => setHourFilter(null)} disabled={hourFilter === null}>
          Reset
        </button>
      </div>

      <div className="legend">
        <span className="small muted">Congestion Impact</span>
        <div className="legend-bar">
          {[10, 30, 50, 70, 90].map((c) => (
            <span key={c} className="legend-swatch" style={{ background: cisCss(c) }} />
          ))}
        </div>
        <div className="legend-ax"><span>low</span><span>high</span></div>
      </div>
    </div>
  );
}
