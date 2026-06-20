import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

export const metadata = {
  title: 'About — ELEVON',
}

const TIMELINE = [
  {
    year: '2021',
    title: 'Elevon Founded',
    body: 'Started making 3D trail maps for NICA Arkansas at 15. First map was for a mountain bike race course.',
  },
  {
    year: '2023',
    title: 'Pan-American Games',
    body: 'Represented MaccabiUSA at the Pan-American Maccabi Games in Buenos Aires, Argentina for cycling.',
  },
  {
    year: '2024',
    title: 'Duke University',
    body: 'Started B.S. Mechanical Engineering with an Innovation & Entrepreneurship certificate. Became President of Duke Club Cycling.',
  },
  {
    year: '2025',
    title: 'Boyd Cycling Internship',
    body: 'Interned at Boyd Cycling & Time Bicycles. Engineered a carbon rim impact tester in a 72-hour design-build sprint.',
  },
  {
    year: '2025',
    title: 'Re:3D — Austin',
    body: 'R&D internship at Re:3D, printing with recycled materials on large-format pellet systems. Pushing what\u2019s possible with sustainable additive manufacturing.',
  },
  {
    year: '2025',
    title: 'Elevon Launches',
    body: 'The maps go online. Any ski resort in the world, shipped to your door.',
  },
]

export default function AboutPage() {
  return (
    <main className="bg-snow">
      <Nav />

      {/* Section 1 — Hero strip */}
      <section className="w-full bg-slate pt-28 md:pt-20">
        <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-center gap-12 px-6 py-24 md:grid-cols-2 md:gap-16 md:px-10">
          <h1 className="font-bebas uppercase text-snow [font-size:clamp(48px,5.5vw,92px)]">
            Built by someone who&rsquo;s actually been on the mountain
          </h1>

          <div className="flex h-[400px] items-center justify-center border border-stone/20 bg-slate">
            <span className="label-eyebrow text-stone">[ founder photo ]</span>
          </div>
        </div>
      </section>

      {/* Section 2 — Story */}
      <section className="w-full bg-snow py-24">
        <div className="mx-auto max-w-3xl px-6">
          <p className="font-inter text-[17px] leading-loose text-stone">
            I&rsquo;m Westley Kleinman &mdash; a mechanical engineering student at
            Duke University and the founder of Elevon. I started making 3D
            topographic maps at 15 for NICA Arkansas so mountain bikers could
            actually visualize the trail systems they were racing on. What
            started as a local project turned into something I couldn&rsquo;t stop
            building.
          </p>

          <p className="mt-8 font-inter text-[17px] leading-loose text-stone">
            This summer I&rsquo;m working in R&amp;D at Re:3D in Austin, Texas &mdash;
            printing with recycled plastics on large-format pellet systems and
            testing materials most people haven&rsquo;t figured out yet. It&rsquo;s made
            me a better printer and a better engineer. Elevon is what happens
            when that obsession meets the mountains.
          </p>

          <hr className="my-12 w-full border-0 border-t border-stone/20" />

          <p className="font-inter text-[17px] leading-loose text-stone">
            I&rsquo;ve competed in cycling at the Pan-American Maccabi Games in
            Buenos Aires, served as President of Duke Cycling, and interned at
            Boyd Cycling &amp; Time Bicycles where I built a carbon rim impact
            tester from scratch in 72 hours. I care about things that are made
            well and built to last &mdash; which is exactly what these maps are.
          </p>

          <p className="mt-16 font-bebas uppercase text-slate [font-size:clamp(32px,3.5vw,52px)]">
            Every map is made by hand. By me. In my shop.
          </p>
        </div>
      </section>

      {/* Section 3 — Timeline */}
      <section className="w-full bg-snow pb-32">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <h2 className="text-center font-bebas uppercase text-slate [font-size:clamp(48px,5vw,84px)]">
            The Story So Far
          </h2>

          <div className="relative mt-20 grid grid-cols-1 gap-y-12 md:grid-cols-6 md:gap-x-8">
            <div className="pointer-events-none absolute left-0 right-0 top-[7px] hidden border-t border-slate/20 md:block" />

            {TIMELINE.map((entry, i) => (
              <div key={i} className="relative bg-snow md:pr-4">
                <div className="flex items-center gap-3">
                  <span className="block h-[14px] w-[14px] rounded-full bg-snow ring-1 ring-slate/20" />
                  <span className="font-bebas text-[28px] leading-none text-trail">
                    {entry.year}
                  </span>
                </div>
                <h3 className="mt-5 font-inter text-[16px] font-medium leading-snug text-slate">
                  {entry.title}
                </h3>
                <p className="mt-3 font-inter text-[14px] leading-relaxed text-stone">
                  {entry.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 4 — Closing CTA */}
      <section className="w-full bg-slate py-20">
        <div className="mx-auto max-w-[1400px] px-6 text-center md:px-10">
          <h2 className="font-bebas uppercase text-snow [font-size:clamp(44px,5vw,80px)]">
            Want to know more?
          </h2>
          <p className="mt-5 font-inter text-[16px] leading-relaxed text-stone">
            Reach out directly &mdash; I answer my own email.
          </p>

          <a
            href="mailto:westley.kleinman@duke.edu"
            className="group mt-10 inline-flex items-center border-2 border-snow bg-transparent px-8 py-4 transition-colors duration-200 hover:bg-snow"
          >
            <span className="label-nav text-snow transition-colors duration-200 group-hover:text-slate">
              westley.kleinman@duke.edu
            </span>
          </a>

          <p className="mt-8 font-inter text-[13px] text-stone">
            Or check out the full portfolio at{' '}
            <a
              href="https://westleykleinman.com"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-4 transition-colors duration-200 hover:text-snow"
            >
              westleykleinman.com
            </a>
          </p>
        </div>
      </section>

      <Footer />
    </main>
  )
}
