export default function Footer() {
  return (
    <footer className="w-full bg-slate">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-center gap-8 px-6 py-16 md:grid-cols-3 md:px-10">
        <div>
          <div className="font-bebas text-[28px] leading-none tracking-wide text-snow">
            ELEVON
          </div>
          <p className="mt-2 font-inter text-[13px] text-stone">
            The mountain, in your hands.
          </p>
        </div>

        <div className="font-inter text-[11px] uppercase tracking-[0.2em] text-stone md:text-center">
          &copy; 2025 Elevon
        </div>

        <div className="md:text-right">
          <a
            href="mailto:hello@elevon.com"
            className="font-inter text-[13px] text-stone transition-colors duration-200 hover:text-snow"
          >
            hello@elevon.com
          </a>
        </div>
      </div>
    </footer>
  )
}
