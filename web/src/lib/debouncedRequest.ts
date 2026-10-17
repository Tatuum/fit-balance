/**
 * Runs `request` after `delayMs`, then hands its result (or error) to
 * `onSuccess` / `onError` — unless the returned cancel function was called
 * first. Cancelling clears the pending timer *and* makes a request that is
 * already in flight report nothing, so a slow older answer can never
 * overwrite a newer one. Meant to be returned straight from a useEffect, so
 * React's cleanup cancels the previous run before starting the next.
 */
export function debouncedRequest<T>(
  request: () => Promise<T>,
  onSuccess: (result: T) => void,
  onError: (error: unknown) => void,
  delayMs = 500,
): () => void {
  let cancelled = false
  const handle = setTimeout(() => {
    request().then(
      (result) => {
        if (!cancelled) onSuccess(result)
      },
      (error) => {
        if (!cancelled) onError(error)
      },
    )
  }, delayMs)
  return () => {
    cancelled = true
    clearTimeout(handle)
  }
}
