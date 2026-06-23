import { useMemo } from "react";
import { DeckGL } from "deck.gl";
import { Map } from "react-map-gl/maplibre";
import { useApp } from "../context/AppContext";
import { useHotspots, useRoutes } from "../api/hooks";
import { buildLayers } from "./layers";
import type { Hotspot } from "../types";

const CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const INITIAL_VIEW = {
  longitude: 77.59, latitude: 12.97, zoom: 11, pitch: 48, bearing: -12,
};

export default function MapView() {
  const { setSelectedId, setHoveredId, hourFilter, layerMode, selectedId,
    highlightIds, activeStation } = useApp();
  const { data: hotspots = [] } = useHotspots();
  const { data: routes = [] } = useRoutes();

  const layers = useMemo(
    () => buildLayers({ hotspots, routes, layerMode, hourFilter, selectedId, highlightIds, activeStation }),
    [hotspots, routes, layerMode, hourFilter, selectedId, highlightIds, activeStation],
  );

  return (
    <DeckGL
      initialViewState={INITIAL_VIEW}
      controller={true}
      layers={layers}
      onClick={(info: any) => {
        if (info?.object && (info.object as Hotspot).id) setSelectedId((info.object as Hotspot).id);
      }}
      onHover={(info: any) => setHoveredId(info?.object?.id ?? null)}
      getTooltip={({ object }: any) =>
        object && object.cis !== undefined && {
          html: `<b>${object.name ?? "Hotspot"}</b><br/>CIS ${object.cis} · #${object.rank ?? "?"}<br/>${object.police_station ?? ""}`,
          style: { background: "#0b1220", color: "#e5edff", fontSize: "12px",
            padding: "6px 8px", borderRadius: "6px", border: "1px solid #1e293b" },
        }
      }
    >
      <Map reuseMaps mapStyle={CARTO_DARK} />
    </DeckGL>
  );
}
