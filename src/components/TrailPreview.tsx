'use client'

import { useEffect, useRef, useState } from 'react'
import {
  type Category,
  type LiftLine,
  LIFT_COLOR,
  DEFAULT_CATEGORIES,
  difficultyCategory,
} from '@/lib/mapCategories'

export interface DifficultyStats {
  easy: number
  intermediate: number
  advanced: number
  other: number
  total: number
}

interface TrailPreviewProps {
  mountainId: string | null
  mountainName: string | null
  lat: number | null
  lng: number | null
  // Optional: notified once the trail fetch settles so a parent can decide
  // whether to offer the 3D view (true = trails available, false = fallback).
  onAvailabilityChange?: (available: boolean) => void
  // Optional: notified with per-difficulty run counts derived from the trail
  // data we already fetch (null when no trail data is available).
  onStats?: (stats: DifficultyStats | null) => void
  // Currently active map-color layers; only matching trails (and lifts, when
  // active) render. Defaults to green/blue/black if omitted.
  activeCategories?: Category[]
  // Lift geometry (projected coordinates) supplied by the parent; rendered red
  // when the "lifts" category is active. null = not loaded / not requested.
  lifts?: LiftLine[] | null
}

type Difficulty = 'easy' | 'intermediate' | 'advanced' | 'other'

interface Run {
  difficulty: Difficulty
  coordinates: [number, number][]
}

interface TrailData {
  mountainId: string
  mountainName: string
  bounds: { width: number; height: number }
  runs: Run[]
}

const STROKE: Record<Difficulty, string> = {
  easy: '#4A7C3C',
  intermediate: '#2C4A6E',
  advanced: '#1A1A1A',
  other: '#8C8880',
}

const strokeFor = (d: Difficulty) => STROKE[d] ?? STROKE.other

type Status = 'loading' | 'ready' | 'unavailable'

const BORDER = 'border border-[rgba(15,25,35,0.15)]'
const BOX = 'flex min-h-[500px] w-full flex-col items-center justify-center'

export default function TrailPreview({
  mountainId,
  mountainName,
  onAvailabilityChange,
  onStats,
  activeCategories = DEFAULT_CATEGORIES,
  lifts,
}: TrailPreviewProps) {
  const [status, setStatus] = useState<Status>('loading')
  const [data, setData] = useState<TrailData | null>(null)
  const [visible, setVisible] = useState(false)

  // Keep the latest callbacks in refs so they don't churn the fetch effect.
  const availabilityRef = useRef(onAvailabilityChange)
  useEffect(() => {
    availabilityRef.current = onAvailabilityChange
  }, [onAvailabilityChange])

  const statsRef = useRef(onStats)
  useEffect(() => {
    statsRef.current = onStats
  }, [onStats])

  useEffect(() => {
    if (!mountainId) return

    let cancelled = false
    setStatus('loading')
    setVisible(false)
    setData(null)

    fetch(`/data/trails/${mountainId}.json`)
      .then((res) => {
        if (!res.ok) throw new Error('not found')
        return res.json() as Promise<TrailData>
      })
      .then((json) => {
        if (cancelled) return
        if (json.runs && json.runs.length > 0) {
          setData(json)
          setStatus('ready')
          availabilityRef.current?.(true)
          const counts: DifficultyStats = {
            easy: 0,
            intermediate: 0,
            advanced: 0,
            other: 0,
            total: json.runs.length,
          }
          for (const run of json.runs) {
            if (run.difficulty in counts) counts[run.difficulty] += 1
            else counts.other += 1
          }
          statsRef.current?.(counts)
        } else {
          setStatus('unavailable')
          availabilityRef.current?.(false)
          statsRef.current?.(null)
        }
      })
      .catch(() => {
        if (cancelled) return
        setStatus('unavailable')
        availabilityRef.current?.(false)
        statsRef.current?.(null)
      })

    return () => {
      cancelled = true
    }
  }, [mountainId])

  // trigger the fade-in once a new state has settled
  useEffect(() => {
    if (status === 'loading') return
    const raf = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(raf)
  }, [status])

  if (!mountainId) return null

  if (status === 'loading') {
    return (
      <div className={`${BORDER} ${BOX} gap-3 bg-white px-8`}>
        <div className="h-px w-2/3 animate-pulse bg-slate/30" />
        <p className="font-inter text-[12px] text-stone">Loading trail preview&hellip;</p>
      </div>
    )
  }

  if (status === 'unavailable' || !data) {
    return (
      <div
        className={`${BORDER} ${BOX} bg-white px-6 text-center transition-opacity duration-[250ms] ${
          visible ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <p className="font-bebas text-[20px] uppercase leading-none text-slate">
          Trail preview not yet available
        </p>
        <p className="mx-auto mt-3 max-w-sm font-inter text-[14px] leading-relaxed text-stone">
          We&rsquo;ll still map this mountain by hand. Detailed trail data
          isn&rsquo;t published for every resort yet.
        </p>
      </div>
    )
  }

  return (
    <div
      className={`transition-opacity duration-[250ms] ${
        visible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <div className={`${BORDER} ${BOX} bg-white p-6`}>
        <div className="relative h-[440px] w-full">
          <svg
            viewBox={`0 0 ${data.bounds.width} ${data.bounds.height}`}
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label={`Trail map preview${mountainName ? ` of ${mountainName}` : ''}`}
            className="absolute inset-0 h-full w-full"
          >
            {data.runs.map((run, i) => {
              const cat = difficultyCategory(run.difficulty)
              if (!cat || !activeCategories.includes(cat)) return null
              return (
                <polyline
                  key={`run-${i}`}
                  points={run.coordinates.map(([x, y]) => `${x},${y}`).join(' ')}
                  fill="none"
                  stroke={strokeFor(run.difficulty)}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )
            })}

            {activeCategories.includes('lifts') &&
              lifts?.map((lift, i) => (
                <polyline
                  key={`lift-${i}`}
                  points={lift.coordinates.map(([x, y]) => `${x},${y}`).join(' ')}
                  fill="none"
                  stroke={LIFT_COLOR}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ))}
          </svg>
        </div>
      </div>
      <p className="mt-3 font-inter text-[12px] text-stone">
        Preview &mdash; actual print includes full elevation relief
      </p>
    </div>
  )
}
