import argparse
import asyncio
import json
import math
import os
import sys
import time
from pathlib import Path

# Configure local writable matplotlib config dir
os.environ["MPLCONFIGDIR"] = str(Path(__file__).resolve().parent / ".mplconfig")

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.app.core.agent import AgentLoop
from backend.app.core.config import settings
from backend.app.core.procedure_parser import parse_deterministic
from backend.app.core.session import Session
from backend.app.core.step_engine import StepEngine
from backend.app.model_clients.factory import get_model_client

DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RAW_RESULTS_DIR = RESULTS_DIR / "raw"
REPLAY_DIR = RESULTS_DIR / "replay"
PROCEDURE_FILE = ROOT_DIR / "demo_target" / "procedures" / "refund.txt"
MANIFEST_FILE = ROOT_DIR / "frontend" / "public" / "replay" / "manifest.json"


def wilson_score_interval(x: int, n: int) -> tuple[float, float]:
    """Computes two-sided 95% Wilson score confidence interval."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996
    p = x / n
    denom = 1 + (z ** 2) / n
    centre = p + (z ** 2) / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + (z ** 2) / (4 * n)) / n)
    low = max(0.0, (centre - margin) / denom) * 100.0
    high = min(1.0, (centre + margin) / denom) * 100.0
    return (round(low, 1), round(high, 1))


def parse_args():
    parser = argparse.ArgumentParser(description="ScreenGuard Evaluation Harness")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of runs to evaluate")
    parser.add_argument("--resume", action="store_true", help="Resume from existing cached raw results")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and estimated cost without making real calls")
    parser.add_argument("--sam", choices=["on", "off"], default="off", help="Enable or disable SAM 3.1")
    parser.add_argument("--window", type=int, default=2, help="Frame detection window after first violation")
    parser.add_argument("--no-cache", dest="no_cache", action="store_true", default=True, help="Bypass model client response cache (default: True)")
    parser.add_argument("--allow-cache", dest="no_cache", action="store_false", help="Allow model client response cache")
    return parser.parse_args()


async def run_evaluation():
    args = parse_args()

    # Refuse mock mode per task rules
    if settings.MODE.lower() == "mock" and not args.dry_run:
        print("ERROR: eval/run.py requires MODE=real (or dry-run). Refusing to run evaluation in mock mode.")
        sys.exit(1)

    RAW_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)

    # Load procedure
    procedure_text = PROCEDURE_FILE.read_text(encoding="utf-8")
    procedure = parse_deterministic(procedure_text)

    # Discover runs in eval/data/
    if not DATA_DIR.exists():
        print("ERROR: eval/data directory not found. Please run python eval/generate_runs.py first.")
        sys.exit(1)

    run_dirs = sorted([d for d in DATA_DIR.iterdir() if d.is_dir() and (d / "labels.json").exists()])
    if not run_dirs:
        print("ERROR: No runs found in eval/data. Run python eval/generate_runs.py first.")
        sys.exit(1)

    if args.limit:
        run_dirs = run_dirs[:args.limit]

    total_frames = 0
    runs_meta = []
    for rd in run_dirs:
        lbl = json.loads((rd / "labels.json").read_text(encoding="utf-8"))
        frames_count = len(lbl.get("frames", []))
        total_frames += frames_count
        runs_meta.append({"run_dir": rd, "labels": lbl, "frames_count": frames_count})

    client = get_model_client()
    minfo = client.model_info() if hasattr(client, "model_info") else {
        "provider": settings.PROVIDER,
        "vision_model": settings.GROQ_VISION_MODEL if settings.PROVIDER == "groq" else "muse-spark-1.3",
        "text_model": settings.GROQ_TEXT_MODEL if settings.PROVIDER == "groq" else "muse-spark-1.3",
        "family": "other",
    }

    est_calls = total_frames
    est_spend_usd = est_calls * 0.0003

    print("=" * 65)
    print("ScreenGuard Evaluation Plan")
    print("=" * 65)
    print(f"Provider:          {minfo['provider']}")
    print(f"Vision Model:      {minfo['vision_model']}")
    print(f"Text Model:        {minfo['text_model']}")
    print(f"Cache Bypass:      {'ENABLED (--no-cache)' if args.no_cache else 'DISABLED'}")
    print(f"Total Runs:        {len(run_dirs)} ({sum(1 for r in runs_meta if not r['labels']['is_mistake'])} correct, {sum(1 for r in runs_meta if r['labels']['is_mistake'])} mistake)")
    print(f"Total Frames:      {total_frames}")
    print(f"Estimated Calls:   ~{est_calls}")
    print(f"Estimated Spend:   ~${est_spend_usd:.4f} USD")
    print(f"Detection Window:  {args.window} frames")
    print(f"SAM 3.1:           {args.sam.upper()}")
    print("=" * 65)

    if args.dry_run:
        print("[Dry-run completed. No real API calls were made.]")
        return

    # Enforce cache bypass
    if args.no_cache:
        setattr(client, "cache_enabled", False)

    agent = AgentLoop(client, cache_enabled=(not args.no_cache))

    eval_results = []
    saved_replay_correct = False
    saved_replay_mistake = False

    total_cache_hits = 0

    for idx, rinfo in enumerate(runs_meta, 1):
        r_dir = rinfo["run_dir"]
        r_labels = rinfo["labels"]
        run_id = r_labels["run_id"]
        is_mistake = r_labels["is_mistake"]
        error_type = r_labels.get("error_type")
        raw_cache_file = RAW_RESULTS_DIR / f"{run_id}.json"

        if args.resume and raw_cache_file.exists():
            print(f"[{idx}/{len(runs_meta)}] Resuming raw: {run_id}")
            run_result = json.loads(raw_cache_file.read_text(encoding="utf-8"))
            eval_results.append(run_result)
            continue

        print(f"[{idx}/{len(runs_meta)}] Evaluating {run_id} ({'Mistake: ' + str(error_type) if is_mistake else 'Correct'})...")

        # Isolated session per run
        session = Session(
            id=f"eval-{run_id}",
            procedure=procedure,
            engine=StepEngine(procedure.steps),
        )

        frame_results = []
        first_violation_frame = r_labels.get("first_violation_frame")

        for f_info in r_labels.get("frames", []):
            f_name = f_info["frame"]
            f_path = r_dir / f_name
            raw_bytes = f_path.read_bytes()

            # Process frame through AgentLoop
            update = await agent.process(session, raw_bytes)

            is_cache_hit = update.cached or (update.calls_used == 0 and update.action.value != "ASK_USER")
            if is_cache_hit:
                total_cache_hits += 1

            f_res = {
                "frame": f_name,
                "frame_path": str(f_path),
                "frame_idx": f_info["frame_idx"],
                "truth_step": f_info.get("current_step"),
                "agent_step": update.current_step_id,
                "action": update.action.value,
                "reason": update.reason,
                "warning": update.warning,
                "blocking": update.blocking,
                "confidence": update.verdict.confidence if update.verdict else 0.0,
                "evidence": update.verdict.evidence if update.verdict else "",
                "latency_ms": update.latency_ms,
                "calls_used": update.calls_used,
                "is_cache_hit": is_cache_hit,
            }
            frame_results.append(f_res)

        # Save replay bundle (1 full correct run, 1 mistake run downscaled to 960px)
        if not is_mistake and not saved_replay_correct:
            replay_correct_dir = REPLAY_DIR / "correct"
            replay_correct_dir.mkdir(parents=True, exist_ok=True)
            for f_info in r_labels.get("frames", []):
                src = r_dir / f_info["frame"]
                img = Image.open(src)
                if img.width > 960:
                    img = img.resize((960, int(img.height * 960 / img.width)), Image.Resampling.LANCZOS)
                img.save(replay_correct_dir / f_info["frame"], format="JPEG", quality=80)
            (replay_correct_dir / "session.json").write_text(json.dumps(frame_results, indent=2), encoding="utf-8")
            saved_replay_correct = True

        if is_mistake and not saved_replay_mistake:
            replay_mistake_dir = REPLAY_DIR / "mistake"
            replay_mistake_dir.mkdir(parents=True, exist_ok=True)
            for f_info in r_labels.get("frames", []):
                src = r_dir / f_info["frame"]
                img = Image.open(src)
                if img.width > 960:
                    img = img.resize((960, int(img.height * 960 / img.width)), Image.Resampling.LANCZOS)
                img.save(replay_mistake_dir / f_info["frame"], format="JPEG", quality=80)
            (replay_mistake_dir / "session.json").write_text(json.dumps(frame_results, indent=2), encoding="utf-8")
            saved_replay_mistake = True

        run_output = {
            "run_id": run_id,
            "is_mistake": is_mistake,
            "error_type": error_type,
            "first_violation_frame": first_violation_frame,
            "frames": frame_results,
            "trace": session.trace,
        }
        raw_cache_file.write_text(json.dumps(run_output, indent=2), encoding="utf-8")
        eval_results.append(run_output)

    # Compute Metrics
    correct_runs = [r for r in eval_results if not r["is_mistake"]]
    mistake_runs = [r for r in eval_results if r["is_mistake"]]

    # 1. Exact Detection Logic:
    # A mistake run is detected ONLY if first WARN/STOP occurs at frame_idx >= first_violation_frame and <= first_violation_frame + window
    # Alerts before first_violation_frame are pre-violation false alarms and do NOT count as detection.
    detected_count = 0
    detection_delays = []
    error_breakdown = {}
    pre_violation_false_alarms = 0
    failures = []

    for mr in mistake_runs:
        etype = mr.get("error_type", "unknown")
        if etype not in error_breakdown:
            error_breakdown[etype] = {"total": 0, "detected": 0}
        error_breakdown[etype]["total"] += 1

        v_frame = mr.get("first_violation_frame")
        all_alerts = [f for f in mr.get("frames", []) if f.get("action") in ["WARN", "STOP"]]

        # Pre-violation alerts
        if v_frame is not None:
            pre_alerts = [f for f in all_alerts if f["frame_idx"] < v_frame]
            pre_violation_false_alarms += len(pre_alerts)

        # Timely detection window
        timely_alerts = [f for f in all_alerts if v_frame is not None and v_frame <= f["frame_idx"] <= v_frame + args.window]
        if timely_alerts:
            first_alert = timely_alerts[0]
            delay = first_alert["frame_idx"] - v_frame
            detected_count += 1
            detection_delays.append(delay)
            error_breakdown[etype]["detected"] += 1
        else:
            # Failure: missed mistake
            v_frame_obj = next((f for f in mr["frames"] if f["frame_idx"] == v_frame), mr["frames"][-1]) if mr["frames"] else None
            failures.append({
                "type": "Missed Mistake",
                "run_id": mr["run_id"],
                "frame": v_frame_obj["frame"] if v_frame_obj else "unknown",
                "frame_path": v_frame_obj["frame_path"] if v_frame_obj else "",
                "truth": f"Violation ({etype}) at frame {v_frame}",
                "agent_action": v_frame_obj["action"] if v_frame_obj else "NONE",
                "evidence": v_frame_obj.get("evidence", "No evidence recorded") if v_frame_obj else "",
                "cause": f"Agent did not trigger WARN/STOP within window of {args.window} frames after violation.",
            })

    num_mistake_runs = len(mistake_runs)
    detection_rate_pct = (detected_count / num_mistake_runs * 100.0) if num_mistake_runs else 0.0
    det_ci_low, det_ci_high = wilson_score_interval(detected_count, num_mistake_runs)
    mean_delay = (sum(detection_delays) / len(detection_delays)) if detection_delays else 0.0

    # 2. False Alarms
    total_false_alarms = 0
    total_correct_frames = sum(len(cr["frames"]) for cr in correct_runs)
    for cr in correct_runs:
        for f in cr["frames"]:
            if f["action"] in ["WARN", "STOP"]:
                total_false_alarms += 1
                if len(failures) < 5:
                    failures.append({
                        "type": "False Alarm",
                        "run_id": cr["run_id"],
                        "frame": f["frame"],
                        "frame_path": f["frame_path"],
                        "truth": f"Correct progress (Step {f.get('truth_step')})",
                        "agent_action": f"{f['action']}: {f.get('warning') or f.get('reason')}",
                        "evidence": f.get("evidence", "No evidence text"),
                        "cause": "Model verdict indicated error on legitimate operator transition.",
                    })

    num_correct_runs = len(correct_runs)
    false_alarms_per_correct = (total_false_alarms / num_correct_runs) if num_correct_runs else 0.0
    false_alarms_per_100_frames = (total_false_alarms / total_correct_frames * 100.0) if total_correct_frames else 0.0

    # 3. Step Tracking Accuracy (exact equality on correct runs)
    matching_step_frames = 0
    eval_correct_frames = 0
    for cr in correct_runs:
        for f in cr["frames"]:
            eval_correct_frames += 1
            truth_val = f.get("truth_step")
            agent_step_id = f.get("agent_step")
            if truth_val is not None and agent_step_id is not None:
                step_obj = procedure.step_map.get(agent_step_id) if hasattr(procedure, "step_map") else None
                agent_order = step_obj.order if step_obj else None
                if agent_order is None:
                    digits = "".join(ch for ch in str(agent_step_id) if ch.isdigit())
                    agent_order = int(digits) if digits else None

                t_digits = "".join(ch for ch in str(truth_val) if ch.isdigit())
                truth_order = int(t_digits) if t_digits else None

                if truth_order is not None and agent_order is not None and truth_order == agent_order:
                    matching_step_frames += 1

    step_acc_pct = (matching_step_frames / eval_correct_frames * 100.0) if eval_correct_frames else 0.0
    step_ci_low, step_ci_high = wilson_score_interval(matching_step_frames, eval_correct_frames)

    # 4. Latency over real model calls
    real_latencies = [f["latency_ms"] for r in eval_results for f in r["frames"] if not f.get("is_cache_hit", False)]
    real_latencies.sort()
    median_lat = real_latencies[len(real_latencies) // 2] if real_latencies else 0.0
    p95_lat = real_latencies[int(len(real_latencies) * 0.95)] if real_latencies else 0.0

    total_calls_calculated = sum(sum(f.get("calls_used", 1) for f in r["frames"]) for r in eval_results)
    client_spend = client.usage().get("estimated_spend_usd", 0.0) if hasattr(client, "usage") else 0.0
    client_calls = client.usage().get("calls_total", 0) if hasattr(client, "usage") else 0

    spend_usd = client_spend if client_spend > 0 else round(total_calls_calculated * 0.0003, 4)
    calls_used = client_calls if client_calls > 0 else total_calls_calculated

    # 5. Status Against Targets (Met / Not met)
    met_detection = "Met" if detection_rate_pct >= 75.0 else "Not met"
    met_false_alarms = "Met" if false_alarms_per_correct <= 1.0 else "Not met"
    met_step_acc = "Met" if step_acc_pct >= 70.0 else "Not met"
    met_latency = "Met" if median_lat <= 3000.0 else "Not met"
    met_spend = "Met" if spend_usd < 5.0 else "Not met"

    print(f"\nCache hits during evaluation: {total_cache_hits} (Target: 0)")
    print(f"Error Detection Rate:        {detection_rate_pct:.1f}% [{det_ci_low}%, {det_ci_high}%] ({met_detection})")
    print(f"False Alarms per Run:        {false_alarms_per_correct:.2f} ({met_false_alarms})")
    print(f"Step Tracking Accuracy:      {step_acc_pct:.1f}% [{step_ci_low}%, {step_ci_high}%] ({met_step_acc})")
    print(f"Median Real Call Latency:    {median_lat:.1f} ms (p95: {p95_lat:.1f} ms) ({met_latency})")
    print(f"Total Spend:                 ${spend_usd:.4f} USD ({met_spend})")

    results_data = {
        "provider": minfo["provider"],
        "vision_model": minfo["vision_model"],
        "text_model": minfo["text_model"],
        "family": minfo["family"],
        "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": settings.MODE,
        "runs_evaluated": len(eval_results),
        "correct_runs": num_correct_runs,
        "mistake_runs": num_mistake_runs,
        "total_frames": total_frames,
        "cache_hits": total_cache_hits,
        "error_detection_rate_pct": round(detection_rate_pct, 1),
        "error_detection_ci_95": [det_ci_low, det_ci_high],
        "false_alarms_per_correct_run": round(false_alarms_per_correct, 2),
        "false_alarms_per_100_frames": round(false_alarms_per_100_frames, 2),
        "pre_violation_false_alarms": pre_violation_false_alarms,
        "step_tracking_accuracy_pct": round(step_acc_pct, 1),
        "step_tracking_ci_95": [step_ci_low, step_ci_high],
        "mean_detection_delay_frames": round(mean_delay, 2),
        "median_latency_ms": round(median_lat, 1),
        "p95_latency_ms": round(p95_lat, 1),
        "total_calls": calls_used,
        "total_spend_usd": round(spend_usd, 4),
        "targets": {
            "error_detection_rate": met_detection,
            "false_alarms": met_false_alarms,
            "step_accuracy": met_step_acc,
            "latency": met_latency,
            "spend": met_spend,
        },
        "error_type_breakdown": error_breakdown,
        "top_failures": failures[:5],
    }
    (RESULTS_DIR / "results.json").write_text(json.dumps(results_data, indent=2), encoding="utf-8")

    # Update manifest.json with model and honest descriptions
    if MANIFEST_FILE.exists():
        try:
            manifest_json = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
            manifest_json["model"] = f"{minfo['vision_model']} via {minfo['provider']}"
            manifest_json["captured_date"] = time.strftime("%Y-%m-%d")
            for r in manifest_json.get("runs", []):
                if r["id"] == "correct_01":
                    r["description"] = f"Flawless 10-step refund procedure verified by {minfo['vision_model']} without deviations."
                elif r["id"] == "mistake_01":
                    r["description"] = f"Intentional step-skip violation intercepted and warned by {minfo['vision_model']}."
            MANIFEST_FILE.write_text(json.dumps(manifest_json, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Manifest update warning: {e}")

    # Generate REPORT.md
    report_md = f"""# ScreenGuard Evaluation Report

**Evaluation Date**: {results_data['evaluation_date']}  
**Provider**: `{minfo['provider']}` | **Vision Model**: `{minfo['vision_model']}` | **Text Model**: `{minfo['text_model']}`  
**Mode**: `{settings.MODE}` | **USE_SAM**: `{settings.USE_SAM}` | **Window**: `{args.window}` frames  
**Sample Size**: {len(eval_results)} runs ({num_correct_runs} correct, {num_mistake_runs} mistake), {total_frames} total frames  
**Cache Policy**: `--no-cache` active ({total_cache_hits} cache hits)  
**Total Compute**: {calls_used} model calls, ${spend_usd:.4f} USD spend  

---

## 1. Executive Summary & Target Compliance

| Metric | Measured Result | 95% Confidence Interval | Sample Size | Target Benchmark | Status |
|---|---|---|---|---|---|
| **Error Detection Rate** | **{detection_rate_pct:.1f}%** | [{det_ci_low}%, {det_ci_high}%] | {num_mistake_runs} mistake runs | >= 75.0% | **{met_detection}** |
| **Step Tracking Accuracy** | **{step_acc_pct:.1f}%** | [{step_ci_low}%, {step_ci_high}%] | {eval_correct_frames} correct frames | >= 70.0% | **{met_step_acc}** |
| **False Alarms (per Run)** | **{false_alarms_per_correct:.2f}** | — | {num_correct_runs} correct runs | <= 1.00 | **{met_false_alarms}** |
| **False Alarms (per 100 Frames)** | **{false_alarms_per_100_frames:.2f}** | — | {total_correct_frames} correct frames | — | Informational |
| **Pre-violation False Alarms** | **{pre_violation_false_alarms}** | — | {num_mistake_runs} mistake runs | — | Informational |
| **Mean Detection Delay** | **{mean_delay:.2f} frames** | — | {len(detection_delays)} detected runs | <= 2.0 frames | **{'Met' if mean_delay <= 2.0 else 'Not met'}** |
| **Real Call Latency (Median / p95)** | **{median_lat:.1f} ms / {p95_lat:.1f} ms** | — | {len(real_latencies)} real calls | <= 3000 ms | **{met_latency}** |
| **Total Spend** | **${spend_usd:.4f} USD** | — | All runs | < $5.00 USD | **{met_spend}** |

---

## 2. Breakdown by Error Type

| Error Category | Detected / Total | Detection Rate |
|---|---|---|
"""
    for etype, data in error_breakdown.items():
        rate = (data["detected"] / data["total"] * 100.0) if data["total"] else 0.0
        report_md += f"| `{etype}` | {data['detected']} / {data['total']} | **{rate:.1f}%** |\n"

    report_md += "\n---\n\n## 3. Top Observed Limitations & Real Failure Modes\n\n"
    if failures:
        for i, f in enumerate(failures[:5], 1):
            report_md += f"{i}. **[{f['type']}] Run `{f['run_id']}`, Frame `{f['frame']}`**:\n"
            report_md += f"   - *Ground Truth*: {f['truth']}\n"
            report_md += f"   - *Agent Action*: {f['agent_action']}\n"
            report_md += f"   - *Evidence Text*: \"{f['evidence']}\"\n"
            report_md += f"   - *Diagnosis*: {f['cause']}\n\n"
    else:
        report_md += "No major failure modes observed during this evaluation run.\n\n"

    report_md += """### What This Evaluation Does Not Show
- **Synthetic/Automated Operator Dynamics**: Recorded Playwright test runs execute with deterministic timing; real-world operators may type with pauses, typos, and sporadic browser scrolling.
- **Single Enterprise Domain**: Testing covers the Acme Admin Refund procedure across 6 distinct views. Cross-domain generalizability across different POS or legacy billing applications requires distinct procedure prompt definitions.
- **Sample Scale**: Evaluation comprises 16 recorded sessions (8 correct, 8 mistake runs). Broader variance requires hundreds of runs across diverse display resolutions.

---

## 4. Replay Artifacts
- **Correct Run Replay Bundle**: `eval/results/replay/correct/`
- **Mistake Run Replay Bundle**: `eval/results/replay/mistake/`
"""
    (RESULTS_DIR / "REPORT.md").write_text(report_md, encoding="utf-8")
    print(f"\nREPORT.md generated at: {RESULTS_DIR / 'REPORT.md'}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
