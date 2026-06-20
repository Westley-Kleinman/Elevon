// Shared category system for the 4-color map layer toggles. The physical printer
// lays a white base plus exactly 3 selectable colors, so customers pick 3 of
// these 4 layers. Kept in one module so MapPreview, TrailPreview, and TerrainMesh
// agree on the categories, colors, and difficulty→category mapping.

export type Category = 'green' | 'blue' | 'black' | 'lifts'

export const LIFT_COLOR = '#C8372D' // matches the site's `trail` red token

export const CATEGORY_COLOR: Record<Category, string> = {
  green: '#4A7C3C',
  blue: '#2C4A6E',
  black: '#1A1A1A',
  lifts: LIFT_COLOR,
}

// Default 3 active on selection (current behavior): green, blue, black.
export const DEFAULT_CATEGORIES: Category[] = ['green', 'blue', 'black']

// Map a trail difficulty to its toggle category. 'other' returns null — it has
// no color channel in the 4-color print model, so it isn't toggle-controlled.
export function difficultyCategory(difficulty: string): Category | null {
  if (difficulty === 'easy') return 'green'
  if (difficulty === 'intermediate') return 'blue'
  if (difficulty === 'advanced') return 'black'
  return null
}

export interface LiftLine {
  name: string | null
  coordinates: number[][]
  rawCoordinates: number[][]
}

export interface LiftData {
  bounds: { width: number; height: number }
  lifts: LiftLine[]
}
