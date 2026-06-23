import { useHotspots } from "../api/hooks";
import { useApp } from "../context/AppContext";
import { cisCss } from "../util";
import CISBreakdownChart from "./CISBreakdownChart";
import TemporalHeatmap from "./TemporalHeatmap";
import BriefPanel from "./BriefPanel";

export default function HotspotDrawer() {
  const { selectedId, setSelectedId } = useApp();
  const { data: hotspots = [] } = useHotspots();
  if (!selectedId) return null;
  const h = hotspots.find((x) => x.id === selectedId);
  if (!h) return null;

  const topViolations = Object.entries(h.violation_mix).slice(0, 3);
  const topVehicles = Object.entries(h.vehicle_mix).slice(0, 3);

  return (
    <div className="drawer">
      <div className="drawer-head">
        <div>
          <div className="drawer-rank">#{h.rank} enforcement priority</div>
          <div className="drawer-name">{h.name}</div>
          <div className="small muted">
            {h.police_station} · {h.nearest_junction?.is_named ? h.nearest_junction.name : "no named junction"}
          </div>
        </div>
        <button className="x" onClick={() => setSelectedId(null)}>✕</button>
      </div>

      <div className="drawer-stats">
        <div className="stat"><span className="cis-pill big" style={{ background: cisCss(h.cis) }}>{h.cis}</span><span className="small muted">CIS</span></div>
        <div className="stat"><b>{h.total_violations.toLocaleString()}</b><span className="small muted">violations</span></div>
        <div className="stat"><b>{Math.round(h.recurrence * 100)}%</b><span className="small muted">days active</span></div>
        <div className="stat"><b>{h.peak_window?.shift}</b><span className="small muted">{h.peak_window?.window}</span></div>
      </div>

      <div className="tags">
        {topViolations.map(([k, v]) => <span className="tag" key={k}>{k} · {v}</span>)}
        {topVehicles.map(([k, v]) => <span className="tag alt" key={k}>{k} · {v}</span>)}
      </div>

      <CISBreakdownChart h={h} />
      <TemporalHeatmap id={h.id} />
      <BriefPanel id={h.id} />
    </div>
  );
}
