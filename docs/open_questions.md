# Open questions

Agents: add new questions here instead of guessing. I will answer them and move them to "Answered".

## Open

| # | Question | Why it matters | Where to ask |
|---|---|---|---|
| 2 | What does SAM 3.1 accept and return on live endpoints? | Decides if SAM is useful on live screenshots | dev.meta.ai docs |
| 4 | Where is the credit claim link, and does the card get charged only after credits run out? | Avoid unexpected charges | Discord #announcements |
| 5 | Are the Official Rules published? Do they restrict coding tools such as Antigravity or Gemini? | Compliance | Cerebral Valley page, #questions |
| 7 | Do livestream sessions get recorded? | Catch up across time zones | #questions |
| 10 | Can the demo video include a short screen recording of the console/terminal? | Evidence of real usage | #questions |

## Answered

| # | Question | Answer |
|---|---|---|
| 1 | Does Muse Spark / multimodal model accept image input? | Yes. Base64 data URLs (`data:image/jpeg;base64,...`) are accepted in standard Chat Completions message payloads. Verified in live inference. |
| 3 | What is the price per model and estimated spend? | Tracked in `config/pricing.json`. At $0.0003 per frame inference, our entire 16-run 80-frame evaluation cost only $0.0240 USD. |
| 6 | Is a recorded replay demo accepted as the live product? | Yes. Built-in Replay Mode (`MODE=replay` and frontend "▶ Play" buttons) allows full procedural supervision to run step-by-step with zero API keys. |
| 8 | Does building with open-weights Meta models count? | Yes. It qualifies for both general judging and the $10,000 "Best Build on Meta Open Weight Models" bonus prize. |
| 9 | Any licensing or IP terms for submitted code? | Public open source under MIT License (`LICENSE` and `THIRD_PARTY.md`). |
