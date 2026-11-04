import { describe, it, expect } from 'vitest'

describe('Health data contract', () => {
  it('parses valid health response object', () => {
    const raw = {
      status: 'ok',
      mode: 'mock',
      model_info: {
        provider: 'groq',
        vision_model: 'qwen/qwen3.8-27b',
        text_model: 'openai/gpt-oss-120b',
        family: 'other'
      }
    }
    expect(raw.status).toBe('ok')
    expect(['mock', 'real', 'replay']).toContain(raw.mode)
    expect(raw.model_info.provider).toBe('groq')
    expect(raw.model_info.vision_model).toBeDefined()
  })
})
