'use client'

import { useState } from 'react'
import Link from 'next/link'
import MountainSearch from './MountainSearch'
import MapPreview from './MapPreview'

interface SelectedMountain {
  id: string
  name: string
  lat: number
  lng: number
}

export default function PreviewSection() {
  const [selected, setSelected] = useState<SelectedMountain | null>(null)

  const orderHref = selected
    ? `/order?id=${encodeURIComponent(selected.id)}&name=${encodeURIComponent(selected.name)}&lat=${selected.lat}&lng=${selected.lng}`
    : '/order'

  return (
    <section id="preview" className="w-full bg-snow py-28">
      <div className="mx-auto max-w-[1400px] px-6 md:px-10">
        {/* Header */}
        <div className="mx-auto max-w-2xl text-center">
          <p className="label-eyebrow">Live Preview</p>
          <h2 className="mt-4 font-bebas uppercase text-slate [font-size:clamp(48px,5vw,84px)]">
            Preview Your Mountain
          </h2>
          <p className="mt-5 font-inter text-[16px] leading-relaxed text-stone">
            Search any resort. See exactly what your map will look like &mdash;
            every trail, every ridge, in 3D &mdash; before you order.
          </p>
        </div>

        {/* Search */}
        <div className="mx-auto mt-12 max-w-lg">
          <MountainSearch
            value={selected?.name ?? ''}
            onSelect={({ id, name, lat, lng }) =>
              setSelected({ id, name, lat, lng })
            }
          />
        </div>

        {/* Preview area */}
        <div className="mx-auto mt-10 max-w-[900px]">
          {selected ? (
            <>
              <MapPreview
                mountainId={selected.id}
                mountainName={selected.name}
                lat={selected.lat}
                lng={selected.lng}
              />

              {/* Order CTA */}
              <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:gap-6">
                <Link
                  href={orderHref}
                  className="group inline-flex items-center border-2 border-slate bg-transparent px-8 py-4 transition-colors duration-200 hover:bg-slate"
                >
                  <span className="label-nav text-slate transition-colors duration-200 group-hover:text-snow">
                    Order This Map&nbsp;&rarr;
                  </span>
                </Link>
                <span className="font-inter text-[14px] text-stone">
                  $49 &middot; Free Shipping &middot; Ships in 5&ndash;7 days
                </span>
              </div>
            </>
          ) : (
            /* Empty state — shown before any mountain is selected */
            <div className="flex min-h-[400px] items-center justify-center border border-stone/20 bg-white">
              <div className="text-center">
                <p className="font-bebas text-[24px] uppercase text-slate">
                  Search a mountain above
                </p>
                <p className="mt-2 font-inter text-[14px] text-stone">
                  Over 4,000 resorts worldwide
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
