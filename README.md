# 🚦 ParkSight — AI Parking-Congestion Intelligence

**Turn 298,450 real Bengaluru traffic-police violation records into a live enforcement map.**

On-street illegal parking near commercial areas, metro stations, and events chokes
carriageways and intersections. Enforcement today is reactive and patrol-based — there is
no heatmap of violations vs. congestion impact, and no way to *prioritize* which zones to
enforce. ParkSight answers: **detect illegal-parking hotspots, quantify their impact on
traffic flow, and tell officers exactly where and when to enforce.**

> Built on a real anonymized BTP dataset (Nov 2023 – Apr 2024, 298K records). No synthetic data.

---

## What it does (4 pillars)

1. **Hotspot detection + 3D heatmap** — 248K parking violations binned into H3 hexagons
   (res-9 ≈ one street segment) → an extruded map where height & colour = severity.
2. **Congestion Impact Score (CIS)** — an explainable 0–100 index per hotspot. The drawer
   shows *why* a hotspot scores what it does (stacked breakdown), so it's never a black box.
3. **Claude assistant + auto briefs** — ask in plain English ("where to send patrols at
   6pm?"); one-click per-hotspot enforcement briefings written by Claude, grounded in the data.
4. **Temporal forecast + patrol routing** — learned hour×weekday peak windows ("when to
   enforce") + greedy nearest-neighbour patrol routes per police station.

---

## Architecture

```
violations.csv (109MB)
        │  build_artifacts.py  (DuckDB + pandas, ~21s)
        ▼
backend/artifacts/*.json   ── hotspots, temporal, routes, kpis, meta …
        │  FastAPI loads into RAM at startup (zero per-request compute)
        ▼
  /api/*  ───────────────►  React + deck.gl + MapLibre  +  Claude (Opus 4.8 / Sonnet 4.6)
```

All heavy analytics are **precomputed offline**; the live app just serves JSON + proxies
two Claude calls. That's why it's fast and why the whole thing fits a 24-hour build.

---

## Quickstart

**Prereqs:** Python 3.11+, Node 18+. The 109MB CSV lives at `data/raw/violations.csv`
(symlinked to the source file).

```bash
# 1. Backend: install + build artifacts + serve
cd backend
python3 -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt
../.venv/bin/python build/build_artifacts.py          # writes artifacts/*.json (~21s)
../.venv/bin/python -m uvicorn app.main:app --port 8000 --reload

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev            # http://localhost:5173

# 3. (optional) enable the Claude assistant + briefs
export ANTHROPIC_API_KEY=sk-ant-...   # then restart uvicorn
```

Or use the helper from the repo root: `./run.sh` (builds artifacts if missing, starts both).

Without an `ANTHROPIC_API_KEY` the whole dashboard still works — only the AI assistant and
briefings show a "configure Claude" message. Everything else (map, scoring, forecast,
routing) is fully local.

---

## Methodology — the Congestion Impact Score

We have **no speed data**, so CIS is *not* a measured congestion delay — it is a
transparent, first-principles **prioritization index**. Each component ∈ [0,1]:

```
CIS = 100 · ( 0.30·Severity + 0.25·Volume + 0.20·Persistence + 0.10·Footprint + 0.15·Junction )
```

| Component | Meaning |
|---|---|
| **Severity** | per-violation road-criticality weight (parking near a traffic light/junction/main road blocks moving traffic; a footpath violation less so) |
| **Volume** | log-scaled, confidence-weighted violation count in the cell |
| **Persistence** | fraction of the 151 days the spot is active (chronic > one-off) |
| **Footprint** | mean vehicle road-space (bus/LGV ≫ scooter — PCU-inspired) |
| **Junction** | sits at a named junction (spillback amplifies impact) |

**Defending it to judges:** every weight is in `meta.json`. We also compute the hotspot
ranking under *equal* weights and report the **Spearman correlation (ρ ≈ 0.97)** — the top
zones are the same regardless of exact weights, so the prioritization is robust, not arbitrary.

### Data-quality funnel (honest, shown in KPIs)
`298,450 raw → 298,448 geofenced → 248,374 after dropping rejected/duplicate reports → 248,374 parking`.
After removing rejected reports, **100% of remaining records carry a parking violation** —
this is a dedicated parking-enforcement corpus. NULL (unadjudicated) reports are kept at
0.7 confidence weight rather than discarded.

### A real insight, not a toy
Timestamps carry a `+00` suffix but the wall-clock distribution (peaks evening→overnight,
dead midday) is the local IST enforcement pattern — market zones like **Upparpet / City
Market** peak pre-dawn, commercial strips peak evening. ParkSight's recommendation is
data-driven: **shift enforcement to evening/night windows**, not midday.

---

## 3-minute demo script

1. **Hero** — land on the 3D hex map. Drag the **time slider** to 6 PM; evening hotspots flare.
2. **Explainability** — click **#1** in the priority rail → drawer opens → CIS breakdown
   ("ranks #1 on recurrence + road-criticality, not just volume") + temporal heatmap.
3. **Claude brief** — click **Generate enforcement brief** → Opus streams a ready-to-act
   one-pager (where, when, action, routing).
4. **NL assistant** — type *"where should patrols go at 6pm?"* → grounded answer naming
   hotspots; the map highlights them.
5. **Routing** — switch to **Patrol routes** → an optimised station route timed to peaks.

---

## Repo layout

```
parksight/
├── data/raw/violations.csv          # source (symlink, git-ignored)
├── backend/
│   ├── build/                       # config.py · methodology.py · stages.py · build_artifacts.py
│   ├── artifacts/                   # generated JSON the API serves
│   └── app/                         # FastAPI: store · routers/{data,assistant} · llm · prompts
└── frontend/src/                    # React + deck.gl: MapView · HotspotDrawer · AssistantPanel …
```

Built for a hackathon. Real data → explainable scoring → Claude-powered briefings — deployable on Monday.
