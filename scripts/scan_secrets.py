import os
import re
import sys
from pathlib import Path

# Sensitive patterns
PATTERNS = [
    (r"gsk_[a-zA-Z0-9]{20,}", "Groq API Key"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/Generic API Key"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub Personal Access Token"),
    (r"bearer\s+[a-zA-Z0-9_\-\.]{25,}", "Bearer Token"),
    (r"-----BEGIN (?:RSA|OPENSSH|EC|DSA)? PRIVATE KEY-----", "Private Key"),
    (r"meta-models/[a-zA-Z0-9_\-]+:[a-zA-Z0-9]{20,}", "Baseten Key"),
]

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".pytest_cache",
    ".venv",
    "venv",
    "dist",
    "build",
    ".gemini",
}

IGNORED_FILES = {
    ".env",
    ".env.local",
    ".env.example",
    "scan_secrets.py",
}


def scan_file(filepath: Path) -> list:
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return findings

    for line_num, line in enumerate(content.splitlines(), 1):
        for pattern, label in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Ignore placeholders
                if "your_" in line.lower() or "example" in line.lower() or "mock" in line.lower():
                    continue
                findings.append((line_num, label, line.strip()[:60]))
    return findings


def main():
    root = Path(__file__).resolve().parent.parent
    total_scanned = 0
    total_findings = 0

    print("=" * 60)
    print("ScreenGuard Secrets Scanner")
    print(f"Scanning repository root: {root}")
    print("=" * 60)

    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(ignored in path.parts for ignored in IGNORED_DIRS):
            continue
        if path.name in IGNORED_FILES or path.name.endswith(".png") or path.name.endswith(".jpg"):
            continue

        total_scanned += 1
        findings = scan_file(path)
        if findings:
            rel = path.relative_to(root)
            for line_num, label, snippet in findings:
                print(f"[!] SECRET DETECTED in {rel}:{line_num} -> {label}")
                print(f"    Snippet: {snippet}")
                total_findings += 1

    print("-" * 60)
    print(f"Scanned {total_scanned} files.")
    if total_findings > 0:
        print(f"FAIL: Found {total_findings} potential secret(s).")
        sys.exit(1)
    else:
        print("PASS: Clean repository! No secrets or API keys found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
