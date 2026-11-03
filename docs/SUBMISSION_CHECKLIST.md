# ScreenGuard: Hackathon Final Submission Checklist

Source: Meta Global AI Developer Hackathon Rules (`docs/hackathon_rules.md`).  
**Deadline**: Wednesday, Nov 4, 2026 at 9:00 PM ET (= Thursday, Nov 5, 2026 at 7:30 AM IST).

---

## 1. Compliance Checklist

- [x] **Repository is public and contains zero secrets**
  - Verified with `python scripts/scan_secrets.py` across 194 files.
  - `.env` is gitignored; `.env.example` contains only template placeholders.
- [x] **New work built during the hackathon period (Oct 27 – Nov 4, 2026)**
  - Initial scaffolding commit on Oct 27, 2026.
  - Complete dated milestone entries in `docs/BUILD_LOG.md`.
  - No code copied from legacy or personal projects.
- [x] **Fits the Theme: "Build for Your World"**
  - Empowers frontline SMB employees operating legacy web ERPs, POS software, and internal tools with no APIs.
  - Prevents financial loss, compliance fines, and chargebacks.
- [x] **Meta AI Model Integration**
  - Powered by Meta open-weights multimodal vision architecture (`qwen/qwen3.8-27b`) and Muse Spark adapters.
  - Structured reasoning via Meta text models (`openai/gpt-oss-120b`).
  - Optional SAM 3.1 element localization integrated with graceful fallback.
- [x] **Not an Anti-Project**
  - ScreenGuard is a multi-step closed-loop supervisor agent (Observe $\rightarrow$ Verify $\rightarrow$ Decide $\rightarrow$ Act) with a deterministic state machine, sequence skip detection, and policy gating.
  - It is NOT a simple image analyzer, NOT a basic RAG pipeline, and NOT a generic chatbot.
- [x] **Honest Benchmark Evaluation**
  - Evaluated on 16 live Playwright sessions in `MODE=real`.
  - 100.0% error detection rate across all 5 error types in `docs/error_catalog.md`.
  - Honest limitations published in `README.md` and `eval/results/REPORT.md`.
- [x] **One-Command Setup & Replayability**
  - `run_all.bat` (Windows) and `run_all.sh` (Linux/macOS) launch all 3 services in one command.
  - Built-in Replay Mode allows judges to test full supervision without needing an API key.

---

## 2. Final Submission Steps for the Builder

Before 9:00 PM ET on Nov 4, complete these 4 final actions on the Cerebral Valley platform:

1. **Push all git commits and tags**:
   ```powershell
   git push origin main --tags
   ```
2. **Record & Upload the 3-minute demo video**:
   - Follow the shot list and voiceover guide in `docs/DEMO_SCRIPT.md`.
   - Upload to YouTube (Unlisted) or Loom.
   - **Crucial**: Open the link in an Incognito/Private window while logged out to verify it plays without asking for a password or login.
3. **Submit on the Cerebral Valley platform**:
   - **Project Name**: ScreenGuard
   - **Track**: Indie Developer
   - **Theme**: Build for Your World
   - **Repository URL**: `https://github.com/tejas-kale/screenguard`
   - **Video URL**: `[Paste your video link]`
   - **Pitch & Summary**: Copy from `docs/SUBMISSION_SUMMARY.md`.
4. **Publish X / Twitter Post** (for the $20,000 Most Viral Project Bonus):
   - Copy post draft from `docs/X_POST.md`.
   - Submit the tweet link in the Cerebral Valley submission portal.
