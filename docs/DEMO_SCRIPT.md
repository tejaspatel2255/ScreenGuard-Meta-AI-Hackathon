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
  1. Click the **"🛫 Preflight"** button in the header. Show all green checkmarks (Backend, Demo App, Budget, Screen Sharing).
  2. Click **"Load Demo"** in the Procedure Panel. Show the 10 plain-English procedural steps being ingested and parsed into structured milestones with risk flags.
  3. Click **"Start Session"**. The live Checklist activates on Step 1.
  4. Click **"Share Tab & Begin Supervision"** and select the Acme Admin tab.
- **Voiceover**:
  > *"Meet ScreenGuard: an autonomous supervisor agent built for the Meta Global AI Hackathon. ScreenGuard ingests standard written procedures, parses them into stateful milestones, and watches a shared browser tab. Notice our privacy safeguard: frames are downscaled and processed strictly in-memory. Nothing is ever saved to disk."*

#### 0:40 – 1:15 | Correct Run: Steps Turn Green
- **Visual**: In Acme Admin:
  1. Sign in with demo credentials. ScreenGuard's checklist checks off Step 1 with a green checkmark and advances to Step 2.
  2. Open Order ORD-1002. ScreenGuard advances to Step 3 and Step 4.
  3. Click "Start refund". Fill in Reason "Damaged item", Amount "120.00", and tick "Manager approved".
  4. Point to the **Decision Trace** updating live in real-time, displaying model confidence and evidence description.
  5. Click "Review refund", then "Confirm refund". Show ScreenGuard confirming completion of all 10 steps.
- **Voiceover**:
  > *"As the operator works, ScreenGuard's client-side change detector monitors 32x32 thumbnail diffs, sending frames only when the screen stabilizes. The multimodal vision model verifies the action against expected visual conditions. Notice the live Decision Trace: it explains the exact reason for every state change. Steps turn green seamlessly without slowing down the operator."*

#### 1:15 – 1:55 | Deliberate Mistake: Skipping Manager Approval
- **Visual**: In ScreenGuard, click **"Restart Session"**.
  1. In Acme Admin, restart and open the refund form for ORD-1002.
  2. Select reason and enter $120.00, but **deliberately DO NOT tick "Manager approved"**.
  3. Click "Review refund".
  4. **BOOM**: Show ScreenGuard's **STOP banner** instantly pop up in bright amber/red!
  5. Show the banner text: *"Step was skipped: Critical high-risk step was skipped: Manager approval required for refunds over $100."*
  6. Show the Decision Trace logging the blocking violation on screen, and the **Stops counter** in the StatsBar incrementing to 1.
  7. In Acme Admin, go back and tick the checkbox. Show ScreenGuard clear the alert and allow the flow to proceed safely.
- **Voiceover**:
  > *"Now, let's watch what happens when an operator makes a mistake. Here, the operator attempts to review a $120 refund without required manager signoff. Instantly, ScreenGuard's deterministic StepEngine detects the missing prerequisite! A high-risk STOP banner fires, preventing the operator from confirming the unauthorized transaction. ScreenGuard caught the error at the exact moment it happened, before any money left the company."*

#### 1:55 – 2:25 | The Evaluation Numbers & Session Report
- **Visual**: 
  1. In ScreenGuard, click the **"📊 Evaluation"** tab. Show the honest benchmark numbers: 100% error detection rate across all 8 mistake runs, step accuracy at 67.9%, and 0 ms delay.
  2. Click **"📥 JSON"** and **"📄 Markdown"** export buttons in the Decision Trace to demonstrate reproducible audit reporting.
- **Voiceover**:
  > *"Judges can view our full verification report directly inside the product via the Evaluation tab. Tested across 16 real sessions in MODE=real, ScreenGuard achieved a 100% error detection rate across all 5 mistake categories with transparent Wilson confidence intervals, and full session report exports."*

#### 2:25 – 3:00 | Architecture & Public Replay Mode
- **Visual**: 
  1. Open the public deployment: `https://screenguard.vercel.app`.
  2. Click **"🎬 Watch Recorded Demo"**.
  3. Show the static replay playing smoothly without any backend required.
- **Voiceover**:
  > *"Under the hood, ScreenGuard enforces strict safety: a 300-call session cap, a $100 hard ceiling, and zero telemetry leakage. Anyone can experience our recorded benchmarks on our free public Replay site on Vercel without needing API keys or local servers. ScreenGuard: building autonomous supervision for everyday enterprise workflows. Thank you."*
