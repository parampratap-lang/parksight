"""Single source of truth for the ParkSight methodology.

Every weight, threshold, and table the pipeline uses lives here and is mirrored
into meta.json so the UI can render it and judges can inspect it.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[2]          # parksight/
CSV_PATH = ROOT / "data" / "raw" / "violations.csv"
ARTIFACTS_DIR = ROOT / "backend" / "artifacts"

# ---------------------------------------------------------------- geo / grid
# Greater Bengaluru bounding box (drops GPS garbage outside the city).
GEO_BOUNDS = {"lat_min": 12.80, "lat_max": 13.29, "lon_min": 77.44, "lon_max": 77.77}
H3_RES = 9          # ~170 m edge ≈ one actionable street segment
H3_ROLLUP_RES = 8   # coarse rollup for the zoomed-out city view
MIN_VIOLATIONS = 10  # a cell qualifies as a hotspot at >= this weighted count

# ---------------------------------------------------------------- filters
# A row is a parking violation if ANY of its violation_type labels is in this set.
PARKING_TYPES = {
    "WRONG PARKING", "NO PARKING", "PARKING IN A MAIN ROAD", "PARKING ON FOOTPATH",
    "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC", "DOUBLE PARKING",
    "PARKING NEAR ROAD CROSSING", "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS",
    "PARKING OPPOSITE TO ANOTHER PARKED VEHICLE", "PARKING OTHER THAN BUS STOP",
}
# validation_status values to DROP (confirmed non-violations). Keep approved/null/created/processing.
DROP_VALIDATION = {"rejected", "duplicate"}
CONFIDENCE = {"approved": 1.0, "_default": 0.7}   # NULL/created/processing -> 0.7

# ---------------------------------------------------------------- CIS components
# (A) Road-criticality severity per parking violation type (0..1): how much the
#     obstruction removes moving-traffic capacity / disrupts a control point.
SEVERITY = {
    "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS": 1.00,
    "PARKING NEAR ROAD CROSSING": 0.95,
    "PARKING IN A MAIN ROAD": 0.90,
    "DOUBLE PARKING": 0.85,
    "PARKING OPPOSITE TO ANOTHER PARKED VEHICLE": 0.75,
    "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC": 0.70,
    "PARKING ON FOOTPATH": 0.45,
    "PARKING OTHER THAN BUS STOP": 0.40,
    "WRONG PARKING": 0.35,
    "NO PARKING": 0.30,
    "_default": 0.30,
}
# (D) Vehicle spatial footprint (0..1), PCU-inspired: bigger vehicle obstructs more.
FOOTPRINT = {
    "BUS (BMTC/KSRTC)": 1.00, "PRIVATE BUS": 1.00, "BUS": 1.00,
    "TEMPO": 0.80, "LGV": 0.80, "VAN": 0.80, "MAXI-CAB": 0.80,
    "GOODS AUTO": 0.60, "CAR": 0.55, "PASSENGER AUTO": 0.40,
    "MOTOR CYCLE": 0.20, "SCOOTER": 0.15, "MOPED": 0.15,
    "_default": 0.45,
}
# (E) Junction proximity multiplier.
JUNCTION_NAMED = 1.0
JUNCTION_NONE = 0.4
NO_JUNCTION_LABELS = {"No Junction", "NULL", "", None}

# CIS = 100 * (wS*S + wV*V + wP*P + wF*F + wJ*J)   weights sum to 1.
CIS_WEIGHTS = {"severity": 0.30, "volume": 0.25, "persistence": 0.20,
               "footprint": 0.10, "junction": 0.15}

# ---------------------------------------------------------------- routing / shifts
ROUTE_TOP_N = 60          # take top-N hotspots by CIS into patrol routing
ROUTE_LAMBDA = 0.0        # CIS pull in the greedy objective (0 = pure distance)
SHIFTS = [("Morning", 6, 12), ("Afternoon", 12, 18), ("Evening", 18, 22), ("Night", 22, 6)]

# ---------------------------------------------------------------- offenders
OFFENDER_TOP_N = 50
OFFENDER_MIN_COUNT = 5

# peak-window threshold: contiguous hours whose rate >= FRAC * class max
PEAK_FRAC = 0.6
