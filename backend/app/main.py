"""ParkSight FastAPI app: loads precomputed artifacts into memory at startup,
serves them + proxies the Groq LLM. Run: uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# load GROQ_API_KEY from parksight/.env if present
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .store import ArtifactStore
from .routers import data, assistant


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = ArtifactStore.load()
    yield


app = FastAPI(title="ParkSight API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # hackathon demo — any local origin
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(data.router)
app.include_router(assistant.router)

# In production the Docker image builds the React app to frontend/dist and
# FastAPI serves it at "/" (same origin as /api, so the frontend's relative
# fetches just work). In local dev dist is absent → expose a JSON root instead.
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="spa")
else:
    @app.get("/")
    def root():
        return {"service": "ParkSight API", "docs": "/docs",
                "endpoints": ["/api/kpis", "/api/hotspots", "/api/routes",
                              "/api/assistant", "/api/brief/{id}"]}
