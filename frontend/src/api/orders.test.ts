import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createOrder, fetchOrders, updateOrderStatus } from './orders'

const defaultBase = 'http://localhost:8000'

describe('api/orders', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('fetchOrders builds correct URL and returns data on ok response', async () => {
    const mockData = { orders: [], total: 0 }
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const result = await fetchOrders(5, 10)

    expect(fetchMock).toHaveBeenCalledWith(
      `${defaultBase}/api/orders?offset=5&limit=10`
    )
    expect(result).toEqual(mockData)
  })

  it('fetchOrders throws on non-ok response', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    })

    await expect(fetchOrders(0, 10)).rejects.toThrow(
      /Failed to load orders: 500 Internal Server Error/
    )
  })

  it('createOrder sends POST with body and returns order on ok', async () => {
    const mockOrder = {
      id: 1,
      date: '2025-02-05',
      term: '5Y',
      amount: 1000,
      yield_pct: 4.24,
      status: 'Pending',
      created_at: '2025-02-05T12:00:00Z',
    }
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockOrder),
    })

    const result = await createOrder('5Y', 1000)

    expect(fetchMock).toHaveBeenCalledWith(`${defaultBase}/api/order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ term: '5Y', amount: 1000 }),
    })
    expect(result).toEqual(mockOrder)
  })

  it('createOrder throws with detail message when response has detail', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      text: () => Promise.resolve(JSON.stringify({ detail: 'No yield for 5Y' })),
    })

    await expect(createOrder('5Y', 1000)).rejects.toThrow('No yield for 5Y')
  })

  it('updateOrderStatus sends PATCH and returns order on ok', async () => {
    const mockOrder = {
      id: 1,
      date: '2025-02-05',
      term: '5Y',
      amount: 1000,
      yield_pct: 4.24,
      status: 'Settled',
      created_at: '2025-02-05T12:00:00Z',
    }
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockOrder),
    })

    const result = await updateOrderStatus(1, 'Settled')

    expect(fetchMock).toHaveBeenCalledWith(`${defaultBase}/api/orders/1`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Settled' }),
    })
    expect(result).toEqual(mockOrder)
  })
})
