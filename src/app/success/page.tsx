import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

export const metadata = {
  title: "You're on the map — ELEVON",
}

export default function SuccessPage() {
  return (
    <main className="flex min-h-screen flex-col bg-snow">
      <Nav />

      <section className="flex flex-1 items-center justify-center px-6 py-32">
        <div className="max-w-xl text-center">
          <h1 className="font-bebas uppercase text-slate [font-size:clamp(56px,7vw,108px)]">
            You&rsquo;re on the map.
          </h1>

          <p className="mx-auto mt-6 max-w-md font-inter text-[16px] leading-relaxed text-stone">
            We&rsquo;ll reach out within 24 hours to confirm your mountain and
            get started. Check your email for a receipt from Stripe.
          </p>

          <Link
            href="/"
            className="group mt-10 inline-flex items-center border-2 border-slate bg-transparent px-8 py-4 transition-colors duration-200 hover:bg-slate"
          >
            <span className="label-nav text-slate transition-colors duration-200 group-hover:text-snow">
              Back to Home
            </span>
          </Link>
        </div>
      </section>

      <Footer />
    </main>
  )
}
