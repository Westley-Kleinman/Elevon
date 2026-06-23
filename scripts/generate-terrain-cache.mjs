// Pre-generate cached terrain meshes for the most-developed US ski resorts so
// the live /api/terrain-mesh route can serve them instantly from disk instead
// of waiting on OpenTopography.
//
// Manual / occasional maintenance task — NOT part of dev or build.
//   Usage:  npm run generate-terrain-cache
//   Needs:  OPENTOPO_API_KEYS (read from the environment, or .env.local, comma-separated)
import { readFileSync, existsSync } from 'fs'
import { readFile, writeFile, mkdir } from 'fs/promises'
import path from 'path'
import { fromArrayBuffer } from 'geotiff'
import { squareBounds } from './lib/geoBounds.mjs'

const SKI_AREAS_PATH = path.resolve('public/data/ski-areas.json')
const TRAILS_DIR = path.resolve('public/data/trails')
const OUTPUT_DIR = path.resolve('public/data/terrain')

const BBOX_PADDING = 0.15 // must match the live route + extraction
const TARGET_GRID = 120
const NODATA_MIN = -1000
const NODATA_MAX = 9000
const TOP_N = 500
const DELAY_MS = 1500

// Load OPENTOPO_API_KEYS from the environment, falling back to a minimal parse of
// .env.local (the live Next.js route gets this auto-loaded; a bare node script
// does not). Expects a comma-separated list of keys.
function resolveApiKeys() {
  let keysString = process.env.OPENTOPO_API_KEYS;
  
  try {
    if (!keysString) {
      const envFile = readFileSync(path.resolve('.env.local'), 'utf-8')
      for (const line of envFile.split(/\r?\n/)) {
        const m = line.match(/^\s*OPENTOPO_API_KEYS\s*=\s*(.*)\s*$/)
        if (m) {
          keysString = m[1].replace(/^["']|["']$/g, '').trim();
          break;
        }
      }
    }
  } catch {
    /* no .env.local — fall through */
  }

  if (keysString) {
    // Split by comma, remove whitespace, and filter out any empties
    return keysString.split(',').map(k => k.trim()).filter(Boolean);
  }
  
  return [];
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// Square bbox from a trail file's rawCoordinates ([lng, lat]) — identical logic
// to boundsFromTrails in the API route.
function boundsFromTrailData(trailData) {
  let minLat = Infinity
  let maxLat = -Infinity
  let minLng = Infinity
  let maxLng = -Infinity
  for (const run of trailData.runs ?? []) {
    for (const [lng, lat] of run.rawCoordinates ?? []) {
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) continue
      if (lat < minLat) minLat = lat
      if (lat > maxLat) maxLat = lat
      if (lng < minLng) minLng = lng
      if (lng > maxLng) maxLng = lng
    }
  }
  if (!Number.isFinite(minLat) || !Number.isFinite(minLng)) return null
  return squareBounds(minLat, maxLat, minLng, maxLng, BBOX_PADDING)
}

// Ordered DEM datasets to try. SRTMGL3 covers 60S-60N; COP30 is global and
// handles Alaska + other high-latitude resorts that SRTMGL3 misses.
const DEM_DATASETS = ['SRTMGL3', 'COP30']

function isTiff(arrayBuffer) {
  const h = new Uint8Array(arrayBuffer.slice(0, 2))
  return (h[0] === 0x49 && h[1] === 0x49) || (h[0] === 0x4d && h[1] === 0x4d)
}

// Fetch + parse + downsample, mirroring the live terrain-mesh route exactly.
// Tries SRTMGL3 first; falls back to COP30 for areas outside SRTM coverage.
async function generateTerrain(bounds, apiKeys) {
  // currentKeyIndex is shared across calls by the caller and passed as an
  // object so we can mutate it here on exhaustion.
  let arrayBuffer = null
  let usedDataset = null

  for (const dataset of DEM_DATASETS) {
    // Try every key for this dataset.
    let gotCoverage = false
    for (let ki = 0; ki < apiKeys.length; ki++) {
      const url =
        `https://portal.opentopography.org/API/globaldem?demtype=${dataset}` +
        `&south=${bounds.minLat}&north=${bounds.maxLat}` +
        `&west=${bounds.minLng}&east=${bounds.maxLng}` +
        `&outputFormat=GTiff&API_Key=${apiKeys[ki]}`

      const res = await fetch(url)
      if (!res.ok) {
        const body = await res.text().catch(() => '<unreadable>')
        // Rate-limit errors bubble up so the outer loop can rotate keys.
        throw new Error(`OpenTopography ${res.status}: ${body.slice(0, 200)}`)
      }

      const buf = await res.arrayBuffer()
      if (!isTiff(buf)) {
        // Outside dataset coverage — try next dataset.
        const text = new TextDecoder().decode(buf.slice(0, 100))
        console.warn(`  [${dataset}] non-TIFF (${buf.byteLength}B), trying next dataset. Snippet: ${text}`)
        break
      }

      arrayBuffer = buf
      usedDataset = dataset
      gotCoverage = true
      break
    }

    if (gotCoverage) break
  }

  if (!arrayBuffer) {
    throw new Error(`non-GeoTIFF response (0B): no coverage in any dataset`)
  }

  if (usedDataset !== 'SRTMGL3') {
    console.log(`  [fallback: ${usedDataset}]`)
  }

  const tiff = await fromArrayBuffer(arrayBuffer)
  const image = await tiff.getImage()
  const srcWidth = image.getWidth()
  const srcHeight = image.getHeight()
  const rasters = await image.readRasters()
  const band = rasters[0]

  let min = Infinity
  for (let i = 0; i < band.length; i++) {
    const v = band[i]
    if (v >= NODATA_MIN && v <= NODATA_MAX && v < min) min = v
  }
  if (!Number.isFinite(min)) throw new Error('no valid elevation data')

  const cleanAt = (x, y) => {
    const v = band[y * srcWidth + x]
    return v >= NODATA_MIN && v <= NODATA_MAX ? v : min
  }

  const gridWidth = Math.min(TARGET_GRID, srcWidth)
  const gridHeight = Math.min(TARGET_GRID, srcHeight)
  const elevations = new Array(gridWidth * gridHeight)
  let outMin = Infinity
  let outMax = -Infinity

  for (let gy = 0; gy < gridHeight; gy++) {
    const sy =
      gridHeight === 1 ? 0 : Math.round((gy / (gridHeight - 1)) * (srcHeight - 1))
    for (let gx = 0; gx < gridWidth; gx++) {
      const sx =
        gridWidth === 1 ? 0 : Math.round((gx / (gridWidth - 1)) * (srcWidth - 1))
      const v = cleanAt(sx, sy)
      elevations[gy * gridWidth + gx] = v
      if (v < outMin) outMin = v
      if (v > outMax) outMax = v
    }
  }

  return {
    gridWidth,
    gridHeight,
    elevations,
    minElevation: outMin,
    maxElevation: outMax,
    usedBounds: bounds,
  }
}

async function main() {
  const start = Date.now()

  const apiKeys = resolveApiKeys()
  if (apiKeys.length === 0) {
    console.error(
      'OPENTOPO_API_KEYS is not set (checked process.env and .env.local). Aborting.',
    )
    process.exit(1)
  }

  let currentKeyIndex = 0;
  console.log(`Loaded ${apiKeys.length} API keys for fallback rotation.`);

  const skiAreas = JSON.parse(readFileSync(SKI_AREAS_PATH, 'utf-8'))

  // Region filter: pass --europe, --us, --all, or --countries=FR,CH,AT etc.
  // Default (no flag) is US-only for backwards compatibility.
  const EUROPE_COUNTRIES = new Set([
    'FR','CH','AT','DE','IT','NO','SE','FI','ES','PL','CZ','SK','RO',
    'SI','HR','BG','GB','IE','NL','BE','LU','LI','AD','BA','RS','MK',
    'ME','AL','GR','PT','IS','EE','LV','LT','BY','UA','MD',
  ])
  const arg = process.argv.find(a => a.startsWith('--'))
  let countryFilter = null // null = all countries
  let regionLabel = 'all countries'
  if (!arg || arg === '--us') {
    countryFilter = new Set(['US'])
    regionLabel = 'US'
  } else if (arg === '--europe') {
    countryFilter = EUROPE_COUNTRIES
    regionLabel = 'Europe'
  } else if (arg === '--all') {
    countryFilter = null
    regionLabel = 'all countries'
  } else if (arg.startsWith('--countries=')) {
    countryFilter = new Set(arg.replace('--countries=', '').split(','))
    regionLabel = arg.replace('--countries=', '')
  }

  // Mountains that have a trail file, filtered by region, sorted by run count.
  const eligible = []
  for (const m of skiAreas) {
    if (countryFilter && !countryFilter.has(m.country)) continue
    const trailPath = path.join(TRAILS_DIR, `${m.id}.json`)
    if (!existsSync(trailPath)) continue
    let trailData
    try {
      trailData = JSON.parse(readFileSync(trailPath, 'utf-8'))
    } catch {
      continue
    }
    const runCount = Array.isArray(trailData.runs) ? trailData.runs.length : 0
    if (runCount === 0) continue
    eligible.push({ mountain: m, runCount })
  }

  console.log(
    `Eligible pool (${regionLabel}, has trail data): ${eligible.length}`,
  )

  eligible.sort((a, b) => b.runCount - a.runCount)
  const batch = eligible.slice(0, TOP_N)
  console.log(
    `Generating terrain cache for top ${batch.length} resorts by run count...\n`,
  )

  await mkdir(OUTPUT_DIR, { recursive: true })

  let succeeded = 0
  let failed = 0
  let skipped = 0

  for (let i = 0; i < batch.length; i++) {
    const { mountain, runCount } = batch[i]
    const outPath = path.join(OUTPUT_DIR, `${mountain.id}.json`)

    // 1. Skip if already cached
    if (existsSync(outPath)) {
      skipped++
      continue 
    }

    try {
      const trailData = JSON.parse(
        await readFile(path.join(TRAILS_DIR, `${mountain.id}.json`), 'utf-8'),
      )
      const bounds = boundsFromTrailData(trailData)
      if (!bounds) throw new Error('could not derive bounds from trail data')

      // Pass keys from current index onward so generateTerrain can rotate
      // internally on per-key rate limits within a dataset attempt.
      const terrain = await generateTerrain(bounds, apiKeys.slice(currentKeyIndex))
      await writeFile(outPath, JSON.stringify(terrain))
      
      succeeded++
      console.log(`  + Cached ${mountain.name} (${mountain.id})`)
      
    } catch (err) {
      // Handle Rate Limits by rotating keys
      if (err.message.includes('API maximum rate limit reached') || err.message.includes('401')) {
        console.log(`\n⚠️ OpenTopography limit hit on Key ${currentKeyIndex + 1}.`)
        currentKeyIndex++

        if (currentKeyIndex < apiKeys.length) {
          console.log(`🔄 Switching to Key ${currentKeyIndex + 1} and retrying ${mountain.name}...`)
          i-- // retry this mountain
          await sleep(DELAY_MS)
          continue
        } else {
          console.log('\n🛑 All provided API keys are exhausted. Aborting remaining fetches.')
          break
        }
      }

      // If it's a regular error, log it and move to the next mountain
      failed++
      console.error(
        `  ! ${mountain.name} (${mountain.id}, ${runCount} runs): ${err.message}`,
      )
    }

    if ((i + 1) % 25 === 0) {
      console.log(`Generated ${i + 1}/${batch.length}...`)
    }

    // Be polite to OpenTopography — fixed delay between requests.
    if (i < batch.length - 1) await sleep(DELAY_MS)
  }

  const elapsed = ((Date.now() - start) / 1000).toFixed(1)
  console.log('\n--- Summary ---')
  console.log(`Already Cached: ${skipped}`)
  console.log(`Newly Cached:   ${succeeded}`)
  console.log(`Failed:         ${failed}`)
  console.log(`Attempted:      ${batch.length} of ${eligible.length} eligible`)
  console.log(`Total time:     ${elapsed}s`)
  
  process.exit(0)
}

main().catch((err) => {
  console.error('Fatal error:', err)
  process.exit(1)
})