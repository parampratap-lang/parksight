import { H3HexagonLayer, HeatmapLayer, PathLayer, ScatterplotLayer } from "deck.gl";
import type { Hotspot, LayerMode, Route } from "../types";
import { cisColor, hourInWindow } from "../util";

interface Props {
  hotspots: Hotspot[];
  routes: Route[];
  layerMode: LayerMode;
  hourFilter: number | null;
  selectedId: string | null;
  highlightIds: string[];
  activeStation: string | null;
}

const ROUTE_COLORS: [number, number, number][] = [
  [56, 189, 248], [167, 139, 250], [52, 211, 153], [251, 191, 36],
  [244, 114, 182], [248, 113, 113],
];

export function buildLayers(p: Props): any[] {
  const { hotspots, routes, layerMode, hourFilter, selectedId, highlightIds, activeStation } = p;
  const layers: any[] = [];

  if (layerMode === "heatmap") {
    layers.push(
      new HeatmapLayer({
        id: "heat",
        data: hotspots,
        getPosition: (d: Hotspot) => [d.lon, d.lat],
        getWeight: (d: Hotspot) => d.weighted_volume,
        radiusPixels: 55,
        intensity: 1,
        threshold: 0.04,
      }),
    );
  } else {
    // hero: extruded H3 hexagons coloured + sized by CIS
    layers.push(
      new H3HexagonLayer({
        id: "hex",
        data: hotspots,
        pickable: true,
        extruded: true,
        elevationScale: 28,
        getHexagon: (d: Hotspot) => d.h3,
        getElevation: (d: Hotspot) => {
          const dim = hourFilter !== null && !hourInWindow(hourFilter, d.peak_window?.window);
          return d.cis * (dim ? 0.18 : 1);
        },
        getFillColor: (d: Hotspot) => {
          const [r, g, b] = cisColor(d.cis);
          const active = hourFilter === null || hourInWindow(hourFilter, d.peak_window?.window);
          return [r, g, b, active ? 220 : 45];
        },
        material: { ambient: 0.6, diffuse: 0.6, shininess: 32 },
        updateTriggers: {
          getFillColor: [hourFilter],
          getElevation: [hourFilter],
        },
      }),
    );
  }

  if (layerMode === "routes") {
    const shown = activeStation ? routes.filter((r) => r.police_station === activeStation) : routes;
    layers.push(
      new PathLayer({
        id: "routes",
        data: shown.filter((r) => r.geojson_line),
        getPath: (r: Route) => r.geojson_line!.coordinates,
        getColor: (_r: Route, { index }: any) => ROUTE_COLORS[index % ROUTE_COLORS.length],
        getWidth: 4,
        widthUnits: "pixels",
        capRounded: true,
        jointRounded: true,
      }),
    );
    layers.push(
      new ScatterplotLayer({
        id: "stops",
        data: shown.flatMap((r) => r.stops),
        getPosition: (s: any) => [s.lon, s.lat],
        getRadius: 7,
        radiusUnits: "pixels",
        getFillColor: (s: any) => cisColor(s.cis),
        stroked: true,
        getLineColor: [255, 255, 255],
        lineWidthUnits: "pixels",
        getLineWidth: 1.5,
        pickable: true,
      }),
    );
  }

  // selection / assistant highlight rings
  const ringIds = new Set([selectedId, ...highlightIds].filter(Boolean) as string[]);
  if (ringIds.size) {
    layers.push(
      new ScatterplotLayer({
        id: "rings",
        data: hotspots.filter((h) => ringIds.has(h.id)),
        getPosition: (d: Hotspot) => [d.lon, d.lat],
        getRadius: 140,
        radiusUnits: "meters",
        radiusMinPixels: 10,
        stroked: true,
        filled: false,
        getLineColor: (d: Hotspot) => (d.id === selectedId ? [255, 255, 255] : [56, 189, 248]),
        lineWidthUnits: "pixels",
        getLineWidth: 3,
        updateTriggers: { getLineColor: [selectedId] },
      }),
    );
  }
  return layers;
}
