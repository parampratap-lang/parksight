"""Pipeline stages: raw CSV -> cleaned frame -> artifact dicts.

DuckDB does the fast CSV scan + geo/validation filter; pandas does the modeling
(JSON-array parsing, H3 binning, CIS, temporal, routing). ~285K rows post-filter
fit comfortably in pandas.
"""
from __future__ import annotations
import json
from collections import Counter

import duckdb
import h3
import numpy as np
import pandas as pd

import config as C
import methodology as M


# ----------------------------------------------------------------- load + clean
def load_clean(sample: int | None = None) -> tuple[pd.DataFrame, dict, int]:
    con = duckdb.connect()
    csv = str(C.CSV_PATH)
    rd = (f"read_csv_auto('{csv}', ignore_errors=true, sample_size=-1, "
          f"all_varchar=true)")
    b = C.GEO_BOUNDS
    geo = (f"TRY_CAST(latitude AS DOUBLE) BETWEEN {b['lat_min']} AND {b['lat_max']} "
           f"AND TRY_CAST(longitude AS DOUBLE) BETWEEN {b['lon_min']} AND {b['lon_max']}")

    raw_count = con.execute(f"SELECT count(*) FROM {rd}").fetchone()[0]
    limit = f"LIMIT {sample}" if sample else ""
    # geo filter only in SQL; validation + parking filters in pandas so the
    # data-quality funnel is computed over one consistent population.
    df = con.execute(f"""
        SELECT TRY_CAST(latitude AS DOUBLE) AS lat,
               TRY_CAST(longitude AS DOUBLE) AS lon,
               location, vehicle_number, vehicle_type, violation_type,
               created_datetime, junction_name, police_station, validation_status
        FROM {rd}
        WHERE {geo}
        {limit}
    """).df()
    con.close()
    after_geo = len(df)

    # parse the violation_type JSON array -> parking labels (needed for the funnel)
    def parking_labels(s):
        try:
            return [x for x in json.loads(s) if x in C.PARKING_TYPES]
        except Exception:
            return []
    df["parking_labels"] = df["violation_type"].apply(parking_labels)
    parking_among_geo = int((df["parking_labels"].map(len) > 0).sum())

    # validation filter: drop confirmed non-violations (rejected/duplicate); keep NULL/approved/etc.
    df = df[~df["validation_status"].isin(C.DROP_VALIDATION)].copy()
    after_validation = len(df)
    # parking filter
    df = df[df["parking_labels"].map(len) > 0].copy()
    after_parking = len(df)

    # Temporal parts. Stamps carry a "+00" suffix but the wall-clock distribution
    # (evening->overnight peak, dead midday) is the local IST enforcement pattern,
    # i.e. the offset is mislabeled. We therefore read the literal wall-clock time.
    dt = pd.to_datetime(df["created_datetime"], utc=True, errors="coerce").dt.tz_localize(None)
    df["hour"] = dt.dt.hour
    df["dow"] = dt.dt.weekday          # Mon=0 .. Sun=6
    df["date"] = dt.dt.floor("D")      # datetime64 (NaT-safe for agg)

    # per-row weights / lookups
    df["cw"] = df["validation_status"].map(lambda s: C.CONFIDENCE.get(s, C.CONFIDENCE["_default"]))
    df["fp"] = df["vehicle_type"].map(M.footprint_of)
    df["area"] = df["location"].fillna("").str.split(",").str[0].str.strip()
    df["h3"] = [h3.latlng_to_cell(la, lo, C.H3_RES) for la, lo in zip(df["lat"], df["lon"])]

    funnel = {"raw": int(raw_count), "after_geofence": int(after_geo),
              "parking_among_geofence": parking_among_geo,
              "after_validation": int(after_validation), "after_parking": int(after_parking)}
    return df, funnel, int(raw_count)


# ----------------------------------------------------------------- helpers
def _mode(series: pd.Series):
    s = series.dropna()
    if s.empty:
        return None
    m = s.mode()
    return m.iat[0] if not m.empty else None


def _top_counts(items, n=5) -> dict:
    return dict(Counter(items).most_common(n))


# ----------------------------------------------------------------- hotspots + CIS
def build_hotspots(df: pd.DataFrame, obs_days: int) -> tuple[list[dict], pd.DataFrame]:
    g = df.groupby("h3")
    stats = pd.DataFrame({
        "weighted_count": g["cw"].sum(),
        "total": g.size(),
        "footprint": g["fp"].mean(),
        "active_days": g["date"].nunique(),
        "station": g["police_station"].agg(_mode),
        "junction": g["junction_name"].agg(_mode),
        "area": g["area"].agg(_mode),
        "first_seen": g["date"].min().dt.strftime("%Y-%m-%d"),
        "last_seen": g["date"].max().dt.strftime("%Y-%m-%d"),
    })
    # severity = mean over exploded parking-label occurrences per cell
    exp = df[["h3", "parking_labels"]].explode("parking_labels")
    exp["sev"] = exp["parking_labels"].map(M.severity_of)
    stats["severity"] = exp.groupby("h3")["sev"].mean()

    stats = stats[stats["weighted_count"] >= C.MIN_VIOLATIONS].copy()

    # normalized components
    stats["V"] = M.normalize_log_volume(stats["weighted_count"].to_numpy())
    stats["S"] = stats["severity"].clip(0, 1)
    stats["P"] = (stats["active_days"] / obs_days).clip(0, 1)
    stats["F"] = stats["footprint"].clip(0, 1)
    stats["J"] = stats["junction"].map(M.junction_weight)

    # violation / vehicle mixes per cell (plain dicts; .apply on a dict-return
    # would get expanded into a float MultiIndex Series by pandas)
    vmix = {cell: _top_counts(list(sub)) for cell, sub in exp.groupby("h3")["parking_labels"]}
    vehmix = {cell: _top_counts(list(sub)) for cell, sub in df.groupby("h3")["vehicle_type"]}

    hotspots = []
    for cell, r in stats.iterrows():
        comp = [r["S"], r["V"], r["P"], r["F"], r["J"]]
        cis, breakdown = M.compute_cis(*comp)
        cis_eq = round(100.0 * float(np.mean(comp)), 1)
        lat, lon = h3.cell_to_latlng(cell)
        mix = vmix.get(cell, {})
        named = r["junction"] not in C.NO_JUNCTION_LABELS
        hotspots.append({
            "id": cell, "h3": cell,
            "lat": round(lat, 6), "lon": round(lon, 6),
            "cis": cis, "cis_equal": cis_eq, "cis_breakdown": breakdown,
            "total_violations": int(r["total"]),
            "weighted_volume": round(float(r["weighted_count"]), 1),
            "violation_mix": {k: int(v) for k, v in mix.items()},
            "vehicle_mix": {k: int(v) for k, v in vehmix.get(cell, {}).items()},
            "dominant_violation": next(iter(mix), None),
            "name": r["area"] or (r["junction"] if named else r["station"]) or "Unknown",
            "police_station": r["station"],
            "nearest_junction": {"name": r["junction"], "is_named": bool(named)},
            "first_seen": r["first_seen"], "last_seen": r["last_seen"],
            "active_days": int(r["active_days"]),
            "recurrence": round(float(r["P"]), 3),
        })
    hotspots.sort(key=lambda h: -h["cis"])
    for i, h in enumerate(hotspots, 1):
        h["rank"] = i
    return hotspots, stats


# ----------------------------------------------------------------- temporal
def _matrix(sub: pd.DataFrame, dow_counts: np.ndarray) -> np.ndarray:
    counts = np.zeros((7, 24))
    timed = sub.dropna(subset=["hour", "dow"])
    for d, h in zip(timed["dow"].astype(int), timed["hour"].astype(int)):
        counts[d, h] += 1
    rate = counts / dow_counts[:, None]
    return rate


def build_temporal(df: pd.DataFrame, hotspots: list[dict], dow_counts: np.ndarray):
    profiles = {}
    for h in hotspots:
        sub = df[df["h3"] == h["id"]]
        rate = _matrix(sub, dow_counts)
        pk = M.peak_windows(rate)
        profiles[h["id"]] = {
            "h3": h["id"],
            "matrix_rate": np.round(rate, 3).tolist(),
            "peak": pk,
        }
        # attach a compact peak summary onto the hotspot itself
        h["peak_window"] = {"class": pk["class"], "window": pk["window"],
                            "peak_hour": pk["peak_hour"], "shift": M.shift_of(pk["peak_hour"])}
    city_rate = _matrix(df, dow_counts)
    city = {"matrix_rate": np.round(city_rate, 3).tolist(), "peak": M.peak_windows(city_rate)}
    return profiles, city


# ----------------------------------------------------------------- routes
def build_routes(hotspots: list[dict]) -> list[dict]:
    top = hotspots[:C.ROUTE_TOP_N]
    routes = []
    by_station: dict[str, list[dict]] = {}
    for h in top:
        by_station.setdefault(h["police_station"] or "Unassigned", []).append(h)
    for station, hs in by_station.items():
        stops = [{"id": h["id"], "lat": h["lat"], "lon": h["lon"], "cis": h["cis"],
                  "name": h["name"], "rank": h["rank"],
                  "peak_hour": h["peak_window"]["peak_hour"],
                  "window": h["peak_window"]["window"]} for h in hs]
        r = M.order_route(stops)
        routes.append({
            "police_station": station,
            "n_stops": len(stops),
            "total_km": r["total_km"],
            "total_cis": round(sum(s["cis"] for s in stops), 1),
            "stops": r["ordered"],
            "geojson_line": r["geojson_line"],
        })
    routes.sort(key=lambda r: -r["total_cis"])
    return routes


# ----------------------------------------------------------------- offenders
def build_offenders(df: pd.DataFrame) -> list[dict]:
    valid = df[df["vehicle_number"].notna() & (df["vehicle_number"] != "NULL")]
    g = valid.groupby("vehicle_number")
    agg = pd.DataFrame({
        "count": g.size(),
        "vehicle_type": g["vehicle_type"].agg(_mode),
        "distinct_hotspots": g["h3"].nunique(),
        "first_seen": g["date"].min().dt.strftime("%Y-%m-%d"),
        "last_seen": g["date"].max().dt.strftime("%Y-%m-%d"),
    })
    agg = agg[agg["count"] >= C.OFFENDER_MIN_COUNT].sort_values("count", ascending=False).head(C.OFFENDER_TOP_N)
    stations = g["police_station"].apply(lambda s: list(pd.Series(s).dropna().unique()[:4]))
    out = []
    for veh, r in agg.iterrows():
        out.append({
            "vehicle_number": veh, "vehicle_type": r["vehicle_type"],
            "count": int(r["count"]), "distinct_hotspots": int(r["distinct_hotspots"]),
            "stations": stations.get(veh, []),
            "first_seen": r["first_seen"], "last_seen": r["last_seen"],
        })
    return out


# ----------------------------------------------------------------- stations
def build_stations(hotspots: list[dict], df: pd.DataFrame) -> list[dict]:
    by = {}
    for h in hotspots:
        by.setdefault(h["police_station"] or "Unassigned", []).append(h)
    station_totals = df.groupby("police_station").size()
    out = []
    for st, hs in by.items():
        cis_vals = [h["cis"] for h in hs]
        types = Counter()
        for h in hs:
            types.update(h["violation_mix"])
        out.append({
            "police_station": st,
            "hotspot_count": len(hs),
            "mean_cis": round(float(np.mean(cis_vals)), 1),
            "max_cis": round(float(np.max(cis_vals)), 1),
            "total_violations": int(station_totals.get(st, 0)),
            "top_violation": next(iter([k for k, _ in types.most_common(1)]), None),
        })
    out.sort(key=lambda s: -s["max_cis"])
    return out


# ----------------------------------------------------------------- kpis
def build_kpis(df: pd.DataFrame, funnel: dict, hotspots: list[dict],
               offenders: list[dict], city: dict) -> dict:
    vt = Counter()
    for ls in df["parking_labels"]:
        vt.update(ls)
    veh = Counter(df["vehicle_type"].dropna())
    n_offender_rows = sum(o["count"] for o in offenders)
    return {
        "total_violations_raw": funnel["raw"],
        "total_parking": funnel["after_parking"],
        "parking_pct": round(100.0 * funnel["parking_among_geofence"] / max(funnel["after_geofence"], 1), 1),
        "hotspot_count": len(hotspots),
        "date_range": {"start": df["date"].min().strftime("%Y-%m-%d"),
                       "end": df["date"].max().strftime("%Y-%m-%d")},
        "data_quality_funnel": funnel,
        "violation_type_dist": dict(vt.most_common(12)),
        "vehicle_type_dist": dict(veh.most_common(12)),
        "top_stations": [{"police_station": h["police_station"]} for h in hotspots[:5]],
        "city_peak": city["peak"],
        "repeat_offenders": len(offenders),
        "repeat_offender_violations": int(n_offender_rows),
        "top_hotspots": [{"rank": h["rank"], "name": h["name"], "cis": h["cis"],
                          "police_station": h["police_station"]} for h in hotspots[:10]],
    }


# ----------------------------------------------------------------- meta
def build_meta(funnel: dict, hotspots: list[dict], obs_days: int) -> dict:
    weighted = np.array([h["cis"] for h in hotspots])
    equal = np.array([h["cis_equal"] for h in hotspots])
    rho = M.spearman(weighted, equal) if len(hotspots) > 2 else 1.0
    return {
        "h3_resolution": C.H3_RES,
        "min_violations": C.MIN_VIOLATIONS,
        "observation_days": obs_days,
        "cis_weights": C.CIS_WEIGHTS,
        "severity_table": C.SEVERITY,
        "footprint_table": C.FOOTPRINT,
        "geo_bounds": C.GEO_BOUNDS,
        "row_counts": funnel,
        "hotspot_count": len(hotspots),
        "robustness_spearman": round(rho, 4),
        "methodology_note": ("CIS is a transparent prioritization index, not a measured "
                             "congestion delay. Components: road-criticality severity, "
                             "log-scaled volume, temporal persistence, vehicle footprint (PCU-inspired), "
                             "junction proximity."),
    }
