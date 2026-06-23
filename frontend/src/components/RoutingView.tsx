import { useRoutes } from "../api/hooks";
import { useApp } from "../context/AppContext";
import { cisCss, fmtHour } from "../util";

export default function RoutingView() {
  const { data: routes = [] } = useRoutes();
  const { activeStation, setActiveStation, setLayerMode, setSelectedId } = useApp();

  return (
    <div className="list">
      <div className="list-head small muted">
        Optimised patrol route per station · ordered by impact, timed to peaks
      </div>
      {routes.map((r) => {
        const open = r.police_station === activeStation;
        return (
          <div key={r.police_station} className={`route${open ? " open" : ""}`}>
            <button
              className="route-head"
              onClick={() => {
                const next = open ? null : r.police_station;
                setActiveStation(next);
                setLayerMode("routes");
              }}
            >
              <span className="row-name">{r.police_station}</span>
              <span className="small muted">{r.n_stops} stops · {r.total_km} km</span>
            </button>
            {open && (
              <ol className="route-stops">
                {r.stops.map((s) => (
                  <li key={s.id} onClick={() => setSelectedId(s.id)}>
                    <span className="dot" style={{ background: cisCss(s.cis) }} />
                    <span className="row-name">{s.name}</span>
                    <span className="small muted">CIS {s.cis} · ~{fmtHour(s.peak_hour)}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        );
      })}
    </div>
  );
}
