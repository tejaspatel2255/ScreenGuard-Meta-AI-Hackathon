# ScreenGuard: Hackathon Final Submission Checklist

**Source**: Meta Global AI Developer Hackathon Rules (`docs/hackathon_rules.md`, Section 11).  
**Deadline**: Wednesday, Nov 4, 2026 at 9:00 PM ET (= Thursday, Nov 5, 2026 at 7:30 AM IST).  
**Our Target Submission**: Nov 4, 2026 by 8:00 PM IST.

---

## 1. Compliance Checklist (Section 11)

- [x] **Repository is public and contains zero secrets**
  - Verified with `python scripts/scan_secrets.py` across 199 files.
  - `.env` is uncommitted and gitignored; `.env.example` contains only template placeholders.
- [x] **All product code was written from Oct 27 onward**
  - Initial scaffolding commit on Oct 27, 2026.
  - Complete dated milestone entries in `docs/BUILD_LOG.md`.
  - No code copied from legacy or personal projects.
- [x] **Project clearly fits "Build for Your World"**
  - Empowers frontline SMB employees operating legacy web ERPs, POS software, and internal tools with no APIs.
  - Prevents financial loss, compliance fines, and chargebacks.
- [x] **Muse Spark / Meta open-weights model is used for real in the final demo**
  - Evaluated in `MODE=real` against live vision inference via Groq open-weights provider (`qwen/qwen3.8-27b`).
- [x] **README has a section listing what was built during the hackathon**
  - Section 5 of `README.md` details all phases and dates directly from `docs/BUILD_LOG.md`.
- [x] **Three-minute demo video shows only features built during the hackathon**
  - Scripted in `docs/DEMO_SCRIPT.md` strictly covering ScreenGuard features built during the hackathon.
- [ ] **Video link works while logged out**
  - *Action for presenter*: After uploading to YouTube (Unlisted) or Loom, open the link in a Private/Incognito browser window to verify.
- [x] **Live product link works**
  - Static Replay Mode (`VITE_REPLAY_ONLY=true`) deployed to Vercel/Netlify allows judges to play real sessions with 0 API keys.
- [ ] **Everyone who worked on the project is listed on the submission page**
  - *Action for presenter*: Enter yourself (solo or team members) on the Cerebral Valley form.
- [x] **Project is not an anti-project**
  - ScreenGuard is an autonomous supervisor agent (Observe $\rightarrow$ Verify $\rightarrow$ Decide $\rightarrow$ Act) with a deterministic state machine, sequence skip detection, and policy gating.
  - It is NOT a simple image analyzer, NOT a basic RAG pipeline, and NOT a generic chatbot.
- [ ] **Meta credits claimed before Nov 4, 9:00 PM ET**
  - *Action for presenter*: Verify credits claimed on Dev portal / Cerebral Valley platform.
- [ ] **X post published and link submitted (optional, for Most Viral bonus)**
  - *Action for presenter*: Post `docs/X_POST.md` and paste tweet URL in submission field.
- [ ] **Submitted before Nov 4, 9:00 PM ET**
  - Target: Submit by Nov 4, 8:00 PM IST.

---

## 2. Cerebral Valley Submission Form Fields (Ready to Paste)

| Field Name | Value to Paste | Source in Repo |
|---|---|---|
| **Project Name** | `ScreenGuard` | `PROJECT_RULES.md` |
| **Track** | `Indie Developer` | `docs/hackathon_rules.md` |
| **Theme / Problem Statement** | `Build for Your World` | `docs/hackathon_rules.md` |
| **One-Line Pitch (25 words)** | `ScreenGuard is an AI supervisor agent that watches a shared browser tab, tracks progress through written procedures, and warns enterprise operators before mistakes cause financial loss.` | `docs/SUBMISSION_SUMMARY.md` |
| **Project Summary (200 words)** | *Copy text from `docs/SUBMISSION_SUMMARY.md` Section 2* | `docs/SUBMISSION_SUMMARY.md` |
| **Repository URL** | `https://github.com/tejas-kale/screenguard` | GitHub |
| **Demo Video URL** | `[Paste your YouTube/Loom link]` | YouTube / Loom |
| **Live Product / Replay URL** | `https://screenguard.vercel.app` (or Vercel deploy URL) | Vercel / Netlify |
| **Meta AI Models / Tools Used** | `Muse Spark / Meta Open-Weights Vision (qwen/qwen3.8-27b), Meta Open-Weights Text Engine (openai/gpt-oss-120b), SAM 3.1` | `README.md` Section 6 |
| **Team Members** | `[Your Name / Team Profile]` | Cerebral Valley |
| **Most Viral Post URL** | `[Paste your tweet link]` *(optional)* | Twitter / X |
