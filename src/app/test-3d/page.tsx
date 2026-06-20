'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'

// WebGL must not render on the server.
const TerrainMesh = dynamic(() => import('@/components/TerrainMesh'), {
  ssr: false,
})

// Telluride Ski Area bounding box (hardcoded for this Stage 1 test).
const TELLURIDE = {
  minLat: 37.89,
  maxLat: 37.96,
  minLng: -107.86,
  maxLng: -107.78,
}
// Telluride Ski Area feature_id (its trail file in public/data/trails).
const TELLURIDE_ID = '31448f6acd1c42f66ba4b466f00261c81d791b52'

interface TrailLine {
  difficulty: string
  rawCoordinates: number[][]
}

interface Bounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
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

type Status = 'idle' | 'loading' | 'ready' | 'error'

export default function Test3DPage() {
  const [status, setStatus] = useState<Status>('idle')
  const [data, setData] = useState<TerrainData | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const renderTerrain = async () => {
    setStatus('loading')
    setErrorMsg('')
    setData(null)
    try {
      const params = new URLSearchParams({
        minLat: String(TELLURIDE.minLat),
        maxLat: String(TELLURIDE.maxLat),
        minLng: String(TELLURIDE.minLng),
        maxLng: String(TELLURIDE.maxLng),
        mountainId: TELLURIDE_ID,
      })
      const res = await fetch(`/api/terrain-mesh?${params.toString()}`)
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json?.error ?? 'Failed to load terrain.')
      }
      setData(json as TerrainData)
      setStatus('ready')
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Something went wrong.')
      setStatus('error')
    }
  }

  return (
    <main className="min-h-screen bg-snow px-6 py-16 md:px-10">
      <div className="mx-auto max-w-[1100px]">
        <p className="label-eyebrow">Stage 1 · Dev Test</p>
        <h1 className="mt-3 font-bebas uppercase text-slate [font-size:clamp(40px,5vw,72px)]">
          Terrain Mesh Pipeline
        </h1>
        <p className="mt-3 max-w-xl font-inter text-[14px] leading-relaxed text-stone">
          Hardcoded to Telluride Ski Area. Fetches SRTM elevation, downsamples to
          a ~120&times;120 grid, and renders a displaced 3D mesh. Drag to rotate,
          scroll to zoom, right-drag to pan.
        </p>

        <button
          type="button"
          onClick={renderTerrain}
          disabled={status === 'loading'}
          className="group mt-8 inline-flex items-center border-2 border-slate bg-transparent px-8 py-4 transition-colors duration-200 hover:bg-slate disabled:cursor-not-allowed disabled:opacity-60"
        >
          <span className="label-nav text-slate transition-colors duration-200 group-hover:text-snow">
            {status === 'loading' ? 'Rendering\u2026' : 'Render Terrain'}
          </span>
        </button>

        <div className="mt-8 h-[600px] w-full border border-stone/20 bg-snow">
          {status === 'idle' && (
            <div className="flex h-full items-center justify-center">
              <p className="font-inter text-[13px] text-stone">
                Press &ldquo;Render Terrain&rdquo; to load the elevation mesh.
              </p>
            </div>
          )}

          {status === 'loading' && (
            <div className="flex h-full items-center justify-center">
              <p className="font-inter text-[13px] text-stone">
                Fetching elevation data&hellip;
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="flex h-full items-center justify-center px-6 text-center">
              <p className="font-inter text-[13px] text-trail">{errorMsg}</p>
            </div>
          )}

          {status === 'ready' && data && (
            <TerrainMesh
              gridWidth={data.gridWidth}
              gridHeight={data.gridHeight}
              elevations={data.elevations}
              minElevation={data.minElevation}
              maxElevation={data.maxElevation}
              trails={data.trails}
              usedBounds={data.usedBounds}
            />
          )}
        </div>

        {status === 'ready' && data && (
          <p className="mt-4 font-inter text-[12px] text-stone">
            Grid {data.gridWidth}&times;{data.gridHeight} &middot; elevation{' '}
            {Math.round(data.minElevation)}&ndash;{Math.round(data.maxElevation)} m
            &middot; trails: {data.trails ? data.trails.length : 'none'} &middot;
            box lat [{data.usedBounds.minLat.toFixed(3)},{' '}
            {data.usedBounds.maxLat.toFixed(3)}] lng [
            {data.usedBounds.minLng.toFixed(3)},{' '}
            {data.usedBounds.maxLng.toFixed(3)}]
          </p>
        )}
      </div>
    </main>
  )
}
