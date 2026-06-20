import { createRequire } from 'module'
import { readFileSync, writeFileSync, mkdirSync } from 'fs'
import path from 'path'
import { squareBounds } from './lib/geoBounds.mjs'
import { parseGpkgGeometry } from './lib/wkb.mjs'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

const GPKG_PATH = path.resolve('openskidata.gpkg')
const OUTPUT_DIR = path.resolve('public/data/trails')
// Must match TRAIL_BBOX_PADDING in src/app/api/terrain-mesh/route.ts so the 2D
// preview and the 3D terrain share the exact same square bounding box.
const BBOX_PADDING = 0.15

function difficultyToCategory(difficulty) {
  if (!difficulty) return 'other'
  const d = difficulty.toLowerCase()
  if (d === 'novice' || d === 'easy') return 'easy'
  if (d === 'intermediate') return 'intermediate'
  if (d === 'advanced' || d === 'expert' || d === 'extreme' || d === 'freeride') return 'advanced'
  return 'other'
}

async function main() {
  console.log('Loading GeoPackage...')
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(GPKG_PATH))

  console.log('Loading ski areas list...')
  const skiAreas = JSON.parse(readFileSync(path.resolve('public/data/ski-areas.json'), 'utf-8'))

  mkdirSync(OUTPUT_DIR, { recursive: true })

  let processed = 0
  let withTrails = 0
  let parseErrors = 0

  for (const area of skiAreas) {
    processed++
    if (processed % 500 === 0) console.log(`Processed ${processed}/${skiAreas.length}... (${withTrails} with trails so far)`)

    const stmt = db.prepare('SELECT difficulty, geometry FROM runs_linestring WHERE ski_area_ids = ?')
    stmt.bind([area.id])

    const runs = []
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

      const category = difficultyToCategory(row.difficulty)
      for (const line of lines) {
        if (!line || line.length < 2) continue
        if (line.some(([x, y]) => !Number.isFinite(x) || !Number.isFinite(y))) continue
        runs.push({ difficulty: category, coords: line })
      }
    }
    stmt.free()

    if (runs.length === 0) continue

    // WKB X = lng, Y = lat.
    let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity
    for (const run of runs) {
      for (const [x, y] of run.coords) {
        if (x < minLng) minLng = x
        if (x > maxLng) maxLng = x
        if (y < minLat) minLat = y
        if (y > maxLat) maxLat = y
      }
    }

    // Square (physical) geo box — same math as the terrain API route, so the 2D
    // SVG and 3D mesh cover the identical area.
    const sq = squareBounds(minLat, maxLat, minLng, maxLng, BBOX_PADDING)
    const centerLat = (sq.minLat + sq.maxLat) / 2
    const cosLat = Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6)

    // Project into physical space (longitude scaled by cos(lat)) so the square
    // box maps to a square viewBox and trails keep their true proportions.
    const physWidth = (sq.maxLng - sq.minLng) * cosLat
    const physHeight = sq.maxLat - sq.minLat
    const VIEW = 1000
    const scale = VIEW / Math.max(physWidth, physHeight)
    const padding = 50

    const projectedRuns = runs.map(run => ({
      difficulty: run.difficulty,
      coordinates: run.coords.map(([x, y]) => [
        (x - sq.minLng) * cosLat * scale + padding,
        (sq.maxLat - y) * scale + padding
      ]),
      // Original geographic coordinates as [lng, lat] (WKB X = lng, Y = lat).
      // Needed for 3D draping onto the terrain mesh.
      rawCoordinates: run.coords.map(([x, y]) => [x, y])
    }))

    const output = {
      mountainId: area.id,
      mountainName: area.name,
      bounds: {
        width: physWidth * scale + padding * 2,
        height: physHeight * scale + padding * 2,
      },
      runs: projectedRuns
    }

    writeFileSync(path.join(OUTPUT_DIR, `${area.id}.json`), JSON.stringify(output))
    withTrails++
  }

  console.log(`\nDone. ${withTrails} mountains have trail data out of ${skiAreas.length} total.`)
  console.log(`Parse errors encountered: ${parseErrors}`)
  db.close()
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})