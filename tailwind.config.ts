import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/app/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        snow: '#F4F1ED',
        slate: '#0F1923',
        alpine: '#2C4A6E',
        trail: '#C8372D',
        // Darkened from the original #8C8880 (~3.1:1 on snow, failed WCAG AA) to
        // ~4.9:1 so small body/label text meets the 4.5:1 contrast minimum.
        stone: '#6B6862',
      },
      fontFamily: {
        bebas: ['var(--font-bebas)', 'Bebas Neue', 'sans-serif'],
        inter: ['var(--font-inter)', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
