import { createRequire } from 'module'
import { readFileSync } from 'fs'
import path from 'path'

const require = createRequire(import.meta.url)
const initSqlJs = require('sql.js')

async function main() {
  console.log('Loading GeoPackage...')
  const SQL = await initSqlJs()
  const db = new SQL.Database(readFileSync(path.resolve('openskidata.gpkg')))

  const tableQuery = db.exec("SELECT name FROM sqlite_master WHERE type='table'")
  const tables = tableQuery[0].values.map(v => v[0])
  console.log('ALL TABLES:', tables)

  const runTables = tables.filter(t => t.toLowerCase().includes('run'))
  console.log('RUN-RELATED TABLES:', runTables)

  for (const t of runTables) {
    try {
      const count = db.exec(`SELECT COUNT(*) FROM "${t}"`)
      console.log(`${t} row count:`, count[0]?.values[0][0])

      const cols = db.exec(`PRAGMA table_info("${t}")`)
      console.log(`${t} columns:`, cols[0]?.values.map(v => v[1]))
    } catch (e) {
      console.log(`${t} error:`, e.message)
    }
  }

  db.close()
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})