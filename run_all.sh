#!/usr/bin/env bash
set -e

echo "============================================================"
echo "Starting ScreenGuard All-in-One Environment"
echo "============================================================"
echo "1. Backend API (FastAPI)     -> http://127.0.0.1:8000"
echo "2. Frontend App (Vite+React) -> http://localhost:5173"
echo "3. Demo Target (Acme Admin)  -> http://127.0.0.1:5500"
echo "============================================================"

cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT SIGINT SIGTERM

# 1. Start Demo Target App on port 5500
python3 -m http.server 5500 --directory demo_target &
DEMO_PID=$!

# 2. Start Backend API on port 8000
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 3. Start Frontend App on port 5173
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "All services running in background. Press Ctrl+C to terminate all."
wait
