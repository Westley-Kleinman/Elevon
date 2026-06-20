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
        stone: '#8C8880',
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
