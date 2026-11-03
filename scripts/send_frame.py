import sys
from pathlib import Path
import httpx


def send_frame_main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/send_frame.py <SESSION_ID> <IMAGE_PATH> [BASE_URL]")
        print("Example: python scripts/send_frame.py sess-abc12345 sample_screen.png")
        sys.exit(1)

    session_id = sys.argv[1]
    image_path = Path(sys.argv[2])
    base_url = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8000"

    if not image_path.exists():
        print(f"Error: image file '{image_path}' not found.")
        sys.exit(1)

    image_bytes = image_path.read_bytes()
    mime = "image/jpeg" if image_bytes.startswith(b"\xff\xd8") else "image/png"

    url = f"{base_url.rstrip('/')}/api/session/{session_id}/frame"
    print(f"Sending frame ({len(image_bytes)} bytes, {mime}) to {url}...")

    try:
        response = httpx.post(url, content=image_bytes, headers={"Content-Type": mime}, timeout=60.0)
        if response.status_code != 200:
            print(f"Server Error {response.status_code}: {response.text}")
            sys.exit(1)

        data = response.json()
        print("=" * 60)
        print("ScreenGuard Supervisor Step Update:")
        print(f"Action:       {data.get('action')}")
        print(f"Reason:       {data.get('reason')}")
        print(f"Warning:      {data.get('warning')}")
        print(f"Current Step: {data.get('current_step_id')}")
        print(f"Blocking:     {data.get('blocking')}")
        print(f"Latency:      {data.get('latency_ms', 0):.1f}ms")
        print(f"Spend:        ${data.get('estimated_spend_usd', 0):.6f}")
        print(f"Cached:       {data.get('cached')}")
        print(f"Calls Used:   {data.get('calls_used')}")
        print("=" * 60)
    except Exception as e:
        print(f"Failed to post frame: {e}")
        sys.exit(1)


if __name__ == "__main__":
    send_frame_main()
