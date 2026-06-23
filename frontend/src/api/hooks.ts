import useSWR from "swr";
import { fetcher } from "./client";
import type { Hotspot, Kpis, Route, Temporal } from "../types";

const opts = { revalidateOnFocus: false, revalidateIfStale: false };

export const useKpis = () => useSWR<Kpis>("/api/kpis", fetcher, opts);
export const useHotspots = () => useSWR<Hotspot[]>("/api/hotspots", fetcher, opts);
export const useRoutes = () => useSWR<Route[]>("/api/routes", fetcher, opts);
export const useMeta = () => useSWR<any>("/api/meta", fetcher, opts);
export const useTemporal = (id?: string | null) =>
  useSWR<Temporal>(id ? `/api/temporal/${id}` : null, fetcher, opts);
