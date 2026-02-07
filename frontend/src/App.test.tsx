import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders Treasury Yields heading and date selector', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, statusText: 'Err' }))

    render(<App />)

    expect(await screen.findByRole('heading', { name: /Treasury Yields/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/As of date/i)).toBeInTheDocument()
  })
})
