"""In-memory artifact store. Loads the precomputed JSON once at startup;
every data endpoint just slices these dicts — no per-request compute."""
from __future__ import annotations
import json
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

_FILES = ["hotspots", "temporal_profiles", "city_temporal", "routes",
          "repeat_offenders", "stations", "kpis", "meta"]


class ArtifactStore:
    def __init__(self) -> None:
        self.data: dict = {}
        self.hotspot_index: dict[str, dict] = {}

    @classmethod
    def load(cls, artifacts_dir: Path | str = ARTIFACTS) -> "ArtifactStore":
        s = cls()
        d = Path(artifacts_dir)
        for name in _FILES:
            p = d / f"{name}.json"
            if p.exists():
                s.data[name] = json.loads(p.read_text())
            else:
                s.data[name] = [] if name in ("hotspots", "routes", "repeat_offenders", "stations") else {}
                print(f"[store] WARNING missing artifact {p}")
        s.hotspot_index = {h["id"]: h for h in s.data.get("hotspots", [])}
        print(f"[store] loaded {len(s.hotspot_index)} hotspots, "
              f"{len(s.data.get('routes', []))} routes, "
              f"{len(s.data.get('repeat_offenders', []))} offenders")
        return s

    # convenience accessors
    @property
    def hotspots(self) -> list[dict]:
        return self.data.get("hotspots", [])

    def hotspot(self, hid: str) -> dict | None:
        return self.hotspot_index.get(hid)

    def temporal(self, hid: str) -> dict | None:
        return self.data.get("temporal_profiles", {}).get(hid)
