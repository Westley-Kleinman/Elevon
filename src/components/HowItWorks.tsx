const STEPS = [
  {
    number: '1',
    title: 'Choose Your Mountain',
    body: 'Search any resort on earth. If skiers ride it, we can map it.',
  },
  {
    number: '2',
    title: 'We Build the Model',
    body: 'We translate elevation data and the official trail map into a print-ready relief.',
  },
  {
    number: '3',
    title: '4-Color Print',
    body: 'Printed on a Bambu P1S in white, with trails in green, blue, black, and double-black.',
  },
  {
    number: '4',
    title: 'Ships to You',
    body: 'Carefully packed and on its way within 5\u20137 days.',
  },
]

export default function HowItWorks() {
  return (
    <section id="how" className="w-full bg-snow py-32">
      <div className="mx-auto max-w-[1400px] px-6 md:px-10">
        <h2 className="text-center font-bebas uppercase text-slate [font-size:clamp(48px,5vw,84px)]">
          How It Works
        </h2>

        <div className="relative mt-20 grid grid-cols-1 gap-y-12 md:grid-cols-4 md:gap-x-10">
          {/* connecting line across steps on desktop */}
          <div className="pointer-events-none absolute left-0 right-0 top-[7px] hidden border-t border-slate/20 md:block" />

          {STEPS.map((step) => (
            <div key={step.number} className="relative bg-snow md:pr-6">
              <div className="flex items-center gap-3">
                <span className="block h-[14px] w-[14px] rounded-full bg-snow ring-1 ring-slate/20" />
                <span className="font-inter text-[12px] font-semibold uppercase tracking-[0.18em] text-trail">
                  Step {step.number}
                </span>
              </div>
              <h3 className="mt-5 font-inter text-[18px] font-medium leading-snug text-slate">
                {step.title}
              </h3>
              <p className="mt-3 font-inter text-[14px] leading-relaxed text-stone">
                {step.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
