import { createRequire } from 'module'
import { readFileSync, writeFileSync, mkdirSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

const GPKG_PATH = path.resolve('openskidata.gpkg')

function parsePointGeometry(blob) {
  if (blob[0] !== 0x47 || blob[1] !== 0x50) return null // not 'GP' magic

  const flags = blob[3]
  const envelopeIndicator = (flags >> 1) & 0x07
  const envelopeSizes = [0, 32, 48, 48, 64]
  const envelopeBytes = envelopeSizes[envelopeIndicator] ?? 0

  const wkbStart = 8 + envelopeBytes
  const view = new DataView(blob.buffer, blob.byteOffset, blob.byteLength)

  const byteOrder = view.getUint8(wkbStart)
  const little = byteOrder === 1
  let pos = wkbStart + 1

  const geomType = view.getUint32(pos, little)
  pos += 4
  const baseType = geomType & 0xFF

  if (baseType !== 1) return null // 1 = Point

  const x = view.getFloat64(pos, little); pos += 8
  const y = view.getFloat64(pos, little); pos += 8

  if (!Number.isFinite(x) || !Number.isFinite(y)) return null

  return { lng: x, lat: y }
}

async function main() {
  console.log('Loading GeoPackage...')
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(GPKG_PATH))

  const results = db.exec(`
    SELECT feature_id, name, country_codes, regions, geometry
    FROM ski_areas_point
    WHERE name IS NOT NULL AND name != ''
    ORDER BY name
  `)

  if (!results[0]) {
    console.error('No results found.')
    process.exit(1)
  }

  let withCoords = 0
  let withoutCoords = 0

  const mountains = results[0].values.map(row => {
    const blob = row[4]
    let coords = null
    if (blob) {
      const bytes = blob instanceof Uint8Array ? blob : new Uint8Array(blob)
      try {
        coords = parsePointGeometry(bytes)
      } catch (e) {
        coords = null
      }
    }

    if (coords) withCoords++
    else withoutCoords++

    return {
      id: row[0],
      name: row[1],
      country: row[2] ?? '',
      lat: coords?.lat ?? null,
      lng: coords?.lng ?? null
    }
  })

  const unique = [...new Map(mountains.map(m => [m.name + m.id, m])).values()]
  console.log(`Extracted ${unique.length} mountains`)
  console.log(`With coordinates: ${withCoords}, without: ${withoutCoords}`)

  mkdirSync('public/data', { recursive: true })
  writeFileSync('public/data/ski-areas.json', JSON.stringify(unique, null, 2))
  console.log('✅ Saved to public/data/ski-areas.json (now with lat/lng)')

  db.close()
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})