import { createRequire } from 'module'
import { readFileSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

function parseGpkgGeometry(blob) {
  console.log('First 20 bytes:', Array.from(blob.slice(0, 20)))

  if (blob[0] !== 0x47 || blob[1] !== 0x50) {
    console.log('NOT GP magic, got:', blob[0], blob[1])
    return null
  }

  const version = blob[2]
  const flags = blob[3]
  console.log('version:', version, 'flags binary:', flags.toString(2).padStart(8, '0'))

  const envelopeIndicator = (flags >> 1) & 0x07
  const envelopeSizes = [0, 32, 48, 48, 64]
  const envelopeBytes = envelopeSizes[envelopeIndicator] ?? 0
  console.log('envelopeIndicator:', envelopeIndicator, 'envelopeBytes:', envelopeBytes)

  const wkbStart = 8 + envelopeBytes
  console.log('wkbStart offset:', wkbStart)
  console.log('Bytes at wkbStart:', Array.from(blob.slice(wkbStart, wkbStart + 10)))

  const view = new DataView(blob.buffer, blob.byteOffset, blob.byteLength)
  const byteOrder = view.getUint8(wkbStart)
  const little = byteOrder === 1
  console.log('WKB byte order byte:', byteOrder, '-> little endian:', little)

  let pos = wkbStart + 1
  const geomType = view.getUint32(pos, little)
  console.log('geomType raw:', geomType, 'baseType:', geomType % 1000)
  pos += 4

  const numPoints = view.getUint32(pos, little)
  console.log('numPoints:', numPoints)
  pos += 4

  console.log('First point bytes:', Array.from(blob.slice(pos, pos + 16)))
  const x = view.getFloat64(pos, little)
  const y = view.getFloat64(pos + 8, little)
  console.log('First point parsed (assumed little):', x, y)

  const xBE = view.getFloat64(pos, false)
  const yBE = view.getFloat64(pos + 8, false)
  console.log('First point parsed (forced big):', xBE, yBE)

  return null
}

async function main() {
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(path.resolve('openskidata.gpkg')))

  const stmt = db.prepare(
    "SELECT id, geometry FROM runs_linestring WHERE ski_area_ids = '31448f6acd1c42f66ba4b466f00261c81d791b52' LIMIT 1"
  )
  stmt.step()
  const row = stmt.getAsObject()
  stmt.free()

  console.log('Row id:', row.id)
  const bytes = row.geometry instanceof Uint8Array ? row.geometry : new Uint8Array(row.geometry)
  parseGpkgGeometry(bytes)

  db.close()
}

main().catch(err => console.error('Error:', err))