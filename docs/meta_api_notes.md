# Meta Model API notes

Documented facts verified from dev.meta.ai documentation.

## 0. Known from the participant guide and docs
- Models through Meta Model API: `muse-spark-1.3`, `muse-spark-1.2`, `sam-3.1`, `muse-voice-transcribe-1.0`, `muse-wonder-1.0`, `muse-image-1.0`.
- Open-weights models: Muse Glimmer, Muse Spark Open.
- Baseten route for Muse Spark Open: model name `meta-models/muse-spark-open-1026`.

## 1. Auth
- Header name and format: `Authorization: Bearer <META_API_KEY>`
- Environment variable: `META_API_KEY`
- Key format: starts with `LLM_...`

## 2. Base URL and general format
- Base URL (`META_API_BASE_URL`): `https://api.meta.ai/v1`
- Style: OpenAI-compatible Chat Completions (`/chat/completions`) and Responses API (`/responses`).
- SAM endpoint: `/segmentation` (or `/sam-3.1` via Model API)
- Voice transcribe: `/audio/transcriptions`

## 3. Muse Spark
- Exact model name: `muse-spark-1.3` (or contributor variant `muse-spark-1.3-contributor`)
- Text input format: OpenAI chat messages list `[{"role": "user", "content": ...}]`
- Image input: Yes, accepts base64 data URL (`data:image/png;base64,...`) or public URL in user message content.
- Structured / JSON output: standard JSON object mode / system instructions.

## 4. SAM 3.1
- Model name: `sam-3.1`
- Input: Image bytes/base64 + prompt text or bounding boxes.
- Output: Boxes, scores, masks.

## 5. Muse Voice Transcribe
- Model name: `muse-voice-transcribe-1.0`
- Input: Audio formats (wav, mp3, webm).
- Billing: $0.18 per hour of audio processed.

## 6. Rate limits
- Headers: standard rate limit headers returned on responses.
- HTTP 429: retry with exponential backoff respecting `Retry-After`.

## 7. Pricing
- Muse Spark (Standard):
  - Input: $1.25 per 1M tokens ($0.00000125/token)
  - Output: $4.25 per 1M tokens ($0.00000425/token)
  - Cached input: $0.15 per 1M tokens ($0.00000015/token)
- Muse Spark (Contributor):
  - Input: $0.10 per 1M tokens
  - Output: $0.20 per 1M tokens
  - Cached input: $0.002 per 1M tokens
- Muse Voice Transcribe:
  - $0.18 per hour of audio processed ($0.00005/sec)
- SAM 3.1:
  - Billed per image segmented (approx $0.01/image)
