# ScreenGuard

An AI supervisor agent for software workflows. It watches a shared browser tab, tracks progress through a written procedure, and warns you before a skipped, out-of-order or wrong step becomes a costly mistake. It works from pixels alone, so it suits legacy ERP and POS tools that have no API.

Built for the Meta Global AI Developer Hackathon (Indie track, theme: Build for Your World).

Status: in development. This README is completed in Phase 10.

## Built during the hackathon

All product code in this repository was written between Oct 27 and Nov 4, 2026. See docs/BUILD_LOG.md for dated entries.

## Meta tools used

To be filled in Phase 10 (Muse Spark, SAM 3.1, Muse Voice Transcribe, and others if used).

## License

MIT. See LICENSE.

## How to run locally

### Prerequisites
- Python 3.11+
- Node.js 20+

### Backend setup and run
```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Run backend tests
python -m pytest

# Start the FastAPI server (runs on http://127.0.0.1:8000)
python -m uvicorn backend.app.main:app --reload --port 8000
```

### Frontend setup and run
```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Run frontend tests
npm test

# Start the development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build
```
