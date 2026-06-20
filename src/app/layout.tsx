import type { Metadata } from 'next'
import { Bebas_Neue, Inter } from 'next/font/google'
import '@/styles/globals.css'

const bebas = Bebas_Neue({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-bebas',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'ELEVON — The mountain, in your hands.',
  description:
    'ELEVON makes custom 3D-printed topographic trail maps of any ski resort in the world, with every trail printed in its true color. $49.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${bebas.variable} ${inter.variable}`}>
      <body className="bg-snow text-slate font-inter antialiased">
        {children}
      </body>
    </html>
  )
}
