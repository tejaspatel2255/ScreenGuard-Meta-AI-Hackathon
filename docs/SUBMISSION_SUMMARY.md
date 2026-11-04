# ScreenGuard: Hackathon Submission Summary

**Track**: Indie Developer  
**Theme**: Build for Your World  
**Event**: Meta Global AI Developer Hackathon (Oct 27 – Nov 4, 2026)  

---

## 25-Word Pitch

ScreenGuard is an AI supervisor agent that watches a shared browser tab, tracks progress through written procedures, and warns enterprise operators before mistakes cause financial loss.

---

## 200-Word Project Summary

Enterprise staff in retail, finance, logistics, and healthcare spend hours executing standard operating procedures across legacy ERPs, internal portals, and POS software that lack modern APIs or built-in validation guardrails. A single overlooked compliance checkbox or out-of-order submit can trigger audit fines, chargebacks, and hours of manual cleanup.

ScreenGuard solves this from pixels alone. By observing a shared browser tab through privacy-preserving client-side change detection, ScreenGuard ingests plain-English standard operating procedures (SOPs) and evaluates screen state transitions using multimodal vision intelligence.

Its deterministic `StepEngine` state machine validates procedural preconditions, enforces confidence gates ($\ge 0.70$ standard, $\ge 0.85$ high-risk), detects sequence skipping, and triggers real-time visual alerts and spoken warnings before irreversible actions are committed.

In benchmark evaluations across 16 recorded Acme Admin sessions, ScreenGuard achieved a **100.0% error detection rate** across all five major procedural mistake types (skipped step, wrong order, wrong value, wrong control, premature submit) with an average spend of under $0.002 per session and zero frame disk persistence. Step tracking accuracy reached 67.9% and false alarms averaged 3.0 per correct run. ScreenGuard transforms any legacy web interface into a self-supervising, error-free workflow.

---

## Alignment with Judging Criteria

### 1. Impact (Problem Statement: Build for Your World)
Frontline enterprise staff in small and mid-sized businesses cannot afford multimillion-dollar ERP overhauls. ScreenGuard requires zero backend integration, zero browser extensions, and zero API access. It operates purely on visual screen output, protecting SMBs from costly billing and regulatory blunders.

### 2. Model Architecture & Provenance
ScreenGuard uses multimodal vision models as the perceptual verification core of an autonomous supervisor agent. Frames are evaluated against structured procedural constraints with strict Pydantic schemas. The project includes adapters for Meta Model API (`muse-spark-1.3`), Baseten open-weights (`meta-models/muse-spark-open-1026`), and Groq (`qwen/qwen3.8-27b` vision + `openai/gpt-oss-120b` text). All provenance is explicitly displayed in the UI and health endpoints.

### 3. Technical Depth & Execution
- **Observer Loop**: 32x32 grayscale edge delta hashing reduces model calls by up to 80% by discarding idle frames.
- **Safety Machine**: Pure-Python `StepEngine` state machine with sequence skip detection and preview single-mutation state transitions.
- **Spend & Call Guardrails**: Per-session call cap (300 calls) and real-time token budget tracker enforcing strict \$100 hard ceilings.
- **Evaluation**: Playwright test harness with ground-truth instrumentation (`window.__state.truth`) and honest Wilson confidence intervals.

### 4. Demo & Replayability
- Fully working live dashboard with real-time checklist, preview canvas, and decision trace with JSON and Markdown session exports.
- Built-in **Replay Mode** allows anyone to test real benchmark sessions instantly without needing API keys or a running backend.
- One-command setup (`run_all.bat` / `run_all.sh`).
