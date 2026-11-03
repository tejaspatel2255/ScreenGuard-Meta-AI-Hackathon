@echo off
echo ============================================================
echo Starting ScreenGuard All-in-One Environment
echo ============================================================
echo.
echo 1. Backend API (FastAPI)     -> http://127.0.0.1:8000
echo 2. Frontend App (Vite+React) -> http://localhost:5173
echo 3. Demo Target (Acme Admin)  -> http://127.0.0.1:5500
echo.
echo Press Ctrl+C in each opened window to stop individual servers.
echo ============================================================

:: 1. Start Demo Target App on port 5500
start "ScreenGuard - Demo Target (Port 5500)" cmd /k "python -m http.server 5500 --directory demo_target"

:: 2. Start Backend API on port 8000
start "ScreenGuard - Backend API (Port 8000)" cmd /k "uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 3. Start Frontend App on port 5173
start "ScreenGuard - Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

echo.
echo All services launched!
echo Open http://localhost:5173 to begin.
