# PROJECT_RULES.md

Every coding session must read this file first. If a chat instruction conflicts with it, stop and ask me.

## 1. Project

- Name: ScreenGuard
- One line: an AI supervisor agent that watches a shared browser tab, tracks progress through a written procedure, and warns the user when a step is skipped, out of order or done wrongly.
- Event: Meta Global AI Developer Hackathon (hosted by Meta and Cerebral Valley). Track: Indie Developer. Theme: Build for Your World.
- Building period: Oct 27 to Nov 4, 2026. Submission due Nov 4 at 9:00 PM ET.
- Target users: staff of small businesses that run legacy ERP, POS and admin tools with no API, for example billing, refunds and customer onboarding.
- ScreenGuard is an agent (observe, verify, decide, act). It is NOT a simple image analyzer, a basic RAG app or a generic chatbot. The hackathon lists those as projects to avoid.

## 2. Models and roles

| Model | Role | Required |
|---|---|---|
| Muse Spark (Meta Model API) | Parses procedures, reads screenshots, judges the current step, writes warnings | Yes |
| SAM 3.1 (Meta Model API) | Locates UI elements named in the current step | Optional, measured on versus off |
| Muse Voice Transcribe (Meta Model API) | Turns a spoken procedure into text | Optional |
| Muse Spark Open (Baseten, model meta-models/muse-spark-open-1026) | Alternative judging model | Optional, only with partner credits |
| Muse Code | Coding agent for developers, not a runtime dependency | Optional |

Never hard-code endpoints or request formats. Read docs/meta_api_notes.md. If a fact is missing, add it to docs/open_questions.md and ask me.

## 3. Stack

- Backend: Python 3.11, FastAPI, uvicorn, pydantic v2, httpx, pytest.
- Frontend: Vite, React, TypeScript, Vitest.
- Demo target app: plain HTML, CSS and vanilla JS (folder demo_target).
- Evaluation: Playwright for Python, matplotlib.
- Everything in the code must be free and open source.

## 4. Repository layout

    screenguard/
      backend/app/        main.py, api/, core/, model_clients/, prompts/
      backend/tests/
      frontend/src/
      demo_target/        index.html, procedures/
      eval/               generate_runs.py, run.py, data/, results/
      docs/
      scripts/
      config/pricing.json

## 5. Hard rules

1. Only work built from Oct 27 onward counts. Keep docs/BUILD_LOG.md with a dated entry per phase. Never copy code from my older projects (ERP-System, POS-Web-App, Chronos and others).
2. The repository is public. Never commit secrets, keys, personal data or assets I do not have rights to. Keys live in .env only. .env.example is committed, .env is not.
3. All model calls go through the adapter classes in backend/app/model_clients.
4. MODE=mock is for development only. Every metric, claim and demo result must come from MODE=real (or a replay recorded from MODE=real).
5. Cost control: send frames only when the screen changes, downscale to max 1024 px wide, cache by frame hash, cap model calls per session (MAX_CALLS_PER_SESSION) and per minute (MAX_CALLS_PER_MINUTE), estimate the cost of every call, and refuse real calls once MAX_ESTIMATED_SPEND_USD is reached. My credits are limited ($150) and a credit card is on file, so overspending costs real money.
6. Validate every model output with pydantic. On invalid output retry once, then mark the result uncertain. Never crash on a bad model response.
7. Never invent screen content. If evidence is missing, the answer is uncertain.
8. Privacy: frames stay in memory and are not written to disk unless a debug toggle is on. Tell the user what is sent to the model.
9. List every third-party library and its license in THIRD_PARTY.md.
10. Do not run destructive commands and do not touch files outside this repo. Ask before installing global tools.
11. No paid services, paid SDKs or telemetry.
12. Work only on the phase I name. Do not build later phases early.

## 6. Agent behaviour (the product)

Loop for every accepted frame: OBSERVE (cache, optional SAM) -> VERIFY (Muse Spark verdict) -> DECIDE (policy) -> ACT (update step engine, UI, log).

Actions: ADVANCE, WAIT, WARN, RECHECK, ASK_USER, STOP.

- Advance a step only when status is done and confidence >= 0.7 (high-risk steps: >= 0.85).
- If evidence for step k+1 appears while step k is not done, mark k skipped and warn.
- Do not repeat the same warning within 8 seconds.
- At most 2 model calls per checkpoint (3 with RECHECK).
- Every action is stored in a decision trace with its reason.

## 7. Data contracts

- Step: id, order, instruction, expected_elements, success_condition, forbidden_actions, depends_on, risk (low or high).
- Verdict: step_id, status (done, in_progress, wrong, uncertain), observed_step_ids, evidence, warning_text, confidence (0 to 1), source (real or mock).
- StepUpdate: session_id, step_states, action, reason, warning, boxes (normalized), timings, calls_used, estimated_spend_usd.

## 8. Coding standards

- Type hints everywhere in Python; TypeScript strict mode.
- Small functions, clear names, no dead code, comments only where the why is not obvious.
- Prompts live in backend/app/prompts as text files, not inline strings.
- Structured logs; never log keys or image data.

## 9. Testing and evidence

- Step engine: at least 15 unit tests. Adapters: mocked httpx tests. Frontend: Vitest for change detection.
- The evaluation harness (eval/) produces the numbers shown to judges: step accuracy, error detection rate, false alarms per correct run, detection delay, latency, calls and spend per run.
- Failures are shown honestly in the README.

## 10. Reporting format after every task

Files changed. How to run. How to test. What is left. Anything that conflicts with these rules.
