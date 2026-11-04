"""Audit script to verify claims across docs and frontend.

Fails if any documentation or source code claims a model is active when the
configured provider/flags do not support it.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.app.core.config import settings

# Files to check
TARGET_FILES = [
    ROOT / "README.md",
    ROOT / "docs" / "SUBMISSION_CHECKLIST.md",
    ROOT / "docs" / "SUBMISSION_SUMMARY.md",
    ROOT / "docs" / "DEMO_SCRIPT.md",
    ROOT / "frontend" / "src" / "components" / "ReplayMode.tsx",
    ROOT / "frontend" / "public" / "replay" / "manifest.json",
]


def check_claims() -> int:
    provider = settings.PROVIDER.lower()
    use_sam = settings.USE_SAM
    violations = []

    for file_path in TARGET_FILES:
        if not file_path.exists():
            continue
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        for idx, line in enumerate(lines, 1):
            lower = line.lower()
            
            # If provider is not meta or baseten, lines claiming active Muse Spark execution are invalid
            if provider not in ["meta", "baseten"]:
                if "powered by muse spark" in lower or "executed by muse spark" in lower:
                    violations.append((file_path, idx, f"Claims Muse Spark while PROVIDER={provider}: '{line.strip()}'"))
            
            # Check false SAM claims if USE_SAM is disabled
            if not use_sam:
                if "using sam 3.1" in lower or "sam 3.1 element detection" in lower:
                    if "optional" not in lower and "disabled" not in lower and "fallback" not in lower:
                        violations.append((file_path, idx, f"Claims active SAM 3.1 while USE_SAM=False: '{line.strip()}'"))

            # Check false open-weights claims for Groq qwen/gpt-oss
            if "groq" in lower and ("meta open-weights" in lower and "qwen" in lower):
                violations.append((file_path, idx, f"Associates Meta open-weights with non-Meta model: '{line.strip()}'"))

    if violations:
        print(f"FAILED: Found {len(violations)} claim violation(s):")
        for f, l, msg in violations:
            print(f"  {f.relative_to(ROOT)}:{l} -> {msg}")
        return 1

    print(f"PASSED: All claims match configured provider '{provider}' and flags (USE_SAM={use_sam}).")
    return 0


if __name__ == "__main__":
    sys.exit(check_claims())
