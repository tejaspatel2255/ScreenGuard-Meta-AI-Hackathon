# ScreenGuard: 3-Minute Demo Video Script

**Target Duration**: 2 minutes 50 seconds to 3 minutes  
**Format**: Screen capture with voiceover (side-by-side: Acme Admin on left, ScreenGuard on right)  
**Rule Compliance**: Demonstrates *only* code and features created during the hackathon (Oct 27 – Nov 4, 2026).

---

### Scene Breakdown & Timing

#### 0:00 – 0:30 | The Hook & Problem Statement
- **Visual**: Show the Acme Admin refund screen (`http://127.0.0.1:5500`). Point out the Refund form: Order ORD-1002, amount $120.00, and the subtle "Manager approved" checkbox.
- **Voiceover**: 
  > *"Every day, frontline staff execute critical procedures on legacy ERP and admin portals with no modern APIs or guardrails. One missing checkbox—like omitting Manager Approval on a refund over $100—leads to compliance audits, chargebacks, and lost revenue. Modernizing these legacy systems costs millions. What if an AI agent could sit beside the employee and supervise the workflow using pixels alone?"*

#### 0:30 – 1:00 | Introducing ScreenGuard & Starting Supervision
- **Visual**: Switch to ScreenGuard Dashboard (`http://localhost:5173`).
  1. Click **"Load Demo"** in the Procedure Panel. Show the 10 plain-English procedural steps being ingested and parsed into structured milestones with risk flags.
  2. Click **"Start Session"**. The live Checklist activates on Step 1.
  3. Click **"Share Tab & Begin Supervision"** and select the Acme Admin tab.
- **Voiceover**:
  > *"Meet ScreenGuard: an autonomous AI supervisor agent built for the Meta Global AI Hackathon. ScreenGuard ingests standard written procedures, parses them into stateful milestones, and watches a shared browser tab. Notice our privacy safeguard: frames are downscaled and processed strictly in-memory. Nothing is ever saved to disk."*

#### 1:00 – 1:45 | Walkthrough 1: The Correct Workflow
- **Visual**: In Acme Admin:
  1. Sign in with demo credentials. Show ScreenGuard's checklist instantly check off Step 1 with a green checkmark and advance to Step 2.
  2. Open Order ORD-1002. ScreenGuard advances to Step 3 and Step 4.
  3. Click "Start refund". Fill in Reason "Damaged item", Amount "120.00", and tick "Manager approved".
  4. Point to the **Decision Trace** updating live in real-time, displaying model confidence (1.00) and evidence description.
  5. Click "Review refund", then "Confirm refund". Show ScreenGuard confirming completion of all 10 steps.
- **Voiceover**:
  > *"As the operator works, ScreenGuard's client-side change detector monitors 32x32 thumbnail diffs, sending frames only when the screen stabilizes. Meta's multimodal vision model verifies the action against expected visual conditions. Notice the live Decision Trace on the right: it explains the exact reason for every state change. Steps advance seamlessly without slowing down the operator."*

#### 1:45 – 2:25 | Walkthrough 2: Catching a Costly Mistake Live!
- **Visual**: In ScreenGuard, click **"Restart Session"**.
  1. In Acme Admin, restart and open the refund form for ORD-1002.
  2. Select reason and enter $120.00, but **deliberately DO NOT tick "Manager approved"**.
  3. Click "Review refund".
  4. **BOOM**: Show ScreenGuard's **STOP / WARN banner** instantly pop up in bright amber/red with an alert chime!
  5. Show the banner text: *"Step was skipped: Manager approval required for refunds over $100."*
  6. Show the Decision Trace logging the blocking violation.
  7. In Acme Admin, fix the mistake by going back and ticking the checkbox. Show ScreenGuard clear the alert and allow the flow to proceed safely.
- **Voiceover**:
  > *"Now, let's watch what happens when an operator makes a mistake. Here, the operator attempts to submit a $120 refund without required manager signoff. Instantly, ScreenGuard's deterministic StepEngine detects the missing prerequisite! A high-risk warning banner fires, preventing the operator from confirming the unauthorized transaction. ScreenGuard caught the error at the exact moment it happened, before any money left the company."*

#### 2:25 – 2:50 | Technical Depth, Meta Tooling & Benchmark
- **Visual**: Show the slide or repo view of `eval/results/REPORT.md` and `eval/results/performance_chart.png`.
- **Voiceover**:
  > *"Under the hood, ScreenGuard combines Meta's open-weights vision intelligence with a pure-Python state machine and strict token cost controls. In our automated evaluation benchmark across 16 real Playwright sessions covering all five error categories, ScreenGuard achieved a 100% error detection rate with zero frame delay and an average cost of less than a quarter of a cent per run."*

#### 2:50 – 3:00 | Closing & Call to Action
- **Visual**: Show the live dashboard with the StatsBar and GitHub repository link.
- **Voiceover**:
  > *"ScreenGuard turns any legacy web portal into a self-supervising, error-free workflow. It's completely open source under MIT. Thank you!"*

---

### Quick Recording Checklist for the Presenter
- [ ] Display resolution set to 1920x1080 (or 1280x720) with 100% scaling.
- [ ] Run `run_all.bat` so Acme Admin (:5500), Backend (:8000), and Frontend (:5173) are active.
- [ ] Have the browser windows arranged side-by-side: Acme Admin on left half, ScreenGuard on right half.
- [ ] Ensure microphone is crisp and background noise is minimized.
- [ ] Keep video length strictly under 3 minutes (e.g. 2:55).
- [ ] Upload video as **Unlisted** on YouTube or Loom and verify the link opens in an incognito window without login.
