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

// Fetch + parse + downsample, mirroring the live terrain-mesh route exactly.
async function generateTerrain(bounds, apiKey) {
  const url =
    `https://portal.opentopography.org/API/globaldem?demtype=SRTMGL3` +
    `&south=${bounds.minLat}&north=${bounds.maxLat}` +
    `&west=${bounds.minLng}&east=${bounds.maxLng}` +
    `&outputFormat=GTiff&API_Key=${apiKey}`

  const res = await fetch(url)
  if (!res.ok) {
    const body = await res.text().catch(() => '<unreadable>')
    throw new Error(`OpenTopography ${res.status}: ${body.slice(0, 200)}`)
  }

  const arrayBuffer = await res.arrayBuffer()
  const head = new Uint8Array(arrayBuffer.slice(0, 2))
  const isTiff =
    (head[0] === 0x49 && head[1] === 0x49) ||
    (head[0] === 0x4d && head[1] === 0x4d)
  if (!isTiff) {
    const text = new TextDecoder().decode(arrayBuffer.slice(0, 200))
    throw new Error(`non-GeoTIFF response (${arrayBuffer.byteLength}B): ${text}`)
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

  // US mountains that also have a trail file, with their run count as a
  // popularity proxy.
  const eligible = []
  for (const m of skiAreas) {
    if (m.country !== 'US') continue
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
    `Eligible pool (country === 'US' AND has trail data): ${eligible.length}`,
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

      // Use the currently active API key
      const terrain = await generateTerrain(bounds, apiKeys[currentKeyIndex])
      await writeFile(outPath, JSON.stringify(terrain))
      
      succeeded++
      console.log(`  + Cached ${mountain.name} (${mountain.id})`)
      
    } catch (err) {
      // 2. Handle Rate Limits by rotating keys
      if (err.message.includes('API maximum rate limit reached') || err.message.includes('401')) {
        console.log(`\n⚠️ OpenTopography limit hit on Key ${currentKeyIndex + 1}.`);
        currentKeyIndex++;

        if (currentKeyIndex < apiKeys.length) {
          console.log(`🔄 Switching to Key ${currentKeyIndex + 1} and retrying ${mountain.name}...`);
          // Decrement 'i' so the loop repeats this exact mountain on the next pass
          i--; 
          await sleep(DELAY_MS); // Be polite before retrying
          continue; 
        } else {
          console.log('\n🛑 All provided API keys are exhausted. Aborting remaining fetches.')
          break // Break the loop so the summary prints and the script exits
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