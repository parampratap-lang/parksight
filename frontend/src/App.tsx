import MapView from "./components/MapView";
import KpiBar from "./components/KpiBar";
import Controls from "./components/Controls";
import RightRail from "./components/RightRail";
import HotspotDrawer from "./components/HotspotDrawer";
import AssistantPanel from "./components/AssistantPanel";

export default function App() {
  return (
    <>
      <div className="map-layer"><MapView /></div>

      <header className="brand-dock">
        <div className="brand">
          <span className="logo" />
          <div>
            <div className="brand-name">ParkSight</div>
            <div className="brand-sub">Bengaluru parking-congestion intelligence</div>
          </div>
        </div>
        <AssistantPanel />
      </header>

      <div className="topbar"><KpiBar /></div>
      <Controls />
      <RightRail />
      <HotspotDrawer />
    </>
  );
}
