import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { debouncedRequest } from './debouncedRequest'

// A promise the test resolves or rejects by hand, to control when "the
// network" answers.
function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (error: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('debouncedRequest', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('waits for the delay before sending the request', () => {
    const request = vi.fn(() => Promise.resolve('ok'))
    debouncedRequest(request, vi.fn(), vi.fn(), 500)

    vi.advanceTimersByTime(499)
    expect(request).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(request).toHaveBeenCalledTimes(1)
  })

  it('passes the result to onSuccess', async () => {
    const onSuccess = vi.fn()
    debouncedRequest(() => Promise.resolve('advice'), onSuccess, vi.fn())

    await vi.advanceTimersByTimeAsync(500)
    expect(onSuccess).toHaveBeenCalledWith('advice')
  })

  it('passes a failure to onError', async () => {
    const onError = vi.fn()
    const failure = new Error('boom')
    debouncedRequest(() => Promise.reject(failure), vi.fn(), onError)

    await vi.advanceTimersByTimeAsync(500)
    expect(onError).toHaveBeenCalledWith(failure)
  })

  it('sends nothing if cancelled before the delay passes', async () => {
    const request = vi.fn(() => Promise.resolve('ok'))
    const cancel = debouncedRequest(request, vi.fn(), vi.fn())

    cancel()
    await vi.advanceTimersByTimeAsync(1000)
    expect(request).not.toHaveBeenCalled()
  })

  it('ignores a successful answer that arrives after cancelling', async () => {
    const pending = deferred<string>()
    const onSuccess = vi.fn()
    const cancel = debouncedRequest(() => pending.promise, onSuccess, vi.fn())

    await vi.advanceTimersByTimeAsync(500) // request is now in flight
    cancel()
    pending.resolve('stale')
    await vi.advanceTimersByTimeAsync(0)

    expect(onSuccess).not.toHaveBeenCalled()
  })

  it('ignores a failure that arrives after cancelling', async () => {
    const pending = deferred<string>()
    const onError = vi.fn()
    const cancel = debouncedRequest(() => pending.promise, vi.fn(), onError)

    await vi.advanceTimersByTimeAsync(500)
    cancel()
    pending.reject(new Error('late'))
    await vi.advanceTimersByTimeAsync(0)

    expect(onError).not.toHaveBeenCalled()
  })

  it('lets only the newest of two overlapping runs report, even if the older answers last', async () => {
    const older = deferred<string>()
    const newer = deferred<string>()
    const seen: string[] = []

    const cancelOlder = debouncedRequest(() => older.promise, (r) => seen.push(r), vi.fn())
    await vi.advanceTimersByTimeAsync(500) // older is in flight
    cancelOlder() // what React's effect cleanup does before the next run
    debouncedRequest(() => newer.promise, (r) => seen.push(r), vi.fn())
    await vi.advanceTimersByTimeAsync(500) // newer is in flight

    newer.resolve('new')
    await vi.advanceTimersByTimeAsync(0)
    older.resolve('old') // slow answer arrives last
    await vi.advanceTimersByTimeAsync(0)

    expect(seen).toEqual(['new'])
  })
})
