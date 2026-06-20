import { createRequire } from 'module'
import { readFileSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

async function main() {
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(path.resolve('openskidata.gpkg')))

  const tables = db
    .exec("SELECT name FROM sqlite_master WHERE type='table'")[0]
    .values.map((v) => v[0])
  const liftTables = tables.filter((t) => t.toLowerCase().includes('lift'))
  console.log('LIFT-RELATED TABLES:', liftTables)

  const cols = db.exec('PRAGMA table_info("lifts_linestring")')
  console.log('\nlifts_linestring columns:')
  for (const v of cols[0].values) {
    console.log(`  cid ${v[0]}  name=${v[1]}  type=${v[2]}`)
  }

  const cnt = db.exec('SELECT COUNT(*) FROM "lifts_linestring"')
  console.log('\nlifts_linestring row count:', cnt[0].values[0][0])

  const sample = db.exec(
    'SELECT name, ski_area_ids, typeof(geometry), length(geometry) FROM "lifts_linestring" WHERE ski_area_ids IS NOT NULL LIMIT 5',
  )
  console.log('\nsample columns:', sample[0].columns)
  for (const v of sample[0].values) console.log('  ', JSON.stringify(v))

  db.close()
}

main().catch((err) => {
  console.error('Error:', err)
  process.exit(1)
})
