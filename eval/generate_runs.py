import http.server
import json
import os
import random
import socketserver
import sys
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

PORT = 5588
DEMO_TARGET_DIR = Path(__file__).resolve().parent.parent / "demo_target"
DATA_DIR = Path(__file__).resolve().parent / "data"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_TARGET_DIR), **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress HTTP server logging


def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), QuietHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd


def capture_frame(page, run_dir: Path, frame_idx: int, label_list: list):
    frame_name = f"frame_{frame_idx:04d}.jpg"
    frame_path = run_dir / frame_name
    page.screenshot(path=str(frame_path), type="jpeg", quality=85)

    truth = page.evaluate("window.__state.truth")
    screen = page.evaluate("window.__state.screen")
    label_list.append({
        "frame": frame_name,
        "frame_idx": frame_idx,
        "screen": screen,
        "current_step": truth.get("current_step"),
        "steps_done": truth.get("steps_done", []),
        "violations": truth.get("violations", []),
    })


def run_correct_flow(page, run_dir: Path, variant_idx: int):
    labels = []
    frame_idx = 1

    # 1. Login
    page.goto(f"http://127.0.0.1:{PORT}")
    page.wait_for_selector("#btn-signin")
    time.sleep(0.2)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    page.click("#btn-signin")
    page.wait_for_selector("#btn-open-ord-1002")
    time.sleep(0.3)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    # 2. Open ORD-1002
    page.click("#btn-open-ord-1002")
    page.wait_for_selector("#btn-start-refund")
    time.sleep(0.3)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    # 3. Start refund
    page.click("#btn-start-refund")
    page.wait_for_selector("#btn-review")
    time.sleep(0.3)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    # 4. Fill refund form correctly
    page.select_option("#sel-reason", "Damaged item")
    time.sleep(0.2)
    page.fill("#inp-amount", "120.00")
    time.sleep(0.2)
    page.check("#chk-manager")
    time.sleep(0.2)
    notes = [
        "Customer reported minor packaging damage on arrival.",
        "Box torn during delivery transit; item lightly scuffed.",
        "Approved replacement credit.",
        "Priority customer claim verified."
    ]
    page.fill("#txt-note", notes[variant_idx % len(notes)])
    time.sleep(0.3)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    # 5. Click Review refund
    page.click("#btn-review")
    page.wait_for_selector("#btn-confirm")
    time.sleep(0.3)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    # 6. Click Confirm refund
    page.click("#btn-confirm")
    page.wait_for_selector("#btn-done")
    time.sleep(0.3)
    capture_frame(page, run_dir, frame_idx, labels)

    # Write labels.json
    output_meta = {
        "run_id": run_dir.name,
        "is_mistake": False,
        "error_type": None,
        "first_violation_frame": None,
        "frames": labels
    }
    (run_dir / "labels.json").write_text(json.dumps(output_meta, indent=2), encoding="utf-8")


def run_mistake_flow(page, run_dir: Path, error_type: str):
    labels = []
    frame_idx = 1
    first_violation_frame = None

    # Login
    page.goto(f"http://127.0.0.1:{PORT}")
    page.wait_for_selector("#btn-signin")
    time.sleep(0.2)
    capture_frame(page, run_dir, frame_idx, labels)
    frame_idx += 1

    if error_type == "wrong_value" and random.random() < 0.5:
        # Open wrong order ORD-1003 instead of ORD-1002
        page.click("#btn-signin")
        page.wait_for_selector("#btn-open-ord-1003")
        time.sleep(0.3)
        page.click("#btn-open-ord-1003")
        first_violation_frame = frame_idx
        page.wait_for_selector("#btn-start-refund")
        time.sleep(0.3)
        capture_frame(page, run_dir, frame_idx, labels)
        frame_idx += 1

        page.click("#btn-start-refund")
        page.wait_for_selector("#btn-review")
        time.sleep(0.3)
        capture_frame(page, run_dir, frame_idx, labels)
    else:
        # Normal open ORD-1002
        page.click("#btn-signin")
        page.wait_for_selector("#btn-open-ord-1002")
        time.sleep(0.3)
        page.click("#btn-open-ord-1002")
        page.wait_for_selector("#btn-start-refund")
        time.sleep(0.3)
        page.click("#btn-start-refund")
        page.wait_for_selector("#btn-review")
        time.sleep(0.3)
        capture_frame(page, run_dir, frame_idx, labels)
        frame_idx += 1

        # Apply specific error on refund form
        if error_type == "skipped_step":
            # Leave manager approval unticked on $120 refund!
            page.select_option("#sel-reason", "Damaged item")
            page.fill("#inp-amount", "120.00")
            # Do NOT check #chk-manager
            page.fill("#txt-note", "Missing manager signoff intentionally.")
            time.sleep(0.3)
            page.click("#btn-review")
            first_violation_frame = frame_idx
            page.wait_for_selector("#btn-confirm")
            time.sleep(0.3)
            capture_frame(page, run_dir, frame_idx, labels)
            frame_idx += 1

        elif error_type == "wrong_order":
            # Click Review refund immediately before selecting reason or amount
            page.click("#btn-review")
            first_violation_frame = frame_idx
            page.wait_for_selector("#btn-confirm")
            time.sleep(0.3)
            capture_frame(page, run_dir, frame_idx, labels)
            frame_idx += 1

        elif error_type == "wrong_control":
            # Select "Wrong item" instead of "Damaged item"
            page.select_option("#sel-reason", "Wrong item")
            page.fill("#inp-amount", "120.00")
            page.check("#chk-manager")
            time.sleep(0.3)
            page.click("#btn-review")
            first_violation_frame = frame_idx
            page.wait_for_selector("#btn-confirm")
            time.sleep(0.3)
            capture_frame(page, run_dir, frame_idx, labels)
            frame_idx += 1

        elif error_type == "wrong_value":
            # Enter 1200.00 instead of 120.00
            page.select_option("#sel-reason", "Damaged item")
            page.fill("#inp-amount", "1200.00")
            page.check("#chk-manager")
            time.sleep(0.3)
            page.click("#btn-review")
            first_violation_frame = frame_idx
            page.wait_for_selector("#btn-confirm")
            time.sleep(0.3)
            capture_frame(page, run_dir, frame_idx, labels)
            frame_idx += 1

        elif error_type == "premature_submit":
            # Review has no approval, but user clicks confirm refund!
            page.select_option("#sel-reason", "Damaged item")
            page.fill("#inp-amount", "120.00")
            # Do NOT check #chk-manager
            page.click("#btn-review")
            page.wait_for_selector("#btn-confirm")
            time.sleep(0.2)
            page.click("#btn-confirm")
            first_violation_frame = frame_idx
            page.wait_for_selector("#btn-done")
            time.sleep(0.3)
            capture_frame(page, run_dir, frame_idx, labels)

    output_meta = {
        "run_id": run_dir.name,
        "is_mistake": True,
        "error_type": error_type,
        "first_violation_frame": first_violation_frame,
        "frames": labels
    }
    (run_dir / "labels.json").write_text(json.dumps(output_meta, indent=2), encoding="utf-8")


def main():
    print(f"Starting local demo app server on port {PORT}...")
    server = start_server()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    mistake_types = [
        "skipped_step",
        "wrong_order",
        "wrong_value",
        "wrong_control",
        "premature_submit",
        "skipped_step",     # Repeat common
        "wrong_value",      # Repeat common
        "wrong_order",      # Repeat common
    ]

    print("Generating 8 correct runs and 8 mistake runs with Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})

        # 8 Correct Runs
        for i in range(1, 9):
            run_id = f"correct_{i:02d}"
            run_dir = DATA_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            page = context.new_page()
            run_correct_flow(page, run_dir, i)
            page.close()
            print(f"  [✓] Generated {run_id}")

        # 8 Mistake Runs
        for i, err in enumerate(mistake_types, 1):
            run_id = f"mistake_{i:02d}_{err}"
            run_dir = DATA_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            page = context.new_page()
            run_mistake_flow(page, run_dir, err)
            page.close()
            print(f"  [!] Generated {run_id} ({err})")

        browser.close()

    print("\nDataset generation complete! Saved in eval/data/")


if __name__ == "__main__":
    main()
