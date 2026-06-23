// Three-panel section showing the product evolution:
//   traditional flat map  →  digital 3D preview  →  physical printed map
// Placeholder image slots will be swapped for real photos later.

const PANELS = [
  {
    label: 'Traditional Flat Map',
    caption: '5,000 years of the same view',
  },
  {
    label: 'Digital 3D Preview',
    caption: 'Every trail, every ridge, rendered',
  },
  {
    label: 'Your Physical Map',
    caption: 'Printed and on your wall',
  },
]

export default function EvolutionStrip() {
  return (
    <section className="w-full bg-slate py-28">
      <div className="mx-auto max-w-[1400px] px-6 md:px-10">
        {/* Section headline */}
        <h2 className="text-center font-bebas uppercase text-snow [font-size:clamp(40px,4vw,72px)]">
          From flat lines to physical form.
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-center font-inter text-[15px] leading-relaxed text-stone">
          Maps haven&rsquo;t changed in centuries. We rebuilt them from the
          ground up &mdash; starting with the actual shape of the mountain.
        </p>

        {/* Three panels */}
        <div className="relative mt-16 grid grid-cols-1 gap-6 md:grid-cols-3 md:gap-0">
          {PANELS.map((panel, i) => (
            <div key={panel.label} className="flex flex-col items-stretch">
              {/* Image placeholder */}
              <div className="relative flex aspect-[4/3] w-full items-center justify-center bg-alpine/30">
                <span className="label-eyebrow text-stone">[ photo ]</span>

                {/* Arrow connector — shown between panels on desktop */}
                {i < PANELS.length - 1 && (
                  <div
                    className="absolute -right-4 top-1/2 z-10 hidden -translate-y-1/2 md:block"
                    aria-hidden="true"
                  >
                    <svg
                      width="32"
                      height="16"
                      viewBox="0 0 32 16"
                      fill="none"
                      className="text-trail"
                    >
                      <path
                        d="M0 8H28M28 8L22 2M28 8L22 14"
                        stroke="currentColor"
                        strokeWidth="2"
                      />
                    </svg>
                  </div>
                )}
              </div>

              {/* Label */}
              <div className="mt-5 px-1 md:px-6">
                <p className="font-bebas text-[22px] uppercase leading-none text-snow">
                  {panel.label}
                </p>
                <p className="mt-2 font-inter text-[13px] leading-relaxed text-stone">
                  {panel.caption}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
