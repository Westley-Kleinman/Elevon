'use client'

import Fuse from 'fuse.js'
import { useEffect, useMemo, useRef, useState } from 'react'

interface SkiArea {
  id: string
  name: string
  country: string
  lat: number
  lng: number
}

interface MountainSearchProps {
  onSelect: (mountain: {
    id: string
    name: string
    lat: number
    lng: number
  }) => void
  value: string
}

const MAX_RESULTS = 8

export default function MountainSearch({ onSelect, value }: MountainSearchProps) {
  const [areas, setAreas] = useState<SkiArea[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [query, setQuery] = useState(value)
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)

  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setQuery(value)
  }, [value])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setLoadError(false)
    fetch('/data/ski-areas.json')
      .then((res) => {
        if (!res.ok) throw new Error(`ski-areas ${res.status}`)
        return res.json() as Promise<SkiArea[]>
      })
      .then((data) => {
        if (cancelled) return
        if (!Array.isArray(data)) throw new Error('malformed ski-areas data')
        setAreas(data)
        setLoading(false)
      })
      .catch(() => {
        if (cancelled) return
        setLoadError(true)
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const fuse = useMemo(
    () =>
      new Fuse(areas, {
        keys: ['name', 'country'],
        threshold: 0.3,
        minMatchCharLength: 2,
      }),
    [areas],
  )

  const results = useMemo(() => {
    if (query.trim().length < 2) return []
    return fuse.search(query.trim()).slice(0, MAX_RESULTS).map((r) => r.item)
  }, [fuse, query])

  // close on outside click
  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [])

  const choose = (mountain: {
    id: string
    name: string
    lat: number
    lng: number
  }) => {
    setQuery(mountain.name)
    onSelect(mountain)
    setOpen(false)
    setActiveIndex(-1)
  }

  const showDropdown = open && query.trim().length >= 2

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < results.length) {
        e.preventDefault()
        const { id, name, lat, lng } = results[activeIndex]
        choose({ id, name, lat, lng })
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
      setActiveIndex(-1)
    }
  }

  return (
    <div ref={containerRef} className="relative w-full">
      <label htmlFor="mountain-search" className="label-eyebrow block">
        Which mountain?
      </label>

      {loading ? (
        <p className="mt-3 py-2 font-inter text-[16px] italic text-stone">
          Loading mountains&hellip;
        </p>
      ) : loadError ? (
        <p className="mt-3 py-2 font-inter text-[14px] leading-relaxed text-stone">
          We couldn&rsquo;t load the mountain list right now. Please refresh the
          page &mdash; or email{' '}
          <a
            href="mailto:westley.kleinman@duke.edu"
            className="text-stone underline-offset-2 transition-colors duration-200 hover:text-slate hover:underline"
          >
            westley.kleinman@duke.edu
          </a>{' '}
          and we&rsquo;ll map your mountain by hand.
        </p>
      ) : (
        <input
          id="mountain-search"
          type="text"
          autoComplete="off"
          value={query}
          placeholder="e.g. Vail, Park City, Whistler..."
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
            setActiveIndex(-1)
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          className="mt-2 w-full border-0 border-b-2 border-slate bg-transparent px-0 py-2 font-inter text-[16px] text-slate outline-none placeholder:text-stone/70"
        />
      )}

      {showDropdown && (
        <div className="absolute left-0 right-0 z-30 border-x border-b border-slate/15 bg-snow">
          {results.length > 0 ? (
            <ul className="dropdown-scroll max-h-[240px] overflow-y-auto">
              {results.map((area, i) => (
                <li key={area.id}>
                  <button
                    type="button"
                    onMouseEnter={() => setActiveIndex(i)}
                    onClick={() =>
                      choose({
                        id: area.id,
                        name: area.name,
                        lat: area.lat,
                        lng: area.lng,
                      })
                    }
                    className={`block w-full cursor-pointer border-0 px-3 py-[10px] text-left transition-colors duration-100 ${
                      activeIndex === i ? 'bg-[#E8E5E1]' : 'bg-transparent'
                    }`}
                  >
                    <span className="block font-inter text-[14px] font-medium text-slate">
                      {area.name}
                    </span>
                    <span className="block font-inter text-[12px] text-stone">
                      {area.country}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-3 py-[10px] font-inter text-[13px] italic text-stone">
              No results &mdash; try a different spelling
            </div>
          )}
        </div>
      )}
    </div>
  )
}
