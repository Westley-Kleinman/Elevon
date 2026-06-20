const COLUMNS = [
  {
    number: '01',
    title: 'Your Mountain',
    body: 'Any ski resort in the world. You name it, we map it. From Vail to a local hill no one\u2019s ever heard of.',
  },
  {
    number: '02',
    title: 'Four-Color Precision',
    body: 'Trails printed in their actual colors \u2014 green, blue, black, double-black \u2014 exactly as they appear on the mountain\u2019s trail map.',
  },
  {
    number: '03',
    title: 'Physical Depth',
    body: 'Real topographic relief. You can feel the steepness. Each layer is a true elevation contour, not a decorative pattern.',
  },
]

export default function WhatIsThis() {
  return (
    <section id="what" className="w-full bg-slate py-32">
      <div className="mx-auto max-w-[1400px] px-6 md:px-10">
        <h2 className="text-center font-bebas uppercase text-snow [font-size:clamp(48px,5vw,84px)]">
          Not a poster. Not a print.
        </h2>

        <div className="mt-20 grid grid-cols-1 gap-x-12 gap-y-16 md:grid-cols-3">
          {COLUMNS.map((col) => (
            <div key={col.number} className="max-w-sm">
              <div className="font-bebas text-[72px] leading-none text-trail">
                {col.number}
              </div>
              <h3 className="mt-3 font-bebas text-[32px] uppercase leading-none text-snow">
                {col.title}
              </h3>
              <p className="mt-4 font-inter text-[15px] leading-relaxed text-stone">
                {col.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
