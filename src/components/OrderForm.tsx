'use client'

import { useState } from 'react'
import MountainSearch from './MountainSearch'
import MapPreview from './MapPreview'

interface OrderFormProps {
  initialId?: string | null
  initialName?: string
  initialLat?: number | null
  initialLng?: number | null
}

export default function OrderForm({
  initialId = null,
  initialName = '',
  initialLat = null,
  initialLng = null,
}: OrderFormProps) {
  const [mountain, setMountain] = useState(initialName)
  const [mountainId, setMountainId] = useState<string | null>(initialId)
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(
    initialLat !== null && initialLng !== null
      ? { lat: initialLat, lng: initialLng }
      : null,
  )
  const [quantity, setQuantity] = useState(1)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!mountain.trim()) {
      setError('Please choose a mountain first.')
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mountain, quantity, notes }),
      })

      if (!res.ok) throw new Error('Checkout failed')

      const data = (await res.json()) as { url?: string }
      if (data.url) {
        window.location.href = data.url
      } else {
        throw new Error('No checkout URL returned')
      }
    } catch {
      setError('Something went wrong starting checkout. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="grid grid-cols-1 gap-12 md:grid-cols-5 md:gap-16">
      {/* Left — trail preview / map photo + specs (60%) */}
      <div className="md:col-span-3">
        {mountainId ? (
          <MapPreview
            mountainId={mountainId}
            mountainName={mountain || null}
            lat={coords?.lat ?? null}
            lng={coords?.lng ?? null}
          />
        ) : (
          <div className="flex min-h-[500px] items-center justify-center bg-slate">
            <span className="label-eyebrow text-stone">[ map photo ]</span>
          </div>
        )}
        <p className="mt-5 font-inter text-[13px] leading-relaxed text-stone">
          Size: 12&quot; &times; 10&quot; approx&nbsp; &middot;&nbsp; Material: PLA&nbsp;
          &middot;&nbsp; Colors: 4&nbsp; &middot;&nbsp; Ships in 5&ndash;7 days
        </p>
        <p className="mt-3 font-inter text-[13px] leading-relaxed text-stone">
          Maps are typically printed around 10&quot; &times; 10&quot;. Want a
          custom size, a different mountain format, or something off-menu? Reach
          out &mdash;{' '}
          <a
            href="mailto:westley.kleinman@duke.edu"
            className="text-stone underline-offset-2 transition-colors duration-200 hover:text-slate hover:underline"
          >
            westley.kleinman@duke.edu
          </a>
        </p>
      </div>

      {/* Right — order form (40%) */}
      <div className="md:col-span-2">
        <form onSubmit={handleSubmit} className="w-full">
          <h1 className="font-bebas uppercase text-slate [font-size:clamp(44px,5vw,68px)]">
            Order Your Map
          </h1>

          <div className="mt-4 flex items-baseline gap-4">
            <span className="font-bebas text-[56px] leading-none text-trail">$49</span>
            <span className="label-eyebrow">Free Shipping</span>
          </div>

          <div className="mt-10">
            <MountainSearch
              value={mountain}
              onSelect={({ id, name, lat, lng }) => {
                setMountain(name)
                setMountainId(id)
                setCoords({ lat, lng })
              }}
            />
          </div>

          {/* Previews disclaimer — calm, low-weight trust footnote */}
          <div className="mt-8">
            <span className="label-eyebrow block">A Note on Previews</span>
            <p className="mt-2 font-inter text-[13px] leading-relaxed text-stone">
              Not every mountain will render a preview &mdash; some resorts
              aren&rsquo;t fully mapped yet. If your mountain doesn&rsquo;t show a
              preview, don&rsquo;t worry: we&rsquo;ll still hand-map it for your
              print. Trail previews are sourced from open community map data and
              may not perfectly match official resort trail maps &mdash; some
              trails near resort boundaries may belong to adjacent trail systems.
              Your final printed map is verified by hand before production.
            </p>
          </div>

          {/* Quantity */}
          <div className="mt-10">
            <span className="label-eyebrow block">Quantity</span>
            <div className="mt-3 inline-flex items-center border-2 border-slate">
              <button
                type="button"
                aria-label="Decrease quantity"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="flex h-12 w-12 items-center justify-center font-inter text-2xl leading-none text-slate transition-colors duration-200 hover:bg-slate hover:text-snow"
              >
                &minus;
              </button>
              <span className="flex h-12 w-14 items-center justify-center border-x-2 border-slate font-inter text-[18px] font-medium text-slate">
                {quantity}
              </span>
              <button
                type="button"
                aria-label="Increase quantity"
                onClick={() => setQuantity((q) => Math.min(99, q + 1))}
                className="flex h-12 w-12 items-center justify-center font-inter text-2xl leading-none text-slate transition-colors duration-200 hover:bg-slate hover:text-snow"
              >
                +
              </button>
            </div>
          </div>

          {/* Notes */}
          <div className="mt-10">
            <label htmlFor="order-notes" className="label-eyebrow block">
              Order Notes (optional)
            </label>
            <textarea
              id="order-notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="A specific trail map year, a gift note, anything we should know..."
              className="mt-2 w-full resize-none border-0 border-b-2 border-slate bg-transparent px-0 py-2 font-inter text-[16px] text-slate outline-none placeholder:text-stone/70"
            />
          </div>

          {error && (
            <p className="mt-6 font-inter text-[13px] text-trail">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-10 flex w-full items-center justify-center bg-slate px-8 py-5 transition-colors duration-200 hover:bg-alpine disabled:cursor-not-allowed disabled:opacity-70"
          >
            <span className="font-bebas text-[24px] uppercase tracking-wide text-snow">
              {submitting ? 'Redirecting\u2026' : `Order Now \u2014 $${49 * quantity}`}
            </span>
          </button>

          <p className="mt-5 font-inter text-[13px] leading-relaxed text-stone">
            Secure checkout via Stripe. We&rsquo;ll email you within 24hrs to
            confirm your mountain.
          </p>
        </form>
      </div>
    </div>
  )
}
