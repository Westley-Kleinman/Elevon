// OpenTopography API key + dataset handling with automatic fallback.
//
// KEY FALLBACK
// Free keys are capped (~200 calls/24h). Configure several and the code tries
// them left-to-right, skipping exhausted/blocked ones (401/403/429).
//
//   OPENTOPO_API_KEYS=key1,key2,key3   (preferred)
//   OPENTOPO_API_KEY=key1              (legacy single-key, still supported)
//
// DATASET FALLBACK
// SRTMGL3 only covers 60°S–60°N, so Alaskan and other high-latitude resorts
// return an empty response. When that happens we automatically retry with
// COP30 (Copernicus DEM, 30m, global coverage), which handles the full US
// including Alaska.
//
// Fallback order: SRTMGL3 → COP30

export function getOpenTopoKeys(): string[] {
  const raw =
    process.env.OPENTOPO_API_KEYS ?? process.env.OPENTOPO_API_KEY ?? ''
  return raw
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean)
}

// Ordered list of DEM datasets to try. SRTMGL3 is preferred (90m, well-tested)
// with COP30 as the global fallback (30m, covers Alaska and high latitudes).
const DEM_DATASETS = ['SRTMGL3', 'COP30'] as const
type DemDataset = (typeof DEM_DATASETS)[number]

// Statuses meaning "this key is exhausted/blocked" — retrying with a new key
// may help. Other failures (bad bbox, upstream 5xx) won't be fixed by swapping
// keys, so we don't burn additional quota on them.
const RETRYABLE_STATUS = new Set([401, 403, 429])

export interface DemFetchResult {
  arrayBuffer: ArrayBuffer
  // Which dataset ultimately returned good data.
  dataset: DemDataset
}

// Checks whether an ArrayBuffer looks like a GeoTIFF by inspecting the first
// two magic bytes (little-endian "II" or big-endian "MM").
export function isTiff(buf: ArrayBuffer): boolean {
  const h = new Uint8Array(buf.slice(0, 2))
  return (h[0] === 0x49 && h[1] === 0x49) || (h[0] === 0x4d && h[1] === 0x4d)
}

// Fetches elevation data from OpenTopography, trying:
//   1. Each configured API key for the current dataset.
//   2. If SRTMGL3 returns a non-TIFF (coverage gap), retry with COP30.
//
// Returns a resolved DemFetchResult on success, or throws an Error describing
// the final failure so callers can surface a 502.
export async function fetchDem(bounds: {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}): Promise<DemFetchResult> {
  const keys = getOpenTopoKeys()
  if (keys.length === 0) throw new Error('no OpenTopography API keys configured')

  for (const dataset of DEM_DATASETS) {
    // Try every key for this dataset before giving up on it.
    let allKeysExhausted = false
    let lastKeyError = ''

    for (let i = 0; i < keys.length; i++) {
      const url =
        `https://portal.opentopography.org/API/globaldem?demtype=${dataset}` +
        `&south=${bounds.minLat}&north=${bounds.maxLat}` +
        `&west=${bounds.minLng}&east=${bounds.maxLng}` +
        `&outputFormat=GTiff&API_Key=${keys[i]}`

      const res = await fetch(url)

      if (!res.ok) {
        if (RETRYABLE_STATUS.has(res.status)) {
          // Key exhausted — try the next key for the same dataset.
          const body = await res.text().catch(() => '<unreadable>')
          const more = i + 1 < keys.length
          console.warn(
            `opentopo [${dataset}]: key #${i + 1}/${keys.length} failed (${res.status}); ` +
              `${more ? 'trying next key' : 'all keys exhausted'}: ${body.slice(0, 160)}`,
          )
          lastKeyError = `${res.status}: ${body.slice(0, 100)}`
          if (i + 1 === keys.length) allKeysExhausted = true
          continue
        }
        // Non-retryable HTTP error (4xx other than auth, 5xx).
        const body = await res.text().catch(() => '<unreadable>')
        throw new Error(`OpenTopography ${dataset} HTTP ${res.status}: ${body.slice(0, 200)}`)
      }

      const arrayBuffer = await res.arrayBuffer()

      if (!isTiff(arrayBuffer)) {
        // Empty / non-TIFF body — outside this dataset's coverage. Try the
        // next dataset (e.g. fall from SRTMGL3 to COP30 for Alaska).
        const snippet = new TextDecoder().decode(arrayBuffer.slice(0, 100))
        console.warn(
          `opentopo [${dataset}]: non-TIFF response (${arrayBuffer.byteLength}B) — ` +
            `outside coverage, trying next dataset. Snippet: ${snippet}`,
        )
        break // move to next dataset, don't try more keys for this one
      }

      return { arrayBuffer, dataset }
    }

    if (allKeysExhausted) {
      throw new Error(`all API keys exhausted for ${dataset}: ${lastKeyError}`)
    }
  }

  throw new Error(
    'No elevation data available for this area (tried all datasets: ' +
      DEM_DATASETS.join(', ') +
      ')',
  )
}
