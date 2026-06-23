"""Offline build: 109MB CSV -> backend/artifacts/*.json  (idempotent).

    python build_artifacts.py            # full dataset
    python build_artifacts.py --sample 40000   # fast dev subset
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import sibling modules
import config as C
import stages as S


def _write(name: str, obj) -> None:
    path = C.ARTIFACTS_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"), default=str)
    print(f"  wrote {name:28s} ({path.stat().st_size/1024:8.1f} KB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None, help="row LIMIT for fast dev")
    args = ap.parse_args()

    t0 = time.time()
    print(f"[1/8] loading + cleaning  (sample={args.sample or 'full'}) ...")
    df, funnel, _ = S.load_clean(args.sample)
    dates = pd.to_datetime(df["date"].dropna())
    obs_days = (dates.max() - dates.min()).days + 1
    dow_counts = np.array([
        sum(1 for d in pd.date_range(dates.min(), dates.max()) if d.weekday() == k)
        for k in range(7)
    ], dtype=float)
    dow_counts[dow_counts == 0] = 1
    print(f"      funnel={funnel}  obs_days={obs_days}")

    print("[2/8] hotspots + CIS ...")
    hotspots, _ = S.build_hotspots(df, obs_days)
    print(f"      {len(hotspots)} hotspots (>= {C.MIN_VIOLATIONS} weighted violations)")

    print("[3/8] temporal profiles ...")
    profiles, city = S.build_temporal(df, hotspots, dow_counts)

    print("[4/8] patrol routes ...")
    routes = S.build_routes(hotspots)

    print("[5/8] repeat offenders ...")
    offenders = S.build_offenders(df)

    print("[6/8] station rollups ...")
    stations = S.build_stations(hotspots, df)

    print("[7/8] kpis ...")
    kpis = S.build_kpis(df, funnel, hotspots, offenders, city)

    print("[8/8] meta ...")
    meta = S.build_meta(funnel, hotspots, obs_days)
    meta["build_seconds"] = round(time.time() - t0, 1)

    print("writing artifacts ->", C.ARTIFACTS_DIR)
    _write("hotspots.json", hotspots)
    _write("temporal_profiles.json", profiles)
    _write("city_temporal.json", city)
    _write("routes.json", routes)
    _write("repeat_offenders.json", offenders)
    _write("stations.json", stations)
    _write("kpis.json", kpis)
    _write("meta.json", meta)

    print(f"\nDONE in {time.time()-t0:.1f}s  | "
          f"top hotspot: {hotspots[0]['name']} (CIS {hotspots[0]['cis']}) "
          f"| robustness rho={meta['robustness_spearman']}")


if __name__ == "__main__":
    main()
