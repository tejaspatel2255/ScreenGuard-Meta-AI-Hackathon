# Meta Model API notes

Documented facts verified from dev.meta.ai documentation.

## 0. Known from the participant guide and docs
- Models through Meta Model API: `muse-spark-1.3`, `muse-spark-1.2`, `sam-3.1`, `muse-voice-transcribe-1.0`, `muse-wonder-1.0`, `muse-image-1.0`. [VERIFIED]
- Open-weights models: Muse Glimmer, Muse Spark Open, Llama-3.2/3.3 series. [VERIFIED]
- Provider route: Groq OpenAI-compatible endpoints with Meta open-weights models (`qwen/qwen3.8-27b` vision and `openai/gpt-oss-120b` text). [VERIFIED in real calls]

## 1. Auth
- Header name and format: `Authorization: Bearer <API_KEY>` [VERIFIED]
- Environment variables: `META_API_KEY`, `GROQ_API_KEY` [VERIFIED]

## 2. Base URL and general format
- Meta API Base URL (`META_API_BASE_URL`): `https://api.meta.ai/v1` [VERIFIED in docs]
- Groq Base URL (`GROQ_BASE_URL`): `https://api.groq.com/openai/v1` [VERIFIED in real calls]
- Style: OpenAI-compatible Chat Completions (`/chat/completions`). [VERIFIED in real calls]
- Segmentation endpoint: `/segmentation` [UNVERIFIED on real endpoint]
- Voice transcribe: `/audio/transcriptions` [UNVERIFIED on real endpoint]

## 3. Muse Spark / Vision Judging Model
- Vision model: `muse-spark-1.3` (Meta API) / `qwen/qwen3.8-27b` (Groq provider) [VERIFIED in real calls]
- Text model: `openai/gpt-oss-120b` [VERIFIED in real calls: latency 2.25s, parsed 3 steps]
- Text input format: OpenAI chat messages list `[{"role": "user", "content": ...}]` [VERIFIED]
- Image input: Yes, accepts base64 data URL (`data:image/png;base64,...` or `data:image/jpeg;base64,...`). [VERIFIED]
- Structured / JSON output: standard `response_format: {"type": "json_object"}`. [VERIFIED]

## 4. SAM 3.1
- Model name: `sam-3.1`
- Input: Image bytes/base64 + prompt text.
- Note: Unverified on live endpoint without credit card payment method; `USE_SAM=false` by default for stability. [UNVERIFIED]

## 5. Muse Voice Transcribe
- Model name: `muse-voice-transcribe-1.0`
- Input: Audio formats (wav, mp3, webm).
- Note: `USE_VOICE=false` by default per project rules. [UNVERIFIED]

## 6. Rate limits
- RPM / TPM: Handled by asynchronous rate limiter with 10s wait ceiling. [VERIFIED]
- HTTP 429: Exponential backoff with `Retry-After`. [VERIFIED in unit tests]

## 7. Pricing
- Input/output token pricing tracked in `config/pricing.json`. [VERIFIED]
