"""System-prompt builders + grounding-context injection for Claude.

The model only ever sees the precomputed artifacts (compact JSON), never raw
rows — so it quotes our numbers instead of inventing them.
"""
from __future__ import annotations
import json

from .store import ArtifactStore


def _compact_hotspot(h: dict) -> dict:
    pw = h.get("peak_window", {})
    return {
        "id": h["id"], "rank": h["rank"], "name": h["name"], "cis": h["cis"],
        "police_station": h["police_station"],
        "junction": h.get("nearest_junction", {}).get("name"),
        "dominant_violation": h.get("dominant_violation"),
        "peak": f'{pw.get("class","")} {pw.get("window","")}'.strip(),
        "total_violations": h.get("total_violations"),
    }


def build_assistant_context(store: ArtifactStore, query: str) -> tuple[str, list[str]]:
    """Return (json_context_str, candidate_hotspot_ids) for the NL assistant.

    Pre-filters hotspots whose name/station/junction is mentioned in the query so
    location-specific questions get grounded, accurate context.
    """
    q = (query or "").lower()
    hotspots = store.hotspots
    matched = [h for h in hotspots
               if any(tok and tok.lower() in q for tok in
                      [h.get("name", ""), h.get("police_station", ""),
                       (h.get("nearest_junction") or {}).get("name", "")])]
    # always include the global top 15, then any location matches, cap 25
    top = hotspots[:15]
    seen, chosen = set(), []
    for h in matched + top:
        if h["id"] not in seen:
            seen.add(h["id"]); chosen.append(h)
        if len(chosen) >= 25:
            break
    ctx = {
        "kpis": store.data.get("kpis", {}),
        "hotspots": [_compact_hotspot(h) for h in chosen],
        "routes": [{"police_station": r["police_station"], "n_stops": r["n_stops"],
                    "total_km": r["total_km"]} for r in store.data.get("routes", [])[:10]],
    }
    return json.dumps(ctx, separators=(",", ":")), [h["id"] for h in matched[:8]]


ASSISTANT_SYSTEM = (
    "You are ParkSight's enforcement analyst for the Bengaluru Traffic Police. "
    "You answer questions about illegal-parking congestion hotspots using ONLY the JSON "
    "data provided below, which is precomputed from 298,450 real violation records "
    "(Nov 2023-Apr 2024).\n"
    "RULES: (1) Ground every claim in the provided data — cite hotspot names, CIS scores, "
    "and time windows. (2) If the data does not contain the answer, say so plainly — never "
    "invent hotspots, scores, streets, or statistics. (3) When asked where to deploy patrols, "
    "rank by Congestion Impact Score (CIS) and respect the peak time windows. (4) Be concise "
    "and operational — this is for officers planning shifts. (5) Output a short direct answer, "
    "then 2-4 bullet recommendations referencing specific hotspots. Output only the answer, no preamble.\n\n"
    "```json\n{context}\n```"
)


BRIEF_SYSTEM = (
    "You are writing a one-page enforcement briefing for a Bengaluru Traffic Police station "
    "officer about a single illegal-parking hotspot. Use ONLY the provided data; do not invent "
    "specifics. Produce GitHub-flavored Markdown with these sections: "
    "**Hotspot Summary** (location, CIS and what drives it), **When to Enforce** (specific "
    "day/hour windows from the temporal data, with the reasoning), **Recommended Action** "
    "(patrol/towing/signage given the violation + vehicle mix), **Patrol Routing Note** (its "
    "place in the station's route). Keep it tight, factual, directly actionable. End with a "
    "one-line **Priority Verdict**. Output only the briefing markdown — no preamble, no meta-commentary."
)


def build_brief_user(store: ArtifactStore, hid: str) -> str | None:
    h = store.hotspot(hid)
    if not h:
        return None
    t = store.temporal(hid) or {}
    route_pos = None
    for r in store.data.get("routes", []):
        for stop in r.get("stops", []):
            if stop["id"] == hid:
                route_pos = {"police_station": r["police_station"], "order": stop["order"],
                             "of_stops": r["n_stops"], "route_km": r["total_km"]}
    ctx = {
        "hotspot": h,
        "temporal_peak": t.get("peak"),
        "route_position": route_pos,
    }
    return ("Generate the enforcement briefing for this hotspot.\n\n```json\n"
            + json.dumps(ctx, separators=(",", ":")) + "\n```")
