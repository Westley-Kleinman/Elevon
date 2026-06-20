import { createRequire } from 'module'
import { readFileSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

async function main() {
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(path.resolve('openskidata.gpkg')))

  const skiAreas = JSON.parse(readFileSync(path.resolve('public/data/ski-areas.json'), 'utf-8'))

  // Pick a well-known resort to test against directly
  const testArea = skiAreas.find(a => a.name === 'Telluride Ski Area') || skiAreas[100]
  console.log('Testing against:', testArea)

  // Try exact match
  const stmt = db.prepare('SELECT COUNT(*) as cnt FROM runs_linestring WHERE ski_area_ids = ?')
  stmt.bind([testArea.id])
  stmt.step()
  console.log('Exact match count:', stmt.getAsObject().cnt)
  stmt.free()

  // Try LIKE match in case there's whitespace or it's a list
  const stmt2 = db.prepare('SELECT COUNT(*) as cnt FROM runs_linestring WHERE ski_area_ids LIKE ?')
  stmt2.bind([`%${testArea.id}%`])
  stmt2.step()
  console.log('LIKE match count:', stmt2.getAsObject().cnt)
  stmt2.free()

  // Show raw ski_area_ids values that contain part of this id, to inspect formatting
  const stmt3 = db.prepare(`
    SELECT ski_area_ids, ski_area_names FROM runs_linestring 
    WHERE ski_area_names LIKE ? LIMIT 5
  `)
  stmt3.bind([`%${testArea.name.split(' ')[0]}%`])
  while (stmt3.step()) {
    console.log('Row with matching name:', stmt3.getAsObject())
  }
  stmt3.free()

  // Test WKB parsing on a single geometry blob in isolation
  const stmt4 = db.prepare('SELECT id, geometry FROM runs_linestring LIMIT 1')
  stmt4.step()
  const row = stmt4.getAsObject()
  const blob = row.geometry
  console.log('Geometry blob type:', blob.constructor.name)
  console.log('Geometry first 16 bytes:', Array.from(blob.slice(0, 16)))
  stmt4.free()

  db.close()
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})