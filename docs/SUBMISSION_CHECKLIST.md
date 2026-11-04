# ScreenGuard: Hackathon Final Submission Checklist

**Source**: Meta Global AI Developer Hackathon Rules (`docs/hackathon_rules.md`, Section 11).  
**Deadline**: Wednesday, Nov 4, 2026 at 9:00 PM ET (= Thursday, Nov 5, 2026 at 7:30 AM IST).  
**Our Target Submission**: Nov 5, 2026 by 2:00 AM IST (well before 7:30 AM IST buffer).

---

## 1. Compliance Checklist (Section 11)

- [x] **Repository is public and contains zero secrets**
  - Verified with `python scripts/scan_secrets.py`.
  - `.env` is uncommitted and gitignored; `.env.example` contains only template placeholders.
- [x] **All product code was written from Oct 27 onward**
  - Initial scaffolding commit on Oct 27, 2026.
  - Complete dated milestone entries in `docs/BUILD_LOG.md`.
  - No code copied from legacy or personal projects.
- [x] **Project clearly fits "Build for Your World"**
  - Empowers frontline SMB employees operating legacy web ERPs, POS software, and internal tools with no APIs.
  - Prevents financial loss, compliance fines, and chargebacks.
- [x] **Multimodal models are used for real and truthfully labeled**
  - Evaluated in `MODE=real` against live vision inference (`qwen/qwen3.8-27b` via Groq) with adapters for Meta Model API (`muse-spark-1.3`).
  - Model provenance is explicitly surfaced in `/api/health`, the header badges, the evaluation tab, and all documentation.
- [x] **README has a section listing what was built during the hackathon**
  - Section 7 of `README.md` details all phases and dates directly from `docs/BUILD_LOG.md`.
- [x] **Three-minute demo video shows only features built during the hackathon**
  - Scripted in `docs/DEMO_SCRIPT.md` strictly covering ScreenGuard features built during the hackathon.
- [ ] **Video link works while logged out**
  - *Action for presenter*: After uploading to YouTube (Unlisted) or Loom, open the link in a Private/Incognito browser window to verify.
- [x] **Live product link works**
  - Static Replay Mode (`VITE_REPLAY_ONLY=true`) deployed to Vercel/Netlify allows judges to play real sessions with 0 API keys.
- [ ] **Everyone who worked on the project is listed on the submission page**
  - *Action for presenter*: Enter yourself on the Cerebral Valley form.
- [x] **Project is not an anti-project**
  - ScreenGuard is an autonomous supervisor agent (Observe $\rightarrow$ Verify $\rightarrow$ Decide $\rightarrow$ Act) with a deterministic state machine, preview inspection, and policy gating.
- [ ] **X post published and link submitted (optional, for Most Viral bonus)**
  - *Action for presenter*: Post `docs/X_POST.md` and paste tweet URL in submission field.
- [ ] **Submitted before Nov 4, 9:00 PM ET**

---

## 2. Cerebral Valley Submission Form Fields (Ready to Paste)

| Field Name | Value to Paste | Source in Repo |
|---|---|---|
| **Project Name** | `ScreenGuard` | `PROJECT_RULES.md` |
| **Track** | `Indie Developer` | `docs/hackathon_rules.md` |
| **25-Word Pitch** | `ScreenGuard is an AI supervisor agent that watches a shared browser tab, tracks progress through written procedures, and warns enterprise operators before mistakes cause financial loss.` | `docs/SUBMISSION_SUMMARY.md` |
| **Project Description** | See 200-word summary in `docs/SUBMISSION_SUMMARY.md` | `docs/SUBMISSION_SUMMARY.md` |
| **GitHub URL** | `https://github.com/tejaspatel2255/ScreenGuard-Meta-AI-Hackathon` | Git remote |
| **Live Demo URL** | `https://screenguard.vercel.app` | Vercel deployment |
| **Video URL** | *(Paste your YouTube or Loom link after recording)* | Video recording |
| **Tools Used** | `qwen/qwen3.8-27b (vision via Groq), openai/gpt-oss-120b (text via Groq), Meta Model API adapter (muse-spark-1.3), Baseten client adapter` | `README.md` Section 5 |
