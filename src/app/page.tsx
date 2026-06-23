import Nav from '@/components/Nav'
import Hero from '@/components/Hero'
import EvolutionStrip from '@/components/EvolutionStrip'
import WhatIsThis from '@/components/WhatIsThis'
import PreviewSection from '@/components/PreviewSection'
import HowItWorks from '@/components/HowItWorks'
import Footer from '@/components/Footer'

function PhotoStrip() {
  return (
    <section className="grid w-full grid-cols-1 md:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="flex h-[400px] items-center justify-center bg-slate"
        >
          <span className="label-eyebrow text-stone">[ photo ]</span>
        </div>
      ))}
    </section>
  )
}

export default function Home() {
  return (
    <main>
      <Nav />
      <Hero />
      <EvolutionStrip />
      <WhatIsThis />
      <PreviewSection />
      <HowItWorks />
      <PhotoStrip />
      <Footer />
    </main>
  )
}
