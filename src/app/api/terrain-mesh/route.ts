import { NextResponse } from 'next/server'
import { fromArrayBuffer } from 'geotiff'
import { squareBounds } from '@/lib/geoBounds'
import { getOpenTopoKeys, fetchDemWithKeyFallback } from '@/lib/opentopo'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const NODATA_MIN = -1000
const NODATA_MAX = 9000
const TARGET_GRID = 120

const TRAIL_BBOX_PADDING = 0.15
// Half-size (in degrees) of the box built around a bare lat/lng center point
// when no trail footprint is available. ~0.04 deg ≈ a few km per side.
const CENTER_BBOX_PADDING = 0.04

interface TrailLine {
  difficulty: string
  rawCoordinates: number[][]
}

interface Bounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

interface TerrainResponse {
  gridWidth: number
  gridHeight: number
  elevations: number[]
  minElevation: number
  maxElevation: number
  trails: TrailLine[] | null
  usedBounds: Bounds
}

// Compute a SQUARE (in true physical terms) bounding box from all trail
// rawCoordinates ([lng, lat]), padded by `padding`. Shares the exact squaring
// math (src/lib/geoBounds.ts) with the extraction script so the 2D and 3D
// previews cover the identical geographic area. Returns null with no points.
function boundsFromTrails(
  trails: TrailLine[] | null,
  padding: number = TRAIL_BBOX_PADDING,
): Bounds | null {
  if (!trails || trails.length === 0) return null

  let minLat = Infinity
  let maxLat = -Infinity
  let minLng = Infinity
  let maxLng = -Infinity

  for (const trail of trails) {
    for (const [lng, lat] of trail.rawCoordinates) {
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) continue
      if (lat < minLat) minLat = lat
      if (lat > maxLat) maxLat = lat
      if (lng < minLng) minLng = lng
      if (lng > maxLng) maxLng = lng
    }
  }

  if (!Number.isFinite(minLat) || !Number.isFinite(minLng)) return null

  return squareBounds(minLat, maxLat, minLng, maxLng, padding)
}

// Fetch a static JSON asset from public/ over HTTP against the current
// deployment origin. We deliberately avoid `fs` here: on Vercel the public/
// directory is served as CDN assets and is NOT present on the serverless
// function's filesystem, and dynamically-named files are never bundled. Going
// through the asset URL works identically in local dev and on Vercel.
async function fetchPublicJson<T>(origin: string, assetPath: string): Promise<T | null> {
  try {
    const res = await fetch(`${origin}${assetPath}`)
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

// Read a pre-generated terrain cache file for a mountain, if present. Shape
// matches the live response minus `trails` (those come from the trail file).
async function loadTerrainCache(
  origin: string,
  mountainId: string,
): Promise<Omit<TerrainResponse, 'trails'> | null> {
  if (!/^[a-zA-Z0-9_-]+$/.test(mountainId)) return null
  const parsed = await fetchPublicJson<Omit<TerrainResponse, 'trails'>>(
    origin,
    `/data/terrain/${mountainId}.json`,
  )
  if (!parsed || !Array.isArray(parsed.elevations) || !parsed.usedBounds) return null
  return parsed
}

// Load raw [lng, lat] trail geometry for a mountain, if its trail file exists.
// Returns null when the file is missing or unreadable. mountainId is validated
// against a strict charset to prevent path traversal.
async function loadTrails(
  origin: string,
  mountainId: string,
): Promise<TrailLine[] | null> {
  if (!/^[a-zA-Z0-9_-]+$/.test(mountainId)) return null
  const parsed = await fetchPublicJson<{
    runs?: { difficulty: string; rawCoordinates?: number[][] }[]
  }>(origin, `/data/trails/${mountainId}.json`)
  if (!parsed?.runs) return null
  return parsed.runs
    .filter(
      (run) => Array.isArray(run.rawCoordinates) && run.rawCoordinates.length > 1,
    )
    .map((run) => ({
      difficulty: run.difficulty,
      rawCoordinates: run.rawCoordinates as number[][],
    }))
}

export async function GET(request: Request) {
  try {
    const reqUrl = new URL(request.url)
    const { searchParams } = reqUrl
    // Origin for fetching our own static assets. Prefer the proxy-forwarded host
    // (correct on Vercel behind its edge) and fall back to the request URL.
    const forwardedHost = request.headers.get('x-forwarded-host') ?? request.headers.get('host')
    const forwardedProto = request.headers.get('x-forwarded-proto') ?? reqUrl.protocol.replace(':', '')
    const origin = forwardedHost ? `${forwardedProto}://${forwardedHost}` : reqUrl.origin
    const minLat = Number(searchParams.get('minLat'))
    const maxLat = Number(searchParams.get('maxLat'))
    const minLng = Number(searchParams.get('minLng'))
    const maxLng = Number(searchParams.get('maxLng'))
    const mountainId = searchParams.get('mountainId')

    if (getOpenTopoKeys().length === 0) {
      console.error(
        'terrain-mesh: no OpenTopography API keys configured (set OPENTOPO_API_KEYS)',
      )
      return NextResponse.json(
        { error: 'Elevation service is not configured.' },
        { status: 500 },
      )
    }

    // Optional frontend-tunable padding around the trail footprint. Clamp to a
    // sane [0, 1] range; fall back to the default when missing/invalid.
    const paddingParam = Number(searchParams.get('padding'))
    const padding =
      searchParams.get('padding') !== null && Number.isFinite(paddingParam)
        ? Math.max(0, Math.min(1, paddingParam))
        : TRAIL_BBOX_PADDING

    // Load trails so we can derive the real bounding box from the resort's
    // actual footprint when a trail file exists.
    const trails = mountainId ? await loadTrails(origin, mountainId) : null
    const trailBounds = boundsFromTrails(trails, padding)

    // Fast path: pre-generated cache. Only for the trail-footprint box at the
    // DEFAULT padding (a custom padding slider value changes the requested area,
    // so it must re-fetch live). Trails are merged back in from the trail file.
    const usingDefaultPadding =
      searchParams.get('padding') === null ||
      Math.abs(padding - TRAIL_BBOX_PADDING) < 1e-9
    if (mountainId && trailBounds && usingDefaultPadding) {
      const cached = await loadTerrainCache(origin, mountainId)
      if (cached) {
        return NextResponse.json({ ...cached, trails })
      }
    }

    const lat = Number(searchParams.get('lat'))
    const lng = Number(searchParams.get('lng'))
    const centerValid =
      searchParams.get('lat') !== null &&
      searchParams.get('lng') !== null &&
      Number.isFinite(lat) &&
      Number.isFinite(lng)

    const paramBoxValid =
      searchParams.get('minLat') !== null &&
      searchParams.get('maxLat') !== null &&
      searchParams.get('minLng') !== null &&
      searchParams.get('maxLng') !== null &&
      [minLat, maxLat, minLng, maxLng].every((v) => Number.isFinite(v))

    // Bounding-box priority:
    //   a. trail-file footprint  -> terrain + draped trails
    //   b. lat/lng center point  -> terrain only (no trails)
    //   c. explicit min/max box  -> terrain only (mainly the test page)
    //   d. none of the above     -> 400
    let usedBounds: Bounds | null = null
    if (trailBounds) {
      usedBounds = trailBounds
    } else if (centerValid) {
      usedBounds = {
        minLat: lat - CENTER_BBOX_PADDING,
        maxLat: lat + CENTER_BBOX_PADDING,
        minLng: lng - CENTER_BBOX_PADDING,
        maxLng: lng + CENTER_BBOX_PADDING,
      }
    } else if (paramBoxValid) {
      usedBounds = { minLat, maxLat, minLng, maxLng }
    }

    if (!usedBounds) {
      return NextResponse.json(
        {
          error:
            'Provide a mountainId with trail data, a lat/lng center, or an explicit min/max box.',
        },
        { status: 400 },
      )
    }

    // Only return draped trails when the box came from the trail footprint;
    // the center/param fallbacks have no trail geometry to drape.
    const responseTrails = trailBounds ? trails : null

    const demResult = await fetchDemWithKeyFallback(
      (key) =>
        `https://portal.opentopography.org/API/globaldem?demtype=SRTMGL3` +
        `&south=${usedBounds.minLat}&north=${usedBounds.maxLat}` +
        `&west=${usedBounds.minLng}&east=${usedBounds.maxLng}` +
        `&outputFormat=GTiff&API_Key=${key}`,
    )

    if (!demResult || !demResult.res.ok) {
      const status = demResult?.res.status ?? 'no-keys'
      const body = demResult
        ? await demResult.res.text().catch(() => '<unreadable>')
        : ''
      console.error(
        `terrain-mesh: OpenTopography request failed after ${demResult?.attempts ?? 0} key attempt(s) (${status}):`,
        body,
      )
      return NextResponse.json(
        { error: 'Failed to retrieve elevation data.' },
        { status: 502 },
      )
    }

    const demRes = demResult.res
    const arrayBuffer = await demRes.arrayBuffer()

    // Guard against non-GeoTIFF payloads (OpenTopography occasionally returns a
    // 200/204 with an empty or text body, e.g. outside SRTM's 60N/60S coverage).
    const head = new Uint8Array(arrayBuffer.slice(0, 2))
    const isTiff =
      (head[0] === 0x49 && head[1] === 0x49) ||
      (head[0] === 0x4d && head[1] === 0x4d)
    if (!isTiff) {
      const text = new TextDecoder().decode(arrayBuffer.slice(0, 600))
      console.error(
        `terrain-mesh: non-GeoTIFF response (${demRes.status}, ${arrayBuffer.byteLength} bytes):`,
        text,
      )
      return NextResponse.json(
        { error: 'No elevation data available for this area.' },
        { status: 502 },
      )
    }

    const tiff = await fromArrayBuffer(arrayBuffer)
    const image = await tiff.getImage()
    const srcWidth = image.getWidth()
    const srcHeight = image.getHeight()
    const rasters = await image.readRasters()
    const band = rasters[0] as ArrayLike<number>

    // First pass: minimum valid elevation, used to fill nodata holes.
    let min = Infinity
    let max = -Infinity
    for (let i = 0; i < band.length; i++) {
      const v = band[i]
      if (v >= NODATA_MIN && v <= NODATA_MAX) {
        if (v < min) min = v
        if (v > max) max = v
      }
    }
    if (!Number.isFinite(min)) {
      return NextResponse.json(
        { error: 'No valid elevation data for this area.' },
        { status: 502 },
      )
    }

    const cleanAt = (x: number, y: number): number => {
      const v = band[y * srcWidth + x]
      return v >= NODATA_MIN && v <= NODATA_MAX ? v : min
    }

    // Downsample to ~TARGET_GRID per side via nearest-neighbor. If the source is
    // already smaller, keep its native resolution rather than upsampling.
    const gridWidth = Math.min(TARGET_GRID, srcWidth)
    const gridHeight = Math.min(TARGET_GRID, srcHeight)

    const elevations: number[] = new Array(gridWidth * gridHeight)
    let outMin = Infinity
    let outMax = -Infinity

    for (let gy = 0; gy < gridHeight; gy++) {
      const sy =
        gridHeight === 1
          ? 0
          : Math.round((gy / (gridHeight - 1)) * (srcHeight - 1))
      for (let gx = 0; gx < gridWidth; gx++) {
        const sx =
          gridWidth === 1
            ? 0
            : Math.round((gx / (gridWidth - 1)) * (srcWidth - 1))
        const v = cleanAt(sx, sy)
        elevations[gy * gridWidth + gx] = v
        if (v < outMin) outMin = v
        if (v > outMax) outMax = v
      }
    }

    const result: TerrainResponse = {
      gridWidth,
      gridHeight,
      elevations,
      minElevation: outMin,
      maxElevation: outMax,
      trails: responseTrails,
      usedBounds,
    }

    return NextResponse.json(result)
  } catch (err) {
    console.error('terrain-mesh: unexpected error:', err)
    return NextResponse.json(
      { error: 'Unable to generate terrain mesh.' },
      { status: 500 },
    )
  }
}
