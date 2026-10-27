# ScreenGuard: master prompts (Antigravity + Gemini Flash)

All 11 phases, complete and in order. Paste one prompt per fresh agent conversation. Start every phase only after the previous ACCEPTANCE line passes, then update docs/BUILD_LOG.md, commit and tag.

Before Phase 0: unzip the starter files into the project folder, make the first commit, and read docs/SETUP_CHECKLIST.md.

---

## Phase 0: Scaffold

```text
You are my senior full-stack engineer. We are building ScreenGuard for a hackathon (building period Oct 27 to Nov 4). ScreenGuard is an AI supervisor agent: it watches a shared browser tab, tracks progress through a written step-by-step procedure, and decides when to warn the user about a step that is skipped, out of order, or done wrongly.

CONTEXT: The folder already contains starter files written by me: PROJECT_RULES.md, AGENTS.md, README.md, LICENSE, .gitignore, .env.example, THIRD_PARTY.md, docs/hackathon_rules.md, docs/meta_api_notes.md, docs/open_questions.md, docs/BUILD_LOG.md, docs/SETUP_CHECKLIST.md, docs/MASTER_PROMPTS.md and docs/sample_procedure.txt. Read them all first. Do NOT overwrite or shorten them; only append when a task below says so.

TASK: Create the monorepo skeleton around them. Do not call any external API yet.
1. Folders: backend (FastAPI, Python 3.11, pydantic v2, httpx, pytest, uvicorn), frontend (Vite + React + TypeScript + Vitest), demo_target (static HTML/CSS/JS), eval, scripts, config.
2. Backend: GET /api/health returns status ok and the current MODE. Settings are read from environment variables listed in .env.example. Add one pytest for the health endpoint.
3. Frontend: a page that calls /api/health and shows the result.
4. Append run instructions (backend and frontend commands) to README.md without removing existing text.
5. Append a Phase 0 entry to docs/BUILD_LOG.md.
6. Check that every variable the backend reads exists in .env.example, and add any that are missing.

ACCEPTANCE: pytest passes, frontend builds, health endpoint works, existing starter files are unchanged except for the appends, and the work is ready for a clean commit.
```

---

## Phase 1: Model adapter layer

```text
Read PROJECT_RULES.md and docs/meta_api_notes.md first.

If the notes are empty or incomplete, STOP and list exactly what you need (base URL, auth header, request and response format for each model, whether images and audio are accepted, rate limits, pricing). Do not guess.

TASK: Build the model adapter layer.
1. backend/app/model_clients/base.py: abstract ModelClient with parse_procedure(text), judge_frame(image_bytes, step, context), locate_elements(image_bytes, prompts), transcribe_audio(audio_bytes), generate_export(procedure). Define pydantic result types for each.
2. mock_client.py: deterministic fake responses. Every result carries source=mock.
3. meta_client.py: real implementation following docs/meta_api_notes.md. Add timeouts, retry with exponential backoff on 429 and 5xx, a call counter, a per-minute limiter, a per-session cap, an on-disk cache keyed by a hash of the inputs, and structured logs that never contain keys or image data.
4. Spend guard: a tracker that adds the estimated cost of every real call (prices in config/pricing.json, which you fill from the notes; if pricing is unknown use a conservative placeholder and tell me). Raise SpendLimitReached once MAX_ESTIMATED_SPEND_USD is hit and refuse further real calls.
5. A factory that picks the client from MODE. Feature flags USE_SAM and USE_VOICE; if a model is unavailable, degrade gracefully and say so in the logs.
6. OPTIONAL provider PROVIDER=baseten for the judging model, using the model name in BASETEN_MODEL (meta-models/muse-spark-open-1026) with image input, only if I receive partner credits. Keep it behind the same interface.
7. scripts/smoke_test.py: call each real model once with a tiny sample (text, image, segmentation, audio), print status, latency and estimated cost, and save redacted sample outputs to docs/sample_outputs.
8. Unit tests using mocked httpx responses (success, 429, timeout, invalid JSON, spend limit reached).

ACCEPTANCE: tests pass; the smoke test works in MODE=real and I can see one successful call per available model; the spend hard stop is verified with a tiny limit.
```

---

## Phase 2: Procedure parser and step engine

```text
Read PROJECT_RULES.md first. Use planning mode if available.

TASK: Procedure parsing and the step engine (no UI yet).
1. Pydantic models: Procedure (id, title, steps) and Step (id, order, instruction, expected_elements, success_condition, forbidden_actions, depends_on, risk low or high).
2. backend/app/prompts/parse_procedure.txt: a prompt that turns plain text into this schema as strict JSON, with at most 12 steps and short, visual success conditions (what must be visible on screen).
3. parse_procedure service: uses the model client, validates, retries once, and falls back to a deterministic parser for numbered lists so the app still works without the API.
4. Step engine (pure Python, no I/O). Per-step states: pending, active, done, wrong, skipped, uncertain. Rules: advance only on done with confidence >= 0.7 (configurable); if evidence for step k+1 appears while step k is not done, mark k skipped and emit a warning; the same warning is not repeated within 8 seconds; allow manual override; every transition produces an event with timestamp and reason.
5. REST endpoints: POST /api/procedure/parse, POST /api/session/start, GET /api/session/{id}.
6. At least 15 unit tests for the engine, covering out-of-order evidence, repeated verdicts, low confidence, override, and completion.

ACCEPTANCE: all tests pass; parsing the text in docs/sample_procedure.txt returns valid steps in mock and real modes.
```

---

## Phase 3: Demo target app

```text
Read PROJECT_RULES.md first.

TASK: Build demo_target, a small fake admin site called Acme Admin, so we can test ScreenGuard on repeatable screens. Plain HTML, CSS and vanilla JS, system fonts only, no external assets, a visible DEMO banner, fake data only.

Flow A, Customer onboarding: login, new customer form (name, email, plan), permissions checkboxes, review and submit, success page.
Flow B, Refund: find order, choose reason, enter amount; amounts over 100 require the manager approval checkbox; confirm.

Requirements:
- Every control has a stable id and clear visible text; layouts work at 1280x720.
- A dev-only hook window.__state exposes the true app state for the evaluation harness. The perception pipeline must never read it.
- Write demo_target/procedures/onboarding.txt and refund.txt (8 to 10 numbered steps each, in plain language). The onboarding procedure should match docs/sample_procedure.txt.
- Write docs/error_catalog.md defining five error types with an example for each flow: skipped step, wrong order, wrong value, wrong control, premature submit.
- Serve with python -m http.server from the demo_target folder and document the command.

ACCEPTANCE: both flows can be completed by hand; each error type can be triggered by hand; the procedures and the catalog exist.
```

---

## Phase 4: Screen capture

```text
Read PROJECT_RULES.md first.

TASK: Screen capture in the frontend, plus the frame endpoint (mock mode is fine for now).
1. ProcedurePanel: paste or upload procedure text, call /api/procedure/parse, show the steps, and offer a Start session button.
2. CaptureController: getDisplayMedia on the shared tab, draw to a canvas, downscale to max 1024 px width, encode JPEG at quality 0.7.
3. Change detection: compare 32x32 grayscale thumbnails; send a frame only when the screen changed and has been stable for 800 ms. Also provide a Check now button. Show frames seen, frames sent and frames skipped.
4. POST /api/session/{id}/frame accepts the JPEG (limit 1.5 MB) and returns a StepUpdate (mock for now).
5. Handle: permission denied, user stops sharing, tab hidden, network errors, backend offline. Show a clear message for each.
6. Privacy: frames stay in memory and are never written to disk unless I enable a debug toggle. Show a short notice before sharing starts.
7. Vitest tests for the change detection function.

ACCEPTANCE: I can share the demo_target tab, see the counters move as I use it, and see mock updates arrive; tests pass.
```

---

## Phase 5: Agent pipeline (the core)

```text
Read PROJECT_RULES.md and docs/meta_api_notes.md first. Use planning mode if available and show me the plan before coding.

TASK: The agent pipeline, the core of ScreenGuard. It must behave like an agent that observes, decides and acts, not like a one-shot image analyzer. For each accepted frame, AgentLoop.process(frame, session) does this:
1. OBSERVE: check the cache by frame hash. If USE_SAM is on, call locate_elements for the expected_elements of the current and next step; keep boxes or masks as normalized coordinates for the UI overlay.
2. VERIFY: call judge_frame (Muse Spark) with the frame, the current step, a short summary of completed steps, and the located regions. It must return strict JSON: step_id, status (done, in_progress, wrong, uncertain), observed_step_ids, evidence, warning_text, confidence from 0 to 1.
3. Write backend/app/prompts/judge_frame.txt: judge only what is visible; if unsure return uncertain; never invent screen content; keep warning_text under 20 words and actionable.
4. DECIDE: an AgentPolicy maps the verdict and the step risk to one action: ADVANCE (step done), WAIT (in progress, stay quiet), WARN (wrong or skipped), RECHECK (low confidence: one extra judge_frame call on the next stable frame), ASK_USER (uncertain on a high-risk step), STOP (wrong on a high-risk step: show a blocking banner). High-risk steps need confidence >= 0.85.
5. ACT: feed the action to the step engine and return a StepUpdate with boxes, action, reason, warning, timings, calls_used and estimated spend.
6. Decision trace: store every action with its reason, so the UI and the evaluation can show why the agent acted.
7. Budget: at most 2 model calls per checkpoint, 3 when RECHECK. On timeout or invalid output mark uncertain and continue. The spend hard stop always applies.
8. Add a switch to run with SAM on or off so we can measure whether SAM helps. If it does not help, say so honestly in the docs.
9. Write docs/architecture.md with a Mermaid diagram of the observe, verify, decide, act loop.

ACCEPTANCE: in MODE=real, a correct run through Flow A turns the steps green in order, a deliberate mistake produces a warning within about 5 seconds, and the decision trace explains each action; mock tests pass.
```

---

## Phase 6: Live interface

```text
Read PROJECT_RULES.md first.

TASK: The live interface.
1. Checklist with status chips (done, active, wrong, skipped, uncertain) that use icons and text as well as color.
2. Preview canvas that draws the located boxes over the latest frame.
3. Warning toasts with a one-line reason, plus optional spoken warnings through speechSynthesis (toggle, off by default).
4. Timeline of events and a decision trace panel (action taken and why); counters for model calls used, estimated spend and median latency.
5. Manual controls: mark step done, skip, restart, check now.
6. A Run demo button that loads the Flow A procedure.
7. Download the session as JSON and as a Markdown report, generated in the browser.
8. Loading, empty and error states; keyboard accessible; works in light and dark mode; responsive down to 1024 px width.
9. Keep the design clean and simple: one accent color, readable type, no clutter.

ACCEPTANCE: a first-time user can run the demo without instructions; no console errors; Lighthouse accessibility score of 90 or more.
```

---

## Phase 7: Evaluation harness (this wins credibility)

```text
Read PROJECT_RULES.md first. Use planning mode if available.

TASK: A reproducible evaluation harness. This produces the numbers we show the judges.
1. eval/generate_runs.py using Playwright for Python: for each flow create 10 correct runs (vary data and timing) and 10 mistake runs covering all five error types in docs/error_catalog.md. Save a screenshot after every action to eval/data/run_id/frame_0001.jpg and so on, plus labels.json with the true step status for each frame (use window.__state for ground truth only).
2. eval/run.py with options --mode real, --sam on or off, --limit N, --resume. It replays frames through the pipeline exactly as the app does.
3. Metrics: step accuracy, error detection rate, false alarms per correct run, mean detection delay in frames, median latency, model calls per run, estimated spend per run, and a breakdown by error type.
4. Outputs: eval/results/results.json, eval/results/REPORT.md with markdown tables, and a PNG chart made with matplotlib.
5. Budget guard: before running, print the planned number of model calls and the estimated spend, and ask for confirmation; never repeat finished runs.
6. Integrity: only MODE=real results may be reported; mock results are labelled and excluded. Use a fixed random seed. Save the 5 worst failures with screenshots for the README limitations section.

ACCEPTANCE: generate_runs creates the dataset; a small real run (limit 5) produces a valid REPORT.md.
```

---

## Phase 8: Voice input and export (optional)

```text
Read PROJECT_RULES.md and docs/meta_api_notes.md first. This phase is OPTIONAL; do it only if Phases 0 to 7 are finished.

TASK: Voice input and export.
1. Voice: a Speak the procedure button records audio in the browser (MediaRecorder) and sends it to POST /api/procedure/transcribe, which calls transcribe_audio (Muse Voice Transcribe) and returns text. Show the text so the user can review and edit it before parsing. Limit recordings to 60 seconds and 5 MB. If the model is unavailable, hide the button and log why.
2. Export: a Markdown checklist with each step, its final status and the evidence text, plus a Playwright automation script skeleton generated from the verified steps. Generator order: Muse Spark, else a deterministic template. Show which generator was used.
3. UI: an Export dialog with copy and download buttons.
4. Safety: never embed credentials; add a header comment saying the script must be reviewed before use; never execute generated scripts automatically.
5. Tests: transcription with mocked responses, the deterministic template path, and the output format.

ACCEPTANCE: a spoken procedure becomes editable text and then parsed steps; exporting Flow A produces a readable checklist and a script that passes a syntax check.
```

---

## Phase 9: Hardening and live product

```text
Read PROJECT_RULES.md first.

TASK: Hardening, spend safety and a live product.
1. Error handling: model timeouts, invalid JSON, 429 with backoff and a friendly UI message, backend offline, oversized frames.
2. Spend safety: test that the hard stop at MAX_ESTIMATED_SPEND_USD blocks further real calls, that the per-session and per-minute caps work, and that the UI shows the remaining budget.
3. Security: restrict CORS to localhost plus the deployed frontend origin, enforce input size limits, add a secrets scan script (search for key patterns) and run it, and remove any logging of image data.
4. Privacy: no frame persistence by default; add a settings note explaining exactly what is sent to the model.
5. Performance: show p50 and p95 latency per checkpoint in the UI; fix anything slower than 6 seconds at p95 by reducing image size or skipping redundant checks.
6. Live product on free tiers: add MODE=replay, which plays back a recorded session (frames and the real model outputs saved during the evaluation run) step by step, so visitors can watch the checklist and decision trace update without any API key. Label replay clearly in the UI. Deploy the frontend (Vercel or Netlify free tier) and the backend (Hugging Face Spaces or Render free tier) in replay mode only. Real mode runs on localhost only.
7. Run scripts: one command that starts backend, frontend and demo_target together (a shell script for macOS and Linux and a batch file for Windows).
8. A GitHub Actions workflow (free tier): backend tests, frontend tests, frontend build.
9. Clean the repo: remove dead code, unused dependencies and finished TODOs.

ACCEPTANCE: a fresh clone starts everything with one command, CI passes, the secrets scan is clean, and the public replay link works without any key.
```

---

## Phase 10: Documentation and submission pack

```text
Read PROJECT_RULES.md and docs/hackathon_rules.md first.

TASK: Documentation and submission pack.
1. README.md: one-line pitch; problem and who it helps (name the users and the cost of one mistake); solution; demo GIF placeholder; architecture diagram; a section called Built during the hackathon, generated from docs/BUILD_LOG.md, listing what was created and when; a table of Meta tools used (Muse Spark, SAM 3.1, Muse Voice Transcribe, and Muse Code or Muse Spark Open if used) with the honest role of each; quickstart in 5 commands or fewer; evaluation results copied from eval/results/REPORT.md; limitations (use the real failure list); privacy and safety; cost; an AI-assisted development disclosure; license.
2. docs/SUBMISSION_SUMMARY.md: a 200 word summary and a 25 word pitch, written against the four judging categories: Impact, Use of Meta AI Tooling, Technical Depth and Execution, Demo.
3. docs/DEMO_SCRIPT.md: a 3 minute video shot list with timings and exact on-screen actions: hook with a costly mistake, upload or speak a procedure, correct run, deliberate mistake caught by the agent, decision trace, metrics slide, Meta tools slide, close. The video must show only features built during the hackathon.
4. docs/X_POST.md: a short post draft with a demo clip description (for the Most Viral bonus prize).
5. docs/SUBMISSION_CHECKLIST.md: every requirement found in docs/hackathon_rules.md as a checkbox, including: repo is public, video link works while logged out, everyone who worked on it is listed, live product link works, credits claimed, submitted before Nov 4 at 9:00 PM ET. If hackathon_rules.md is still a placeholder, tell me and stop on this item.
6. Final audit: run all tests, run the secrets scan, verify a fresh clone works, confirm via git log that no code predates Oct 27, and list anything that violates PROJECT_RULES.md.

ACCEPTANCE: every checklist item is done or listed as open for me to fix.
```

---

## Helper prompts

When something breaks:

```text
Read PROJECT_RULES.md. Here is the problem: [paste the error or describe it]. Find the root cause before editing. Propose the smallest fix, show the diff, add a regression test, and tell me how to verify.
```

When you are behind schedule:

```text
We are behind schedule. Keep only: capture, verdict, checklist, evaluation, README. List everything else ranked by value per hour, tell me what to cut, then wait for my approval.
```

Before you submit:

```text
Act as a strict judge for the Meta Global AI Developer Hackathon. Score the project from 0 to 10 on each of these equally weighted categories: Impact, Use of Meta AI Tooling, Technical Depth and Execution, Demo. Name the three weakest points and the smallest change that fixes each, and say whether anything risks the anti-project list (simple image analyzer, basic RAG, generic chatbots).
```
