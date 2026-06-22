// OpenTopography API key handling with automatic fallback.
//
// The free OpenTopography keys are capped (e.g. 200 calls / 24h). To stay up
// when one key is exhausted, configure several keys and let requests fall
// through to the next one on a rate-limit/auth failure.
//
// Configure via .env.local:
//   OPENTOPO_API_KEYS=key1,key2,key3      (preferred — tried left-to-right)
//   OPENTOPO_API_KEY=key1                 (legacy single-key, still supported)

export function getOpenTopoKeys(): string[] {
  const raw =
    process.env.OPENTOPO_API_KEYS ?? process.env.OPENTOPO_API_KEY ?? ''
  return raw
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean)
}

// Statuses meaning "this key is exhausted/blocked" — worth retrying with the
// next key. Other failures (bad bbox, upstream 5xx) won't be fixed by swapping
// keys, so we don't burn additional quota retrying them.
const RETRYABLE_STATUS = new Set([401, 403, 429])

export interface DemFetchResult {
  res: Response
  // Index of the key that produced `res`, or -1 when every key was exhausted.
  keyIndex: number
  attempts: number
}

// Fetches a DEM by trying each configured key in order. `buildUrl` receives a
// key and returns the full OpenTopography request URL.
//
// Returns null only when NO keys are configured. Otherwise returns the first
// successful response, the first non-retryable failure, or (if all keys are
// rate-limited) the last failing response so the caller can surface a 502.
export async function fetchDemWithKeyFallback(
  buildUrl: (key: string) => string,
): Promise<DemFetchResult | null> {
  const keys = getOpenTopoKeys()
  if (keys.length === 0) return null

  let last: Response | null = null

  for (let i = 0; i < keys.length; i++) {
    const res = await fetch(buildUrl(keys[i]))

    if (res.ok) return { res, keyIndex: i, attempts: i + 1 }

    // A failure a different key can't fix — hand it straight back unconsumed.
    if (!RETRYABLE_STATUS.has(res.status)) {
      return { res, keyIndex: i, attempts: i + 1 }
    }

    // Rate-limited / unauthorized: log (consuming the body) and try the next.
    last = res
    const body = await res.text().catch(() => '<unreadable>')
    const more = i + 1 < keys.length
    console.warn(
      `opentopo: key #${i + 1}/${keys.length} failed (${res.status}); ` +
        `${more ? 'falling back to next key' : 'no keys left'}: ${body.slice(0, 160)}`,
    )
  }

  return last ? { res: last, keyIndex: -1, attempts: keys.length } : null
}
