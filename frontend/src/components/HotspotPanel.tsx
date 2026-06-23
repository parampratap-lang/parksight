import { useHotspots } from "../api/hooks";
import { useApp } from "../context/AppContext";
import { cisCss } from "../util";

export default function HotspotPanel() {
  const { data: hotspots = [] } = useHotspots();
  const { selectedId, setSelectedId, setHoveredId, highlightIds } = useApp();
  const top = hotspots.slice(0, 100);

  return (
    <div className="list">
      <div className="list-head small muted">
        Ranked by Congestion Impact Score · top {top.length} of {hotspots.length}
      </div>
      {top.map((h) => {
        const active = h.id === selectedId;
        const hi = highlightIds.includes(h.id);
        return (
          <button
            key={h.id}
            className={`row${active ? " active" : ""}${hi ? " hi" : ""}`}
            onClick={() => setSelectedId(h.id)}
            onMouseEnter={() => setHoveredId(h.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            <span className="row-rank">{h.rank}</span>
            <span className="row-main">
              <span className="row-name">{h.name}</span>
              <span className="row-sub small muted">
                {h.police_station} · {h.peak_window?.class} {h.peak_window?.window}
              </span>
            </span>
            <span className="cis-pill" style={{ background: cisCss(h.cis) }}>{h.cis}</span>
          </button>
        );
      })}
    </div>
  );
}
