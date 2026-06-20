import { createRequire } from 'module'
import { readFileSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

async function main() {
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(path.resolve('openskidata.gpkg')))

  // Grab a few sample runs that DO have a ski_area_ids value
  const sample = db.exec(`
    SELECT id, name, difficulty, ski_area_ids, ski_area_names, typeof(geometry), length(geometry)
    FROM runs_linestring
    WHERE ski_area_ids IS NOT NULL AND ski_area_ids != ''
    LIMIT 5
  `)

  console.log('Columns:', sample[0].columns)
  sample[0].values.forEach(row => console.log(row))

  db.close()
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})