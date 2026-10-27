# Meta Model API notes

Fill this file from the OFFICIAL docs (Docs overview, Quickstart, Model list, API fundamentals, API cookbook). Coding agents must read it and must never guess an endpoint, header, model name or request format. Anything still empty means: stop and ask.

## 0. Known from the participant guide (not from the API docs)

- Models through Meta Model API: Muse Spark series, Muse Wonder, Muse Image, Muse Voice Transcribe, SAM 3.1.
- Open-weights models: Muse Glimmer, Muse Spark Open.
- Credits: $150 per accepted participant. A credit card is required to make API calls. Billing page has a spend limit notification only.
- Baseten route for Muse Spark Open: use model name meta-models/muse-spark-open-1026 (the Baseten docs show meta-models/muse-spark-open). Baseten docs mention sending images and audio to Muse Spark Open.

## 1. Auth

- Where to get the API key:
- Header name and format:
- Environment variable we use: META_API_KEY

## 2. Base URL and general format

- Base URL (META_API_BASE_URL):
- Style (chat completions, custom, other):
- Streaming needed? (we do not plan to stream)
- Common error codes and their meaning:

## 3. Muse Spark

- Exact model name to use:
- Text input format:
- Image input: accepted? (yes or no) Format (base64, URL, multipart)? Max size and dimensions?
- Structured or JSON output option available? How to enable:
- Max output tokens, context length:
- Example request (paste from docs):
- Example response (paste from docs):

## 4. SAM 3.1

- Exact model name and endpoint:
- Input: image format, prompt types (text, points, boxes)?
- Output: masks, boxes, scores? Format and coordinates (pixels or normalized)?
- Limits (image size, number of prompts per call):
- Example request and response (paste from docs):

## 5. Muse Voice Transcribe

- Exact model name and endpoint:
- Input audio formats (webm, wav, mp3), max length and size:
- Output format:
- Example request and response (paste from docs):

## 6. Rate limits

- Requests per minute:
- Tokens per minute:
- Behaviour on 429 (Retry-After header?):

## 7. Pricing and credits

| Model | Unit | Price per unit | Notes |
|---|---|---|---|
| Muse Spark input | per 1M tokens | | |
| Muse Spark output | per 1M tokens | | |
| Image input cost | per image or per token | | |
| SAM 3.1 | per call or per image | | |
| Muse Voice Transcribe | per minute | | |

- How many calls does $150 cover for our flow (estimate):
- Where the credit claim link is, and the date I claimed:

## 8. Muse Code (optional)

- Is it a CLI, IDE tool or API?
- Access steps:
- Useful recipes from the Muse Code cookbook:

## 9. Baseten route (optional)

- Credits approved? (yes or no)
- Endpoint and request format:
- Image input format:
