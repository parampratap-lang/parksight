import { useState } from "react";
import HotspotPanel from "./HotspotPanel";
import RoutingView from "./RoutingView";

export default function RightRail() {
  const [tab, setTab] = useState<"hotspots" | "routes">("hotspots");
  return (
    <aside className="rail">
      <div className="rail-tabs">
        <button className={tab === "hotspots" ? "tab active" : "tab"} onClick={() => setTab("hotspots")}>
          Enforcement priority
        </button>
        <button className={tab === "routes" ? "tab active" : "tab"} onClick={() => setTab("routes")}>
          Patrol routes
        </button>
      </div>
      {tab === "hotspots" ? <HotspotPanel /> : <RoutingView />}
    </aside>
  );
}
