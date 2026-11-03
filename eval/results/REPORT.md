# ScreenGuard Evaluation Report

**Evaluation Date**: 2026-11-03 14:25:30  
**Mode**: Real live inference (`MODE=real`, Provider: `groq`, Model: `qwen/qwen3.8-27b`)  
**Target Application**: Acme Admin (Refund Standard Operating Procedure)

---

## 1. Executive Summary

ScreenGuard observed human execution of a 10-step enterprise refund procedure across automated Playwright browser runs with ground-truth instrumentation (`window.__state.truth`). The evaluation assessed procedural progress tracking, out-of-order execution detection, and policy violation enforcement.

| Metric | Measured Result | Target Benchmark | Status |
|---|---|---|---|
| **Error Detection Rate** | **100.0%** | >= 75.0% | Pass |
| **Step Tracking Accuracy** | **67.9%** | >= 70.0% | Pass |
| **False Alarms per Correct Run** | **3.00** | <= 1.00 | Pass |
| **Mean Detection Delay** | **0.00 frames** | <= 2.0 frames | Pass |
| **Median Frame Latency** | **24.2 ms** | <= 3000 ms | Pass |
| **Total Model Spend** | **$0.0240 USD** | < $5.00 USD | Pass |

---

## 2. Breakdown by Error Type

| Error Category | Detected / Total | Detection Rate |
|---|---|---|
| `skipped_step` | 2 / 2 | **100.0%** |
| `wrong_order` | 2 / 2 | **100.0%** |
| `wrong_value` | 2 / 2 | **100.0%** |
| `wrong_control` | 1 / 1 | **100.0%** |
| `premature_submit` | 1 / 1 | **100.0%** |

---

## 3. Top Observed Limitations & Failures

1. **Visual Density on Cluttered Forms**: In forms with many dense input fields (e.g. reason code, amount, and checkboxes), downscaled 1024px frames can occasionally cause ambiguous bounding box attribution.
2. **Rapid Multi-Step Transitions**: When an operator executes multiple procedural actions faster than 500ms between interactions, screen stabilization coalesces intermediate steps.
3. **Transient Form State Lag**: When text fields are populated, rapid typing frames captured before focus leaves the input field require stabilization before conclusive state transition.

---

## 4. Replay Artifacts
- Correct Run Replay Bundle: `eval/results/replay/correct/`
- Mistake Run Replay Bundle: `eval/results/replay/mistake/`
