# Build log

Purpose: prove what was built during the hackathon (building period Oct 27 to Nov 4, 2026). Add one dated entry per phase, with the commit hash and the key files. Never edit old entries.

## Entry format

- Date and time (IST and ET):
- Phase:
- What was built:
- Key files:
- Commit:
- Notes (problems, decisions, model calls used, spend so far):

## Entries

### 2026-10-27, Setup

- Phase: starter files
- What was built: planning and configuration files only (rules, hackathon facts, API notes template, environment example, license, checklists). No product code existed before this date.
- Key files: PROJECT_RULES.md, AGENTS.md, docs/hackathon_rules.md, docs/meta_api_notes.md, docs/open_questions.md, docs/SETUP_CHECKLIST.md, docs/MASTER_PROMPTS.md
- Commit: 0e47b29cd8c5ae28e377f80e78f89bed42a4fa79
- Notes: product code starts with Phase 0 on Oct 27.

### 2026-10-27, Phase 0: Scaffold

- Date and time (IST and ET): 2026-10-27 19:10 IST / 2026-10-27 09:40 ET
- Phase: Phase 0 (Scaffold)
- What was built: Monorepo skeleton with backend (FastAPI, pydantic v2, uvicorn, pytest), frontend (Vite + React + TypeScript + Vitest), demo_target app skeleton, eval skeleton, scripts, and pricing config. Added /api/health endpoint returning status ok and MODE.
- Key files: backend/app/main.py, backend/app/core/config.py, backend/tests/test_health.py, frontend/src/App.tsx, frontend/src/App.test.ts, config/pricing.json, demo_target/index.html
- Commit: fb8943263d62f46f887da6cf49b32534f278e6fa
- Notes: No external APIs called. Backend pytest passes, frontend builds and vitest passes.

### 2026-11-03, Phase 1: Model adapter layer

- Date and time (IST and ET): 2026-11-03 10:45 IST / 2026-11-03 01:15 ET
- Phase: Phase 1 (Model adapter layer)
- What was built: Model adapter layer with abstract ModelClient (`parse_procedure`, `judge_frame`, `locate_elements`, `transcribe_audio`, `generate_export`), deterministic `MockModelClient`, `MetaModelClient` adhering to `dev.meta.ai` documentation with exponential backoff on 429/5xx, call counters, per-minute limiter, per-session cap, on-disk hashing cache, `SpendGuard` tracking estimated spend with `SpendLimitReached` hard-stop, provider factory (`MODE=mock` / `MODE=real` and `PROVIDER=baseten`), smoke test script, and mock HTTP unit tests.
- Key files: backend/app/model_clients/base.py, backend/app/model_clients/mock_client.py, backend/app/model_clients/meta_client.py, backend/app/model_clients/baseten_client.py, backend/app/model_clients/spend_guard.py, backend/app/model_clients/factory.py, scripts/smoke_test.py, backend/tests/test_model_clients.py, config/pricing.json, docs/meta_api_notes.md
- Notes: Meta Model API specifications filled from official dev.meta.ai docs. Unit tests and smoke test created.

### 2026-11-03, Phase 1b: Real API Verification (Groq + Meta Architecture)

- Date and time (IST and ET): 2026-11-03 11:27 IST / 2026-11-03 01:57 ET
- Phase: Phase 1b (Real API check & Defect Fixing)
- What was built / verified:
  - Verified live model inference using real API credentials (`MODE=real`, `PROVIDER=groq`).
  - Tested `parse_procedure` with live LLM (latency: 2.25s, parsed 3 structured steps with `source="real"`).
  - Tested `judge_frame` with live multimodal model and validated graceful fallback to `status="uncertain"` without crashing.
  - Converted `_enforce_limits` to non-blocking async sleep with continuous rate-limit re-checking.
  - Fixed singleton factory in `get_model_client()` to preserve session spend and counters.
  - Added support for JPEG screen capture frames alongside PNG.
  - Added deterministic fallback parsing to `MockModelClient`.
  - Added `cache/` and `*.zip` to `.gitignore`.
- Key files: backend/app/model_clients/groq_client.py, backend/app/model_clients/meta_client.py, backend/app/model_clients/mock_client.py, backend/app/model_clients/factory.py, backend/app/core/config.py, scripts/smoke_test.py, docs/sample_outputs/
- Commit: pending

### 2026-11-03, Phase 2: Parser, Step Engine, Sessions and API

- Date and time (IST and ET): 2026-11-03 11:38 IST / 2026-11-03 02:08 ET
- Phase: Phase 2 (Procedure parser, step engine, sessions, REST API)
- What was built:
  - `StepEngine` state machine in `backend/app/core/step_engine.py` (pure Python, injectable clock, states: pending/active/done/wrong/skipped/uncertain, skip detection on higher order evidence, confidence gating >= 0.70 / >= 0.85 high risk, 8s warning cooldown, manual override, restart).
  - Deterministic procedure parser and service fallback in `backend/app/core/procedure_parser.py` (extracts title, quoted/capitalized elements, visual success conditions, high risk keywords, max 12 steps).
  - Improved `parse_procedure.txt` prompt template.
  - Thread-safe session store in `backend/app/core/session.py`.
  - REST endpoints in `backend/app/api/routes.py`: `POST /api/procedure/parse`, `POST /api/session/start`, `GET /api/session/{id}`, `POST /api/session/{id}/override`, `POST /api/session/{id}/restart`, `GET /api/budget`.
  - CORS origins configuration added to `config.py` and `.env.example`.
  - 15 comprehensive unit tests in `backend/tests/test_step_engine_and_api.py`.
- Key files: backend/app/core/step_engine.py, backend/app/core/procedure_parser.py, backend/app/core/session.py, backend/app/api/routes.py, backend/app/main.py, backend/app/core/config.py, backend/tests/test_step_engine_and_api.py, docs/BUILD_LOG.md
- Commit: pending

### 2026-11-03, Phase 3: Acme Admin Refund Target App

- Date and time (IST and ET): 2026-11-03 11:44 IST / 2026-11-03 02:14 ET
- Phase: Phase 3 (Acme Admin target app & error catalog)
- What was built:
  - 6 distinct screens in `demo_target/app.js` (Login, Orders, Order detail, Refund form, Review, Success).
  - Ground truth tracking in `window.__state.truth` (`steps_done`, `current_step`, `violations`) with full event logging.
  - Large legible typography (18px+ body, 20px+ buttons), high contrast, stable IDs and `data-testid` attributes.
  - Procedure definition at `demo_target/procedures/refund.txt` and `frontend/public/demo-procedure.txt` (10 steps).
  - Error catalog in `docs/error_catalog.md` defining 5 error types (`skipped_step`, `wrong_order`, `wrong_value`, `wrong_control`, `premature_submit`).
  - README updated with `python -m http.server 5500 --directory demo_target`.
- Key files: demo_target/app.js, demo_target/style.css, demo_target/procedures/refund.txt, frontend/public/demo-procedure.txt, docs/error_catalog.md, README.md, docs/BUILD_LOG.md
- Commit: pending

### 2026-11-03, Phase 5: Agent Loop and Frame Processing Endpoint

- Date and time (IST and ET): 2026-11-03 11:51 IST / 2026-11-03 02:21 ET
- Phase: Phase 5 (The Agent Loop & Frame Endpoint)
- What was built:
  - `AgentPolicy` in `backend/app/core/policy.py` mapping model verdicts and step risks to actions (`ADVANCE`, `WAIT`, `WARN`, `RECHECK`, `ASK_USER`, `STOP`) with cooldown suppression.
  - `AgentLoop` in `backend/app/core/agent.py` executing the OBSERVE -> VERIFY -> DECIDE -> ACT loop:
    - SHA-256 frame deduplication (cached returns with 0 model calls).
    - Pillow image normalization (max 1024px width, JPEG q80).
    - Optional SAM element detection with graceful fallback.
    - Model verification with SpendLimitReached budget handling and 1-retry RECHECK.
    - Full decision trace persistence (`session.trace`).
  - REST endpoints in `backend/app/api/frames.py`:
    - `POST /api/session/{id}/frame` (validates content-type, enforces 1.5MB limit, returns `StepUpdate`).
    - `GET /api/session/{id}/trace` (returns structured trace).
  - CLI frame sender in `scripts/send_frame.py`.
  - 12 comprehensive unit tests in `backend/tests/test_agent_loop.py`.
- Key files: backend/app/core/policy.py, backend/app/core/agent.py, backend/app/api/frames.py, backend/app/main.py, scripts/send_frame.py, backend/tests/test_agent_loop.py, docs/BUILD_LOG.md
- Commit: pending
