import { createRequire } from 'module'
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs'
import path from 'path'
import { squareBounds } from './lib/geoBounds.mjs'
import { parseGpkgGeometry } from './lib/wkb.mjs'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

const GPKG_PATH = path.resolve('openskidata.gpkg')
const TRAILS_DIR = path.resolve('public/data/trails')
const OUTPUT_DIR = path.resolve('public/data/lifts')
// Must match BBOX_PADDING in extract-trails.mjs and TRAIL_BBOX_PADDING in the
// terrain-mesh route so lifts, trails, and terrain all share one square box.
const BBOX_PADDING = 0.15

// Tight lat/lng box around a flat list of [lng, lat] points.
function bboxFromCoords(allCoords) {
  let minLat = Infinity
  let maxLat = -Infinity
  let minLng = Infinity
  let maxLng = -Infinity
  for (const [lng, lat] of allCoords) {
    if (!Number.isFinite(lng) || !Number.isFinite(lat)) continue
    if (lat < minLat) minLat = lat
    if (lat > maxLat) maxLat = lat
    if (lng < minLng) minLng = lng
    if (lng > maxLng) maxLng = lng
  }
  if (!Number.isFinite(minLat) || !Number.isFinite(minLng)) return null
  return { minLat, maxLat, minLng, maxLng }
}

// Recompute the trail-derived bbox from a mountain's existing trail file so
// lifts project into the IDENTICAL box (same inputs + same squareBounds).
function trailBbox(mountainId) {
  const p = path.join(TRAILS_DIR, `${mountainId}.json`)
  if (!existsSync(p)) return null
  try {
    const data = JSON.parse(readFileSync(p, 'utf-8'))
    const all = []
    for (const run of data.runs ?? []) {
      for (const c of run.rawCoordinates ?? []) all.push(c)
    }
    return bboxFromCoords(all)
  } catch {
    return null
  }
}

// Build a projector from a square geo box. Mirrors the exact projection math in
// extract-trails.mjs (longitude scaled by cos(lat), 0-1000 viewbox, 50px pad),
// so trail and lift SVG coordinates line up pixel-for-pixel.
function buildProjector(sq) {
  const centerLat = (sq.minLat + sq.maxLat) / 2
  const cosLat = Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6)
  const physWidth = (sq.maxLng - sq.minLng) * cosLat
  const physHeight = sq.maxLat - sq.minLat
  const VIEW = 1000
  const scale = VIEW / Math.max(physWidth, physHeight)
  const padding = 50

  const project = ([x, y]) => [
    (x - sq.minLng) * cosLat * scale + padding,
    (sq.maxLat - y) * scale + padding,
  ]
  const bounds = {
    width: physWidth * scale + padding * 2,
    height: physHeight * scale + padding * 2,
  }
  return { project, bounds }
}

async function main() {
  console.log('Loading GeoPackage...')
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(GPKG_PATH))

  console.log('Loading ski areas list...')
  const skiAreas = JSON.parse(
    readFileSync(path.resolve('public/data/ski-areas.json'), 'utf-8'),
  )

  mkdirSync(OUTPUT_DIR, { recursive: true })

  let processed = 0
  let withLifts = 0
  let ownBoxFallback = 0
  let parseErrors = 0

  for (const area of skiAreas) {
    processed++
    if (processed % 500 === 0) {
      console.log(
        `Processed ${processed}/${skiAreas.length}... (${withLifts} with lifts so far)`,
      )
    }

    const stmt = db.prepare(
      'SELECT name, geometry FROM lifts_linestring WHERE ski_area_ids = ?',
    )
    stmt.bind([area.id])

    const lifts = []
    while (stmt.step()) {
      const row = stmt.getAsObject()
      const blob = row.geometry
      if (!blob) continue

      const bytes = blob instanceof Uint8Array ? blob : new Uint8Array(blob)
      let lines
      try {
        lines = parseGpkgGeometry(bytes)
      } catch (e) {
        parseErrors++
        continue
      }
      if (!lines) continue

      for (const line of lines) {
        if (!line || line.length < 2) continue
        if (line.some(([x, y]) => !Number.isFinite(x) || !Number.isFinite(y))) continue
        lifts.push({ name: row.name ?? null, coords: line })
      }
    }
    stmt.free()

    if (lifts.length === 0) continue

    // Prefer the mountain's trail box so lifts align with trails + terrain.
    // Fall back to the lifts' own footprint when no trail file exists.
    let sourceBox = trailBbox(area.id)
    if (!sourceBox) {
      const all = []
      for (const lift of lifts) for (const c of lift.coords) all.push(c)
      sourceBox = bboxFromCoords(all)
      if (sourceBox) ownBoxFallback++
    }
    if (!sourceBox) continue

    const sq = squareBounds(
      sourceBox.minLat,
      sourceBox.maxLat,
      sourceBox.minLng,
      sourceBox.maxLng,
      BBOX_PADDING,
    )
    const { project, bounds } = buildProjector(sq)

    const projectedLifts = lifts.map((lift) => ({
      name: lift.name,
      coordinates: lift.coords.map(project),
      // Original geographic coordinates as [lng, lat] (WKB X = lng, Y = lat).
      rawCoordinates: lift.coords.map(([x, y]) => [x, y]),
    }))

    const output = {
      mountainId: area.id,
      mountainName: area.name,
      bounds,
      lifts: projectedLifts,
    }

    writeFileSync(
      path.join(OUTPUT_DIR, `${area.id}.json`),
      JSON.stringify(output),
    )
    withLifts++
  }

  console.log(
    `\nDone. ${withLifts} mountains have lift data out of ${skiAreas.length} total.`,
  )
  console.log(
    `(${ownBoxFallback} used their own lift footprint because no trail file existed.)`,
  )
  console.log(`Parse errors encountered: ${parseErrors}`)
  db.close()
}

main().catch((err) => {
  console.error('Error:', err)
  process.exit(1)
})
