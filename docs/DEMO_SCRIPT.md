# ScreenGuard: 3-Minute Demo Video Script

**Target Duration**: Strictly 3 minutes (0:00 – 3:00)  
**Format**: Screen capture with voiceover (side-by-side: Acme Admin on left, ScreenGuard on right)  
**Rule Compliance**: Demonstrates *only* code and features created during the hackathon (Oct 27 – Nov 4, 2026).

---

### Scene Breakdown & Timings

#### 0:00 – 0:20 | Hook: The Costly Refund Mistake
- **Visual**: Show the Acme Admin refund screen (`http://127.0.0.1:5500`). Point out the form: Order ORD-1002, amount $120.00, and the subtle "Manager approved" checkbox.
- **Voiceover**: 
  > *"Every day, frontline staff execute critical workflows on legacy ERP and admin tools with no APIs or guardrails. One missing checkbox—like omitting Manager Approval on a refund over $100—leads to compliance audits, chargebacks, and lost revenue. What if an AI supervisor agent could sit beside the employee and prevent mistakes using pixels alone?"*

#### 0:20 – 0:40 | Load the Procedure and Start
- **Visual**: Switch to ScreenGuard Dashboard (`http://localhost:5173`).
  1. Click **"Load Demo"** in the Procedure Panel. Show the 10 plain-English procedural steps being ingested and parsed into structured milestones with risk flags.
  2. Click **"Start Session"**. The live Checklist activates on Step 1.
  3. Click **"Share Tab & Begin Supervision"** and select the Acme Admin tab.
- **Voiceover**:
  > *"Meet ScreenGuard: an autonomous supervisor agent built for the Meta Global AI Hackathon. ScreenGuard ingests standard written procedures, parses them into stateful milestones, and watches a shared browser tab. Notice our privacy safeguard: frames are downscaled and processed strictly in-memory. Nothing is ever saved to disk."*

#### 0:40 – 1:15 | Correct Run: Steps Turn Green
- **Visual**: In Acme Admin:
  1. Sign in with demo credentials. ScreenGuard's checklist instantly checks off Step 1 with a green checkmark and advances to Step 2.
  2. Open Order ORD-1002. ScreenGuard advances to Step 3 and Step 4.
  3. Click "Start refund". Fill in Reason "Damaged item", Amount "120.00", and tick "Manager approved".
  4. Point to the **Decision Trace** updating live in real-time, displaying model confidence (1.00) and evidence description.
  5. Click "Review refund", then "Confirm refund". Show ScreenGuard confirming completion of all 10 steps.
- **Voiceover**:
  > *"As the operator works, ScreenGuard's client-side change detector monitors 32x32 thumbnail diffs, sending frames only when the screen stabilizes. Meta's multimodal vision model verifies the action against expected visual conditions. Notice the live Decision Trace: it explains the exact reason for every state change. Steps turn green seamlessly without slowing down the operator."*

#### 1:15 – 2:00 | Deliberate Mistake: Skipping Manager Approval
- **Visual**: In ScreenGuard, click **"Restart Session"**.
  1. In Acme Admin, restart and open the refund form for ORD-1002.
  2. Select reason and enter $120.00, but **deliberately DO NOT tick "Manager approved"**.
  3. Click "Review refund".
  4. **BOOM**: Show ScreenGuard's **STOP / WARN banner** instantly pop up in bright amber/red with an alert chime!
  5. Show the banner text: *"Step was skipped: Critical high-risk step was skipped: Manager approval required for refunds over $100."*
  6. Show the Decision Trace logging the blocking violation on screen.
  7. In Acme Admin, go back and tick the checkbox. Show ScreenGuard clear the alert and allow the flow to proceed safely.
- **Voiceover**:
  > *"Now, let's watch what happens when an operator makes a mistake. Here, the operator attempts to review a $120 refund without required manager signoff. Instantly, ScreenGuard's deterministic StepEngine detects the missing prerequisite! A high-risk STOP banner fires, preventing the operator from confirming the unauthorized transaction. ScreenGuard caught the error at the exact moment it happened, before any money left the company."*

#### 2:00 – 2:25 | The Evaluation Numbers
- **Visual**: Show the slide or repo view of `eval/results/REPORT.md` and `eval/results/performance_chart.png`.
- **Voiceover**:
  > *"We evaluated ScreenGuard using an automated Playwright harness across 16 real sessions in MODE=real. Across all five error categories—skipped steps, wrong order, wrong values, wrong controls, and premature submits—ScreenGuard achieved a 100% error detection rate with zero frame delay and a median latency of 24 milliseconds, all for an average spend of less than a quarter of a cent per run."*

#### 2:25 – 2:45 | The Meta Tools & Roles
- **Visual**: Show the Meta Tools slide or README table highlighting Muse Spark (`muse-spark-1.3`), Meta Llama Vision models, and SAM 3.1.
- **Voiceover**:
  > *"ScreenGuard is powered by Meta's multimodal vision intelligence—supporting Meta Model API Muse Spark and Meta Llama open-weights vision architectures—serving as the perceptual judge for UI state verification. SOP procedures are structured using Meta language tooling, with optional UI localization via SAM 3.1. It operates with strict client-side change detection and a hard spend limit."*

#### 2:45 – 3:00 | Close
- **Visual**: Show the live dashboard with the StatsBar and GitHub repository link.
- **Voiceover**:
  > *"ScreenGuard turns any legacy web portal into a self-supervising, error-free workflow without APIs. It's completely open source under MIT. Thank you!"*

---

### Quick Recording Checklist for the Presenter
- [ ] Display resolution set to 1920x1080 (or 1280x720) with 100% scaling.
- [ ] Run `run_all.bat` so Acme Admin (:5500), Backend (:8000), and Frontend (:5173) are active.
- [ ] Browser windows arranged side-by-side: Acme Admin on left half, ScreenGuard on right half.
- [ ] Ensure microphone is crisp and background noise is minimized.
- [ ] Keep video length strictly under 3 minutes (e.g. 2:55).
- [ ] Upload video as **Unlisted** on YouTube or Loom and verify the link opens in an incognito window without login.
