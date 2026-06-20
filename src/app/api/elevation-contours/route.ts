import { NextResponse } from 'next/server'
import { fromArrayBuffer } from 'geotiff'
import { contours } from 'd3-contour'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

interface ContourLine {
  elevation: number
  coordinates: number[][][]
}

interface ContourResponse {
  bounds: { width: number; height: number }
  lines: ContourLine[]
}

// In-memory cache keyed by mountainId. Persists for the life of the server
// process (cleared on dev hot-reloads, which is fine).
const cache = new Map<string, ContourResponse>()

const NODATA_MIN = -1000
const NODATA_MAX = 9000
const PADDING = 50
const CANVAS = 1000

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const mountainId = searchParams.get('mountainId')
    const latRaw = searchParams.get('lat')
    const lngRaw = searchParams.get('lng')

    const lat = Number(latRaw)
    const lng = Number(lngRaw)

    if (
      !mountainId ||
      latRaw === null ||
      lngRaw === null ||
      !Number.isFinite(lat) ||
      !Number.isFinite(lng)
    ) {
      return NextResponse.json(
        { error: 'mountainId, lat and lng are all required and lat/lng must be valid numbers.' },
        { status: 400 },
      )
    }

    const cached = cache.get(mountainId)
    if (cached) {
      return NextResponse.json(cached)
    }

    const apiKey = process.env.OPENTOPO_API_KEY
    if (!apiKey) {
      console.error('elevation-contours: OPENTOPO_API_KEY is not set')
      return NextResponse.json(
        { error: 'Elevation service is not configured.' },
        { status: 500 },
      )
    }

    const south = lat - 0.05
    const north = lat + 0.05
    const west = lng - 0.05
    const east = lng + 0.05

    const url =
      `https://portal.opentopography.org/API/globaldem?demtype=SRTMGL3` +
      `&south=${south}&north=${north}&west=${west}&east=${east}` +
      `&outputFormat=GTiff&API_Key=${apiKey}`

    const demRes = await fetch(url)
    if (!demRes.ok) {
      const body = await demRes.text().catch(() => '<unreadable>')
      console.error(
        `elevation-contours: OpenTopography request failed (${demRes.status}):`,
        body,
      )
      return NextResponse.json(
        { error: 'Failed to retrieve elevation data.' },
        { status: 502 },
      )
    }

    const arrayBuffer = await demRes.arrayBuffer()

    // OpenTopography sometimes returns a 200 with a plain-text/HTML error body
    // (e.g. rate limiting, bad bbox) instead of a GeoTIFF. Detect that via the
    // TIFF magic bytes ("II" little-endian / "MM" big-endian) before parsing,
    // so geotiff doesn't blow up on a non-raster payload.
    const head = new Uint8Array(arrayBuffer.slice(0, 2))
    const isTiff =
      (head[0] === 0x49 && head[1] === 0x49) ||
      (head[0] === 0x4d && head[1] === 0x4d)
    if (!isTiff) {
      const text = new TextDecoder().decode(arrayBuffer.slice(0, 600))
      console.error(
        `elevation-contours: OpenTopography returned a non-GeoTIFF response ` +
          `(${demRes.status}, ${arrayBuffer.byteLength} bytes, ` +
          `content-type=${demRes.headers.get('content-type')}):`,
        text,
      )
      return NextResponse.json(
        { error: 'Failed to retrieve elevation data.' },
        { status: 502 },
      )
    }

    const tiff = await fromArrayBuffer(arrayBuffer)
    const image = await tiff.getImage()
    const width = image.getWidth()
    const height = image.getHeight()
    const rasters = await image.readRasters()
    const band = rasters[0] as ArrayLike<number>

    // Compute min/max over valid elevation values only.
    let min = Infinity
    let max = -Infinity
    let validCount = 0
    for (let i = 0; i < band.length; i++) {
      const v = band[i]
      if (v >= NODATA_MIN && v <= NODATA_MAX) {
        if (v < min) min = v
        if (v > max) max = v
        validCount++
      }
    }

    if (validCount === 0 || !Number.isFinite(min) || !Number.isFinite(max)) {
      return NextResponse.json(
        { error: 'No valid elevation data for this area.' },
        { status: 502 },
      )
    }

    // Contour interval: aim for ~10 bands, round to nearest 25, minimum 25.
    const range = max - min
    const interval = Math.max(25, Math.round(range / 10 / 25) * 25)

    const thresholds: number[] = []
    for (let t = Math.ceil(min / interval) * interval; t < max; t += interval) {
      thresholds.push(t)
    }

    // Replace nodata/garbage with the min elevation so marching-squares doesn't
    // break on holes in the data.
    const values = new Float64Array(band.length)
    for (let i = 0; i < band.length; i++) {
      const v = band[i]
      values[i] = v >= NODATA_MIN && v <= NODATA_MAX ? v : min
    }

    const generator = contours().size([width, height]).thresholds(thresholds)
    const polygons = generator(Array.from(values))

    const scale = CANVAS / Math.max(width, height)
    const project = (x: number, y: number): number[] => [
      x * scale + PADDING,
      y * scale + PADDING,
    ]

    const lines: ContourLine[] = polygons.map((poly) => ({
      elevation: poly.value,
      // d3 MultiPolygon: coordinates = Array<Polygon> = Array<Array<Ring>>.
      // Flatten one level so each entry is a ring (array of points).
      coordinates: poly.coordinates
        .flatMap((polygon) => polygon)
        .map((ring) => ring.map(([x, y]) => project(x, y))),
    }))

    const result: ContourResponse = {
      bounds: {
        width: width * scale + PADDING * 2,
        height: height * scale + PADDING * 2,
      },
      lines,
    }

    cache.set(mountainId, result)
    return NextResponse.json(result)
  } catch (err) {
    console.error('elevation-contours: unexpected error:', err)
    return NextResponse.json(
      { error: 'Unable to generate elevation contours.' },
      { status: 500 },
    )
  }
}
