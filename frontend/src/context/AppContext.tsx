import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { LayerMode } from "../types";

interface AppState {
  selectedId: string | null;
  setSelectedId: (id: string | null) => void;
  hoveredId: string | null;
  setHoveredId: (id: string | null) => void;
  hourFilter: number | null;            // null = all hours
  setHourFilter: (h: number | null) => void;
  layerMode: LayerMode;
  setLayerMode: (m: LayerMode) => void;
  activeStation: string | null;
  setActiveStation: (s: string | null) => void;
  highlightIds: string[];               // hotspots the assistant referenced
  setHighlightIds: (ids: string[]) => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [hourFilter, setHourFilter] = useState<number | null>(null);
  const [layerMode, setLayerMode] = useState<LayerMode>("hex");
  const [activeStation, setActiveStation] = useState<string | null>(null);
  const [highlightIds, setHighlightIds] = useState<string[]>([]);
  const value = useMemo(
    () => ({ selectedId, setSelectedId, hoveredId, setHoveredId, hourFilter,
      setHourFilter, layerMode, setLayerMode, activeStation, setActiveStation,
      highlightIds, setHighlightIds }),
    [selectedId, hoveredId, hourFilter, layerMode, activeStation, highlightIds],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useApp outside provider");
  return c;
}
