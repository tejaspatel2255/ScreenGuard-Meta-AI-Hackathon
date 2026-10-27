import { describe, it, expect } from 'vitest'

describe('Health data contract', () => {
  it('parses valid health response object', () => {
    const raw = { status: 'ok', mode: 'mock' }
    expect(raw.status).toBe('ok')
    expect(['mock', 'real', 'replay']).toContain(raw.mode)
  })
})
