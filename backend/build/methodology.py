"""The defensible analytical core: CIS scoring, peak-window extraction, routing.

Pure functions over plain numbers / numpy — no IO. Imported by stages.py.
"""
from __future__ import annotations
import math
import numpy as np

import config as C

DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ----------------------------------------------------------------- lookups
def severity_of(label: str) -> float:
    return C.SEVERITY.get(label, C.SEVERITY["_default"])


def footprint_of(vehicle_type: str) -> float:
    return C.FOOTPRINT.get(vehicle_type, C.FOOTPRINT["_default"])


def junction_weight(name: str | None) -> float:
    return C.JUNCTION_NONE if name in C.NO_JUNCTION_LABELS else C.JUNCTION_NAMED


# ----------------------------------------------------------------- CIS
def normalize_log_volume(weighted_counts: np.ndarray) -> np.ndarray:
    """Log-compress then min-max to [0,1] across all qualifying cells."""
    lv = np.log1p(weighted_counts)
    lo, hi = lv.min(), lv.max()
    if hi - lo < 1e-9:
        return np.ones_like(lv)
    return (lv - lo) / (hi - lo)


def compute_cis(S: float, V: float, P: float, F: float, J: float) -> tuple[float, dict]:
    """Combine the five [0,1] components into a 0-100 score + explainable breakdown.

    Each breakdown entry carries the raw component value, its weight, and its
    *points contribution* (100 * weight * value) so the UI can render a stacked bar
    that literally sums to the score.
    """
    w = C.CIS_WEIGHTS
    comps = {"severity": S, "volume": V, "persistence": P, "footprint": F, "junction": J}
    breakdown = {}
    total = 0.0
    for k, val in comps.items():
        pts = 100.0 * w[k] * val
        total += pts
        breakdown[k] = {"value": round(val, 4), "weight": w[k], "points": round(pts, 2)}
    return round(total, 1), breakdown


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation without scipy (rank -> Pearson)."""
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = math.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra * rb).sum() / denom) if denom else 0.0


# ----------------------------------------------------------------- temporal
def smooth_circular(row: np.ndarray, taps: int = 3) -> np.ndarray:
    """3-tap circular moving average across the 24 hours (hours wrap)."""
    k = taps // 2
    return np.array([row[(np.arange(-k, k + 1) + i) % len(row)].mean() for i in range(len(row))])


def peak_windows(matrix: np.ndarray) -> dict:
    """matrix: 7x24 rate matrix (dow x hour, IST). Return peak window + classes.

    Collapse to weekday (Mon-Fri) vs weekend (Sat-Sun), pick the higher-mean
    class, then take the contiguous run of hours >= PEAK_FRAC * class-max around
    the peak hour as the actionable enforcement window.
    """
    weekday = matrix[0:5].mean(axis=0)
    weekend = matrix[5:7].mean(axis=0)
    wd_mean, we_mean = float(weekday.mean()), float(weekend.mean())
    cls, profile = ("Weekday", weekday) if wd_mean >= we_mean else ("Weekend", weekend)
    profile = smooth_circular(profile)

    peak_hour = int(profile.argmax())
    thresh = C.PEAK_FRAC * profile.max()
    # expand contiguously left/right from the peak hour while above threshold
    start = peak_hour
    while profile[(start - 1) % 24] >= thresh and (start - 1) % 24 != peak_hour:
        start = (start - 1) % 24
    end = peak_hour
    while profile[(end + 1) % 24] >= thresh and (end + 1) % 24 != peak_hour:
        end = (end + 1) % 24

    # top-3 (dow, hour) buckets across the full matrix
    flat = [(matrix[d, h], d, h) for d in range(7) for h in range(24)]
    flat.sort(reverse=True)
    top = [{"dow": DOW_NAMES[d], "hour": h, "rate": round(float(r), 2)}
           for r, d, h in flat[:3]]

    return {
        "class": cls,
        "window": f"{start:02d}:00-{(end + 1) % 24 or 24:02d}:00",
        "start_hour": start,
        "end_hour": (end + 1) % 24,
        "peak_hour": peak_hour,
        "peak_rate": round(float(profile.max()), 2),
        "weekday_mean": round(wd_mean, 3),
        "weekend_mean": round(we_mean, 3),
        "top_buckets": top,
    }


def shift_of(hour: int) -> str:
    for name, lo, hi in C.SHIFTS:
        if lo < hi and lo <= hour < hi:
            return name
        if lo > hi and (hour >= lo or hour < hi):  # wraps midnight (Night)
            return name
    return "Night"


# ----------------------------------------------------------------- routing
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def order_route(stops: list[dict]) -> dict:
    """Greedy nearest-neighbour TSP over hotspot centroids, starting at the
    highest-CIS stop. stops: [{id,lat,lon,cis,peak_hour,...}].
    Returns ordered stops + total km + a GeoJSON LineString for the map.
    """
    if not stops:
        return {"ordered": [], "total_km": 0.0, "geojson_line": None}
    remaining = sorted(stops, key=lambda s: -s["cis"])
    route = [remaining.pop(0)]
    total = 0.0
    while remaining:
        cur = route[-1]
        # objective: distance minus a CIS pull (lambda=0 => pure nearest)
        best_i, best_cost, best_d = 0, float("inf"), 0.0
        for i, s in enumerate(remaining):
            d = haversine_km(cur["lat"], cur["lon"], s["lat"], s["lon"])
            cost = d - C.ROUTE_LAMBDA * (s["cis"] / 100.0)
            if cost < best_cost:
                best_i, best_cost, best_d = i, cost, d
        total += best_d
        route.append(remaining.pop(best_i))

    ordered = []
    for seq, s in enumerate(route, 1):
        o = dict(s)
        o["order"] = seq
        ordered.append(o)
    line = {"type": "LineString", "coordinates": [[s["lon"], s["lat"]] for s in route]}
    return {"ordered": ordered, "total_km": round(total, 2), "geojson_line": line}
