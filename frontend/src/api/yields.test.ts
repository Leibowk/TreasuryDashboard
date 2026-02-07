import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchYieldCurve } from './yields'

const defaultBase = 'http://localhost:8000'

describe('api/yields', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('fetchYieldCurve builds correct URL and returns data on ok response', async () => {
    const mockData = {
      data: [{ term: '1M', rate: 4.35 }, { term: '5Y', rate: 4.24 }],
      display_date: '2025-02-05',
    }
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const result = await fetchYieldCurve('2025-02-05')

    expect(fetchMock).toHaveBeenCalledWith(
      `${defaultBase}/api/yields?date=${encodeURIComponent('2025-02-05')}`
    )
    expect(result).toEqual(mockData)
  })

  it('fetchYieldCurve throws on non-ok response', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    })

    await expect(fetchYieldCurve('2025-02-05')).rejects.toThrow(
      /Failed to load yields: 404 Not Found/
    )
  })
})
