'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

const LINKS = [
  { label: 'The Map', href: '/#what' },
  { label: 'How It Works', href: '/#how' },
  { label: 'About', href: '/about' },
  { label: 'Order', href: '/order' },
]

export default function Nav() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [menuOpen])

  return (
    <>
      <header
        className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
          scrolled || menuOpen
            ? 'bg-snow border-b border-slate/10'
            : 'bg-transparent border-b border-transparent'
        }`}
      >
        <nav className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-6 md:h-20 md:px-10">
          <Link
            href="/"
            className="font-bebas text-[28px] leading-none tracking-wide text-slate"
            onClick={() => setMenuOpen(false)}
          >
            ELEVON
          </Link>

          <div className="hidden items-center gap-10 md:flex">
            {LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="label-nav text-stone transition-colors duration-200 hover:text-slate"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <button
            type="button"
            aria-label="Open menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            className="relative z-50 flex h-6 w-7 flex-col justify-center gap-[5px] md:hidden"
          >
            <span
              className={`block h-[2px] w-full bg-slate transition-transform duration-200 ${
                menuOpen ? 'translate-y-[7px] rotate-45' : ''
              }`}
            />
            <span
              className={`block h-[2px] w-full bg-slate transition-opacity duration-200 ${
                menuOpen ? 'opacity-0' : 'opacity-100'
              }`}
            />
            <span
              className={`block h-[2px] w-full bg-slate transition-transform duration-200 ${
                menuOpen ? '-translate-y-[7px] -rotate-45' : ''
              }`}
            />
          </button>
        </nav>
      </header>

      <div
        className={`fixed inset-0 z-40 bg-slate transition-opacity duration-300 md:hidden ${
          menuOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'
        }`}
      >
        <div className="flex h-full flex-col items-center justify-center gap-8">
          {LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="font-bebas text-5xl uppercase tracking-wide text-snow transition-colors duration-200 hover:text-trail"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </>
  )
}
