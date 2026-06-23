"""Read-only data endpoints — thin slices over the in-memory artifact store."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api", tags=["data"])


def _store(request: Request):
    return request.app.state.store


@router.get("/health")
def health(request: Request):
    m = _store(request).data.get("meta", {})
    return {"status": "ok", "hotspots": m.get("hotspot_count", 0),
            "build_seconds": m.get("build_seconds"), "rows": m.get("row_counts", {})}


@router.get("/meta")
def meta(request: Request):
    return _store(request).data.get("meta", {})


@router.get("/kpis")
def kpis(request: Request):
    return _store(request).data.get("kpis", {})


@router.get("/hotspots")
def hotspots(request: Request, limit: int | None = None):
    hs = _store(request).hotspots
    return hs[:limit] if limit else hs


@router.get("/hotspots/{hid}")
def hotspot(request: Request, hid: str):
    h = _store(request).hotspot(hid)
    if not h:
        raise HTTPException(404, f"hotspot {hid} not found")
    return h


@router.get("/temporal/city")
def temporal_city(request: Request):
    return _store(request).data.get("city_temporal", {})


@router.get("/temporal/{hid}")
def temporal(request: Request, hid: str):
    t = _store(request).temporal(hid)
    if not t:
        raise HTTPException(404, f"temporal profile {hid} not found")
    return t


@router.get("/routes")
def routes(request: Request):
    return _store(request).data.get("routes", [])


@router.get("/stations")
def stations(request: Request):
    return _store(request).data.get("stations", [])


@router.get("/offenders")
def offenders(request: Request):
    return _store(request).data.get("repeat_offenders", [])
