export default function Hero() {
  return (
    <section className="relative min-h-screen w-full bg-snow">
      <div className="flex min-h-screen flex-col md:flex-row">
        {/* Left — full-bleed product photo area (60%) */}
        <div className="relative flex min-h-[55vh] w-full items-center justify-center bg-slate md:min-h-screen md:w-[60%]">
          <span className="label-eyebrow text-stone">[ product photo ]</span>
          {/* subtle corner registration marks for an editorial / print feel */}
          <span className="absolute left-6 top-20 h-4 w-4 border-l border-t border-stone/40 md:top-24" />
          <span className="absolute bottom-6 right-6 h-4 w-4 border-b border-r border-stone/40" />
        </div>

        {/* Right — text column (40%) */}
        <div className="flex w-full items-center md:w-[40%]">
          <div className="w-full px-6 pb-16 pt-28 md:px-12 md:py-0 md:pl-12">
            <p className="label-eyebrow">3D Topographic Trail Maps</p>

            <h1 className="mt-6 font-bebas uppercase text-slate [font-size:clamp(64px,6vw,96px)]">
              The mountain,
              <br />
              in your hands.
            </h1>

            <hr className="my-8 w-full border-0 border-t border-stone/40" />

            <p className="max-w-md font-inter text-[16px] leading-relaxed text-stone">
              For 5,000 years, maps were flat. We changed that. Every trail,
              every ridge, every vertical foot — rendered in physical form and
              printed in the exact colors you know on the mountain.
            </p>

            <a
              href="#preview"
              className="group mt-10 inline-flex items-center border-2 border-slate bg-transparent px-8 py-4 transition-colors duration-200 hover:bg-slate"
            >
              <span className="label-nav text-slate transition-colors duration-200 group-hover:text-snow">
                Preview Your Mountain&nbsp;&rarr;
              </span>
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
