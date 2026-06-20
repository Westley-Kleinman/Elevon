import { createRequire } from 'module'
import { readFileSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

async function main() {
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(path.resolve('openskidata.gpkg')))

  // Look at ski_areas_point table structure and a sample row
  const cols = db.exec('PRAGMA table_info("ski_areas_point")')
  console.log('ski_areas_point columns:', cols[0].values.map(v => v[1]))

  const sample = db.exec('SELECT id, feature_id, name FROM ski_areas_point LIMIT 5')
  console.log('Sample ski_areas_point rows:')
  sample[0].values.forEach(row => console.log(row))

  db.close()
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})