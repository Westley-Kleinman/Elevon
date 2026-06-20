'use client'

import { useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import TrailPreview, { type DifficultyStats } from './TrailPreview'
import {
  type Category,
  type LiftData,
  type LiftLine,
  CATEGORY_COLOR,
  DEFAULT_CATEGORIES,
} from '@/lib/mapCategories'

// WebGL must not render on the server.
const TerrainMesh = dynamic(() => import('./TerrainMesh'), { ssr: false })

interface Bounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

interface TrailLine {
  difficulty: string
  rawCoordinates: number[][]
}

interface TerrainData {
  gridWidth: number
  gridHeight: number
  elevations: number[]
  minElevation: number
  maxElevation: number
  trails: TrailLine[] | null
  usedBounds: Bounds
}

interface MapPreviewProps {
  mountainId: string | null
  mountainName: string | null
  lat: number | null
  lng: number | null
}

type Mode = '2d' | 'loading3d' | '3d' | 'error3d'

const BORDER = 'border border-[rgba(15,25,35,0.15)]'
const CENTER_BOX = 'flex min-h-[500px] w-full flex-col items-center justify-center'

// Exaggerated terrain reads better for small/low-relief mountains than true
// scale, so we default above 1× and let the user dial it back.
const DEFAULT_HEIGHT_EXAG = 2.0

const M_TO_FT = 3.28084
const toFt = (m: number) => Math.round(m * M_TO_FT)

// Difficulty swatches — colors match the 2D/3D trail palette exactly.
const DIFFICULTY_META: {
  key: keyof Omit<DifficultyStats, 'total'>
  label: string
  color: string
}[] = [
  { key: 'easy', label: 'Green', color: '#4A7C3C' },
  { key: 'intermediate', label: 'Blue', color: '#2C4A6E' },
  { key: 'advanced', label: 'Black', color: '#1A1A1A' },
  { key: 'other', label: 'Other', color: '#8C8880' },
]

// Human-readable headline from whichever main difficulty dominates.
function difficultySummary(stats: DifficultyStats): string | null {
  const ranked: [number, string][] = [
    [stats.easy, 'Beginner Friendly'],
    [stats.intermediate, 'Mostly Intermediate'],
    [stats.advanced, 'Advanced Terrain'],
  ]
  const best = ranked.reduce((a, b) => (b[0] > a[0] ? b : a))
  return best[0] > 0 ? best[1] : null
}

function MinimalSlider({
  label,
  display,
  min,
  max,
  step,
  value,
  onChange,
}: {
  label: string
  display: string
  min: number
  max: number
  step: number
  value: number
  onChange: (v: number) => void
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="font-inter text-[11px] uppercase tracking-[0.2em] text-stone">
          {label}
        </span>
        <span className="font-inter text-[11px] text-stone">{display}</span>
      </div>
      <input
        type="range"
        className="elevon-range mt-3"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label}
      />
    </div>
  )
}

// 4-color layer toggles. Exactly 3 stay active; see toggleCategory for the FIFO
// replacement logic. Active = full opacity + 2px colored underline; inactive =
// 40% opacity, no underline.
const TOGGLE_ITEMS: { cat: Category; label: string }[] = [
  { cat: 'green', label: 'Green' },
  { cat: 'blue', label: 'Blue' },
  { cat: 'black', label: 'Black' },
  { cat: 'lifts', label: 'Red Lifts' },
]

function CategoryToggles({
  active,
  onToggle,
}: {
  active: Category[]
  onToggle: (c: Category) => void
}) {
  return (
    <div className="mt-8">
      <div className="h-px w-full bg-stone/20" />
      <p className="label-eyebrow mt-6">Map Colors</p>
      <div className="mt-4 flex flex-wrap gap-x-7 gap-y-3">
        {TOGGLE_ITEMS.map(({ cat, label }) => {
          const on = active.includes(cat)
          const color = CATEGORY_COLOR[cat]
          return (
            <button
              key={cat}
              type="button"
              onClick={() => onToggle(cat)}
              aria-pressed={on}
              className={`flex items-center gap-2 pb-1 transition-opacity duration-200 ${
                on ? 'opacity-100' : 'opacity-40 hover:opacity-70'
              }`}
              style={{
                borderBottom: `2px solid ${on ? color : 'transparent'}`,
              }}
            >
              <span
                className="h-2 w-2 shrink-0"
                style={{ backgroundColor: color }}
                aria-hidden="true"
              />
              <span className="font-inter text-[12px] uppercase tracking-[0.18em] text-slate">
                {label}
              </span>
            </button>
          )
        })}
      </div>
      <p className="mt-4 font-inter text-[12px] leading-relaxed text-stone">
        Currently printing in 4 colors (white base + 3 selected). Up to 8-color
        prints are coming soon.
      </p>
    </div>
  )
}

// A single stat: large slate value over a small stone uppercase label, with an
// optional color swatch (used for the trail-difficulty breakdown).
function StatBlock({
  label,
  value,
  swatch,
}: {
  label: string
  value: React.ReactNode
  swatch?: string
}) {
  return (
    <div className="flex items-start gap-2.5">
      {swatch && (
        <span
          className="mt-1 h-2.5 w-2.5 shrink-0"
          style={{ backgroundColor: swatch }}
          aria-hidden="true"
        />
      )}
      <div>
        <div className="font-inter text-[18px] font-medium leading-none text-slate">
          {value}
        </div>
        <div className="label-eyebrow mt-1.5">{label}</div>
      </div>
    </div>
  )
}

// A "mountain spec sheet" below the preview. Trail breakdown is always shown
// once trail data loads; elevation stats only appear after the 3D view has
// fetched terrain (terrain != null).
function MountainStats({
  stats,
  terrain,
}: {
  stats: DifficultyStats
  terrain: TerrainData | null
}) {
  const diffEntries = DIFFICULTY_META.filter((m) => stats[m.key] > 0)
  const summary = difficultySummary(stats)
  const base = terrain ? toFt(terrain.minElevation) : null
  const summit = terrain ? toFt(terrain.maxElevation) : null
  const drop = terrain ? toFt(terrain.maxElevation - terrain.minElevation) : null

  return (
    <div className="mt-8">
      <div className="h-px w-full bg-stone/20" />
      <p className="label-eyebrow mt-6">Mountain Stats</p>

      {summary && (
        <p className="mt-3 font-inter text-[13px] uppercase tracking-[0.18em] text-slate">
          {summary}
        </p>
      )}

      {/* Trail difficulty breakdown */}
      <div className="mt-6 grid grid-cols-2 gap-x-8 gap-y-6 sm:grid-cols-4">
        {diffEntries.map((m) => (
          <StatBlock
            key={m.key}
            swatch={m.color}
            value={stats[m.key]}
            label={`${m.label} Runs`}
          />
        ))}
      </div>

      {/* Totals + elevation spec */}
      <div className="mt-7 grid grid-cols-2 gap-x-8 gap-y-6 sm:grid-cols-4">
        <StatBlock label="Total Trails" value={stats.total} />
        {drop !== null && (
          <StatBlock label="Vertical Drop" value={`${drop.toLocaleString()} ft`} />
        )}
        {base !== null && (
          <StatBlock
            label="Base Elevation"
            value={`${base.toLocaleString()} ft`}
          />
        )}
        {summit !== null && (
          <StatBlock
            label="Summit Elevation"
            value={`${summit.toLocaleString()} ft`}
          />
        )}
      </div>
    </div>
  )
}

export default function MapPreview({
  mountainId,
  mountainName,
  lat,
  lng,
}: MapPreviewProps) {
  const [mode, setMode] = useState<Mode>('2d')
  const [trailsAvailable, setTrailsAvailable] = useState(false)
  const [terrain, setTerrain] = useState<TerrainData | null>(null)
  const [visible, setVisible] = useState(true)
  const [heightExaggeration, setHeightExaggeration] = useState(DEFAULT_HEIGHT_EXAG)
  const [stats, setStats] = useState<DifficultyStats | null>(null)

  // Active map-color layers — exactly 3 at all times (FIFO replacement).
  const [activeCategories, setActiveCategories] =
    useState<Category[]>(DEFAULT_CATEGORIES)

  // Lift overlay data, fetched lazily the first time "Red Lifts" is enabled for
  // a mountain, then cached so re-toggling never refetches. null = not loaded.
  const [lifts, setLifts] = useState<LiftLine[] | null>(null)
  const liftStatusRef = useRef<'idle' | 'loading' | 'done'>('idle')

  // Track the active mountain so a slow 3D fetch can't apply to a newer mountain.
  const currentIdRef = useRef(mountainId)
  useEffect(() => {
    currentIdRef.current = mountainId
  }, [mountainId])

  // Reset to the 2D default whenever the mountain changes.
  useEffect(() => {
    setMode('2d')
    setTrailsAvailable(false)
    setTerrain(null)
    setStats(null)
    setHeightExaggeration(DEFAULT_HEIGHT_EXAG)
    setActiveCategories(DEFAULT_CATEGORIES)
    setLifts(null)
    liftStatusRef.current = 'idle'
  }, [mountainId])

  // Activate a category, dropping the longest-active one (FIFO) so exactly 3
  // stay selected. Clicking an already-active category is a no-op.
  const toggleCategory = (cat: Category) => {
    setActiveCategories((prev) =>
      prev.includes(cat) ? prev : [...prev.slice(1), cat],
    )
  }

  // Fetch lift geometry once, the first time "Red Lifts" becomes active.
  useEffect(() => {
    if (!mountainId) return
    if (!activeCategories.includes('lifts')) return
    if (liftStatusRef.current !== 'idle') return

    const id = mountainId
    liftStatusRef.current = 'loading'
    fetch(`/data/lifts/${id}.json`)
      .then((res) => {
        if (!res.ok) throw new Error('no lifts')
        return res.json() as Promise<LiftData>
      })
      .then((json) => {
        if (currentIdRef.current !== id) return
        setLifts(json.lifts ?? [])
        liftStatusRef.current = 'done'
      })
      .catch(() => {
        if (currentIdRef.current !== id) return
        setLifts([]) // cache the empty result so we don't refetch
        liftStatusRef.current = 'done'
      })
  }, [mountainId, activeCategories])

  const liftsActive = activeCategories.includes('lifts')

  // Brief opacity fade whenever the mode swaps.
  useEffect(() => {
    setVisible(false)
    const raf = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(raf)
  }, [mode])

  const fetchTerrain = async () => {
    if (!mountainId) return
    const id = mountainId
    setMode('loading3d')
    setTerrain(null)
    try {
      // Pass lat/lng so the route can still render terrain-only when a mountain
      // has a center point but no detailed trail file. No padding param -> the
      // route uses its default and can serve the pre-generated cache.
      const params = new URLSearchParams({ mountainId: id })
      if (lat !== null) params.set('lat', String(lat))
      if (lng !== null) params.set('lng', String(lng))

      const res = await fetch(`/api/terrain-mesh?${params.toString()}`)
      if (!res.ok) throw new Error('terrain unavailable')
      const json = (await res.json()) as TerrainData

      if (currentIdRef.current !== id) return // mountain changed mid-flight
      setTerrain(json)
      setMode('3d')
    } catch {
      if (currentIdRef.current === id) setMode('error3d')
    }
  }

  if (!mountainId) return null

  const fade = `transition-opacity duration-[250ms] ${
    visible ? 'opacity-100' : 'opacity-0'
  }`

  // --- Error state is terminal and self-contained -----------------------------
  if (mode === 'error3d') {
    return (
      <div className={fade}>
        <div className={`${BORDER} ${CENTER_BOX} bg-white px-6 text-center`}>
          <p className="font-bebas text-[20px] uppercase leading-none text-slate">
            3D preview unavailable
          </p>
          <p className="mx-auto mt-3 max-w-sm font-inter text-[14px] leading-relaxed text-stone">
            We couldn&rsquo;t load terrain data for this mountain right now. The
            2D preview above still shows your trails.
          </p>
          <button
            type="button"
            onClick={() => setMode('2d')}
            className="group mt-6 inline-flex items-center border-2 border-slate bg-transparent px-6 py-3 transition-colors duration-200 hover:bg-slate"
          >
            <span className="label-nav text-slate transition-colors duration-200 group-hover:text-snow">
              Back to 2D
            </span>
          </button>
        </div>
      </div>
    )
  }

  // --- Preview area (varies by mode) ------------------------------------------
  let preview: React.ReactNode

  if (mode === 'loading3d') {
    preview = (
      <div className={`${BORDER} ${CENTER_BOX} bg-white px-8`}>
        <p className="animate-pulse font-inter text-[13px] text-stone">
          Rendering terrain&hellip;
        </p>
      </div>
    )
  } else if (mode === '3d' && terrain) {
    preview = (
      <>
        <div className={`${BORDER} bg-white`}>
          <div className="h-[500px] w-full">
            <TerrainMesh
              gridWidth={terrain.gridWidth}
              gridHeight={terrain.gridHeight}
              elevations={terrain.elevations}
              minElevation={terrain.minElevation}
              maxElevation={terrain.maxElevation}
              trails={terrain.trails}
              usedBounds={terrain.usedBounds}
              heightExaggeration={heightExaggeration}
              activeCategories={activeCategories}
              lifts={liftsActive ? lifts : null}
            />
          </div>
        </div>
        {!terrain.trails && (
          <p className="mt-3 font-inter text-[12px] text-stone">
            Trail data isn&rsquo;t available for this mountain yet &mdash; showing
            terrain only.
          </p>
        )}
        <button
          type="button"
          onClick={() => setMode('2d')}
          className="mt-3 font-inter text-[12px] text-stone underline-offset-4 transition-colors duration-200 hover:text-slate hover:underline"
        >
          Back to 2D
        </button>
      </>
    )
  } else {
    // Default 2D preview with an optional "View in 3D" affordance.
    preview = (
      <>
        <TrailPreview
          mountainId={mountainId}
          mountainName={mountainName}
          lat={lat}
          lng={lng}
          onAvailabilityChange={setTrailsAvailable}
          onStats={setStats}
          activeCategories={activeCategories}
          lifts={liftsActive ? lifts : null}
        />
        {trailsAvailable && (
          <button
            type="button"
            onClick={fetchTerrain}
            className="group mt-4 inline-flex items-center border-2 border-slate bg-transparent px-6 py-3 transition-colors duration-200 hover:bg-slate"
          >
            <span className="label-nav text-slate transition-colors duration-200 group-hover:text-snow">
              View in 3D
            </span>
          </button>
        )}
      </>
    )
  }

  return (
    <div className={fade}>
      {preview}

      {/* Vertical-scale caption + single Terrain Height slider — only in 3D. */}
      {mode === '3d' && terrain && (
        <div className="mt-4">
          <p className="font-inter text-[11px] text-stone">
            Terrain shown at{' '}
            {heightExaggeration % 1 === 0
              ? heightExaggeration
              : heightExaggeration.toFixed(1)}
            &times; vertical scale for clarity
          </p>
          <div className="mt-4 max-w-[260px]">
            <MinimalSlider
              label="Terrain Height"
              display={`${heightExaggeration.toFixed(1)}\u00d7`}
              min={0.5}
              max={3}
              step={0.1}
              value={heightExaggeration}
              onChange={setHeightExaggeration}
            />
          </div>
        </div>
      )}

      {/* Map-color layer toggles — shown once trail data is available, in both
          2D and 3D, so the customer can pick their 3 print colors. */}
      {trailsAvailable && (
        <CategoryToggles active={activeCategories} onToggle={toggleCategory} />
      )}

      {/* Stats — trail breakdown shows once trail data loads; elevation stats
          appear once the 3D view has fetched terrain. */}
      {stats && <MountainStats stats={stats} terrain={terrain} />}
    </div>
  )
}
