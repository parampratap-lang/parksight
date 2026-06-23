# ---- stage 1: build the React frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # -> /fe/dist

# ---- stage 2: python backend that also serves the built frontend ----
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/                       # includes backend/artifacts/*.json (present in the private deploy repo)
COPY --from=frontend /fe/dist ./frontend/dist
ENV PORT=8000
EXPOSE 8000
# Render injects $PORT; bind 0.0.0.0. __file__-based paths make CWD irrelevant.
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
