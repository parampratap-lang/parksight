#!/usr/bin/env bash
# ParkSight one-command dev launcher: builds artifacts if missing, starts backend + frontend.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv"
if [ ! -d "$VENV" ]; then
  echo "→ creating venv + installing backend deps"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r backend/requirements.txt
fi

if [ ! -f "backend/artifacts/hotspots.json" ]; then
  echo "→ building artifacts from the CSV (~20s)"
  "$VENV/bin/python" backend/build/build_artifacts.py
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "→ installing frontend deps"
  (cd frontend && npm install)
fi

echo "→ starting backend (:8000) and frontend (:5173)"
"$VENV/bin/python" -m uvicorn app.main:app --app-dir backend --port 8000 &
BACK=$!
(cd frontend && npm run dev) &
FRONT=$!
trap "kill $BACK $FRONT 2>/dev/null" EXIT
echo "   backend  → http://localhost:8000/docs"
echo "   frontend → http://localhost:5173"
echo "   (set ANTHROPIC_API_KEY before running to enable the Claude assistant + briefs)"
wait
