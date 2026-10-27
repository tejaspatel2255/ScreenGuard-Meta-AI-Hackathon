# Setup checklist

Today is Oct 27, 2026, so the building period has started. Do sections 1 to 3 in the first hour, then start Phase 0.

## 1. Accounts and access

- [ ] Join the hackathon Discord, post in #intros, and note the #office-hours and #questions channels
- [ ] Claim the $150 Meta Model API credits (link was "coming soon"; watch #announcements). Deadline: Nov 4, 9:00 PM ET
- [ ] Add a credit card to the Meta account so API calls work, and set a spend limit notification on the Billing page (it does not block spending, so keep MAX_ESTIMATED_SPEND_USD at 100 or lower)
- [ ] Create an API key and store it in .env only (never in chat, never in git)
- [ ] Create a public GitHub repository named screenguard (empty, no code yet)
- [ ] Optional: request Baseten ($100) and Modal ($100) credits

## 2. Tools on your computer

- [ ] Git
- [ ] Python 3.11 or newer (python --version)
- [ ] Node.js 20 or newer (node -v)
- [ ] Google Chrome or Microsoft Edge (screen capture works best there)
- [ ] Antigravity with a Gemini Flash model selected; keep command approval on
- [ ] OBS Studio (for the 3-minute video later)
- [ ] After Phase 7 starts: pip install playwright, then playwright install chromium

## 3. Prepare the folder

1. Create the folder and unzip the starter files into it, so PROJECT_RULES.md sits in the folder root.
2. Open the folder in Antigravity.
3. Run these commands in the folder:

        git init
        git add .
        git commit -m "chore: add planning and rules files"

4. Add the commit hash to docs/BUILD_LOG.md later in Phase 0.
5. Copy .env.example to .env and leave MODE=mock for now.

## 4. Fill the knowledge files (30 minutes)

- [ ] Paste the Meta API documentation facts into docs/meta_api_notes.md (sections 1 to 7). Leave blanks if the docs do not say, and add a line in docs/open_questions.md.
- [ ] Try each model once with a throwaway script outside the repo (text, one screenshot, one segmentation, one short audio) and note what works. This answers open questions 1 and 2.
- [ ] Check Cerebral Valley and Discord for the Official Rules. If they are out, paste the new facts into docs/hackathon_rules.md.

## 5. Working method for every phase

1. Open a fresh agent conversation.
2. Paste the phase prompt from docs/MASTER_PROMPTS.md.
3. Planning mode (if available) for Phases 0, 2, 5, 7. Read the plan before approving.
4. Check the ACCEPTANCE line yourself.
5. Update docs/BUILD_LOG.md, commit, and tag (phase-0, phase-1 and so on).
6. If the agent drifts, start a new conversation with: Read PROJECT_RULES.md first.

## 6. Schedule

| Phase | Target dates | Done when |
|---|---|---|
| 0 Scaffold | Oct 27 | Repo runs, health check passes |
| 1 Model adapters | Oct 27 to 28 | One real call per available model works, spend guard on |
| 2 Parser and step engine | Oct 28 | 15 or more engine tests pass |
| 3 Demo target app | Oct 29 | Both flows and error catalog exist |
| 4 Screen capture | Oct 29 to 30 | Tab sharing and frame sending work |
| 5 Agent pipeline | Oct 30 to Nov 1 | A real run catches a deliberate mistake |
| 6 Live interface | Nov 1 | Demo runs with no instructions |
| 7 Evaluation harness | Nov 1 to 2 | REPORT.md from real runs |
| 8 Voice and export (optional) | Nov 2 | Spoken procedure and export work |
| 9 Hardening and live product | Nov 3 | Fresh clone, CI and public replay demo work |
| 10 Docs, video, submission | Nov 3 to 4 | Video, README, checklist done, submitted |

## 7. Time zones (India)

- ET is 9.5 hours behind IST until Nov 1 (US daylight time) and 10.5 hours behind after Nov 1.
- Agents 101 (today, 12:00 PM ET) is about 9:30 PM IST. Agents 102 (Oct 28, 12:00 PM ET) is about 9:30 PM IST.
- Daily office hours: 10 to 11 AM ET is about 7:30 to 8:30 PM IST until Oct 31, then about 8:30 to 9:30 PM IST from Nov 2.
- Submission deadline: Nov 4, 9:00 PM ET is about 7:30 AM IST on Nov 5. Target: submit on Nov 3.
- Closing ceremony: Nov 9, 12:00 PM ET is about 10:30 PM IST.

## 8. Daily habits

- Check Discord #announcements once a day.
- Commit at least once a day and keep BUILD_LOG.md current.
- Check estimated spend before every evaluation run.
- Never build features that are not in the current phase.
