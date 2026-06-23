export interface CisComponent { value: number; weight: number; points: number; [k: string]: any }
export interface Hotspot {
  id: string; h3: string; lat: number; lon: number;
  cis: number; cis_equal: number;
  cis_breakdown: Record<string, CisComponent>;
  total_violations: number; weighted_volume: number;
  violation_mix: Record<string, number>;
  vehicle_mix: Record<string, number>;
  dominant_violation: string | null;
  name: string; police_station: string;
  nearest_junction: { name: string; is_named: boolean };
  first_seen: string; last_seen: string; active_days: number; recurrence: number;
  rank: number;
  peak_window: { class: string; window: string; peak_hour: number; shift: string };
}
export interface Kpis {
  total_violations_raw: number; total_parking: number; parking_pct: number;
  hotspot_count: number; date_range: { start: string; end: string };
  data_quality_funnel: Record<string, number>;
  violation_type_dist: Record<string, number>;
  vehicle_type_dist: Record<string, number>;
  city_peak: { class: string; window: string; peak_hour: number };
  repeat_offenders: number; repeat_offender_violations: number;
  top_hotspots: { rank: number; name: string; cis: number; police_station: string }[];
}
export interface Temporal {
  h3: string; matrix_rate: number[][];
  peak: { class: string; window: string; peak_hour: number; peak_rate: number;
    weekday_mean: number; weekend_mean: number;
    top_buckets: { dow: string; hour: number; rate: number }[] };
}
export interface RouteStop { id: string; lat: number; lon: number; cis: number; name: string; rank: number; peak_hour: number; window: string; order: number }
export interface Route {
  police_station: string; n_stops: number; total_km: number; total_cis: number;
  stops: RouteStop[]; geojson_line: { type: string; coordinates: [number, number][] } | null;
}
export type LayerMode = "hex" | "heatmap" | "routes";
