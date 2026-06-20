'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Line } from '@react-three/drei'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import {
  type Category,
  type LiftLine,
  LIFT_COLOR,
  DEFAULT_CATEGORIES,
  difficultyCategory,
} from '@/lib/mapCategories'

interface TrailLine {
  difficulty: string
  rawCoordinates: number[][]
}

interface Bounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

interface TerrainMeshProps {
  gridWidth: number
  gridHeight: number
  elevations: number[]
  minElevation: number
  maxElevation: number
  trails: TrailLine[] | null
  // The actual bounding box the elevation grid corresponds to (returned by the
  // API as usedBounds). Both terrain and trails share this exact box.
  usedBounds: Bounds
  // Multiplier on the base vertical scaling. 1.0 = default look, 2.0 = twice as
  // tall, 0.5 = flatter. Cheap to change — only re-displaces the mesh, no refetch.
  heightExaggeration?: number
  // Active map-color layers; only matching trails (and lifts) are draped.
  // Defaults to green/blue/black when omitted (e.g. the /test-3d page).
  activeCategories?: Category[]
  // Lift geometry (raw [lng, lat]) to drape in red when the "lifts" layer is
  // active. null/undefined = none.
  lifts?: LiftLine[] | null
}

// Footprint of the terrain in 3D units (longest side). The shorter side is
// scaled to preserve the grid's aspect ratio.
const PLANE_SIZE = 10
// Visual height range the elevation span is mapped into. Real meters would look
// absurd, so we normalize min..max elevation into 0..HEIGHT_RANGE units.
const HEIGHT_RANGE = 2
// How far the solid base extends below the lowest terrain point (mesh units).
// Enough to read as a substantial printed block, not a paper-thin slab.
const BASE_DEPTH = 0.6
// Lift trails slightly above the surface to avoid z-fighting / clipping.
const TRAIL_Y_OFFSET = 0.02
// Moving-average passes applied to raw GPS coords to shave off zigzag noise.
// Kept light (1) so we de-noise without flattening the real trail shape.
const TRAIL_SMOOTH_PASSES = 1
// Max distance (mesh units) between consecutive draped points. Longer source
// segments are linearly subdivided so the line hugs terrain bumps instead of
// cutting straight through them. ~0.1 roughly matches one terrain grid cell.
const MAX_TRAIL_SEGMENT = 0.1

// Zoom-responsive trail width (screen px). Width tracks 1/cameraDistance so lines
// keep a constant size RELATIVE to the terrain: subtle when zoomed out, thicker
// as you zoom in, clamped so they never vanish or balloon.
const TRAIL_REF_DIST = 15 // ≈ |initial camera position [9,8,9]|
const TRAIL_BASE_PX = 1.6 // width at the default zoom — intentionally slim
const TRAIL_MIN_PX = 0.7
const TRAIL_MAX_PX = 4.5

const TRAIL_COLOR: Record<string, string> = {
  easy: '#4A7C3C',
  intermediate: '#2C4A6E',
  advanced: '#1A1A1A',
  other: '#8C8880',
}

const colorFor = (d: string) => TRAIL_COLOR[d] ?? TRAIL_COLOR.other

// Footprint of the terrain plane in mesh units, proportioned to the box's TRUE
// physical shape (longitude degrees shrink by cos(lat)). The longest physical
// side maps to PLANE_SIZE; the other is scaled down. This keeps the terrain and
// trails un-stretched regardless of latitude or box aspect.
function planeDims(b: Bounds) {
  const centerLat = (b.minLat + b.maxLat) / 2
  const cosLat = Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6)
  const physWidth = (b.maxLng - b.minLng) * cosLat
  const physHeight = b.maxLat - b.minLat || 1
  if (physWidth >= physHeight) {
    return { planeWidth: PLANE_SIZE, planeHeight: (PLANE_SIZE * physHeight) / physWidth }
  }
  return { planeWidth: (PLANE_SIZE * physWidth) / physHeight, planeHeight: PLANE_SIZE }
}

// Moving-average smoothing over a polyline of [lng, lat] points. Endpoints are
// preserved; each interior point is averaged with its immediate neighbors.
// Runs `passes` times for slightly stronger (but still shape-preserving) results.
function smoothCoords(coords: number[][], passes: number): number[][] {
  if (coords.length < 3 || passes <= 0) return coords
  let out = coords
  for (let p = 0; p < passes; p++) {
    const next: number[][] = [out[0]]
    for (let i = 1; i < out.length - 1; i++) {
      const [aLng, aLat] = out[i - 1]
      const [bLng, bLat] = out[i]
      const [cLng, cLat] = out[i + 1]
      next.push([(aLng + bLng + cLng) / 3, (aLat + bLat + cLat) / 3])
    }
    next.push(out[out.length - 1])
    out = next
  }
  return out
}

function Terrain({
  gridWidth,
  gridHeight,
  elevations,
  minElevation,
  maxElevation,
  heightExaggeration,
  usedBounds,
}: {
  gridWidth: number
  gridHeight: number
  elevations: number[]
  minElevation: number
  maxElevation: number
  heightExaggeration: number
  usedBounds: Bounds
}) {
  const geometry = useMemo(() => {
    const { planeWidth, planeHeight } = planeDims(usedBounds)
    const range = maxElevation - minElevation || 1
    const heightSpan = HEIGHT_RANGE * heightExaggeration

    const dw = gridWidth > 1 ? gridWidth - 1 : 1
    const dh = gridHeight > 1 ? gridHeight - 1 : 1

    // Final WORLD-space position of a top-surface grid vertex. Built directly in
    // the same centered space the old rotate/center produced (top Y spans
    // [-heightSpan/2, +heightSpan/2]) so trail draping stays aligned untouched.
    const xAt = (gx: number) => -planeWidth / 2 + (gx / dw) * planeWidth
    const zAt = (gy: number) => -planeHeight / 2 + (gy / dh) * planeHeight
    const yAt = (gx: number, gy: number) => {
      const elevation = elevations[gy * gridWidth + gx] ?? minElevation
      const normalized = ((elevation - minElevation) / range) * heightSpan
      return normalized - heightSpan / 2
    }

    const positions: number[] = []
    const indices: number[] = []
    let vCount = 0

    // --- TOP SURFACE: full displaced grid, faces up (+Y) ---
    let minTopY = Infinity
    for (let gy = 0; gy < gridHeight; gy++) {
      for (let gx = 0; gx < gridWidth; gx++) {
        const y = yAt(gx, gy)
        if (y < minTopY) minTopY = y
        positions.push(xAt(gx), y, zAt(gy))
      }
    }
    vCount = gridWidth * gridHeight
    const topIdx = (gx: number, gy: number) => gy * gridWidth + gx
    for (let gy = 0; gy < gridHeight - 1; gy++) {
      for (let gx = 0; gx < gridWidth - 1; gx++) {
        const v00 = topIdx(gx, gy)
        const v10 = topIdx(gx + 1, gy)
        const v01 = topIdx(gx, gy + 1)
        const v11 = topIdx(gx + 1, gy + 1)
        // CCW-from-above winding (verified to yield +Y normals).
        indices.push(v00, v11, v10)
        indices.push(v00, v01, v11)
      }
    }

    const baseY = minTopY - BASE_DEPTH

    // --- BOTTOM: a single flat quad at baseY, faces down (-Y) ---
    const xMin = xAt(0)
    const xMax = xAt(gridWidth - 1)
    const zMin = zAt(0)
    const zMax = zAt(gridHeight - 1)
    const cBase = vCount
    positions.push(xMin, baseY, zMin) // +0
    positions.push(xMax, baseY, zMin) // +1
    positions.push(xMin, baseY, zMax) // +2
    positions.push(xMax, baseY, zMax) // +3
    vCount += 4
    indices.push(cBase + 0, cBase + 1, cBase + 3)
    indices.push(cBase + 0, cBase + 3, cBase + 2)

    // --- SIDE WALLS: one quad per perimeter segment, own vertices (hard edges).
    // patternA front-faces for N/E edges; the reverse (patternA=false) for S/W.
    const addWall = (
      p0: [number, number, number],
      p1: [number, number, number],
      patternA: boolean,
    ) => {
      const base = vCount
      positions.push(p0[0], p0[1], p0[2]) // t0  base+0
      positions.push(p1[0], p1[1], p1[2]) // t1  base+1
      positions.push(p0[0], baseY, p0[2]) // b0  base+2
      positions.push(p1[0], baseY, p1[2]) // b1  base+3
      vCount += 4
      if (patternA) {
        indices.push(base + 0, base + 1, base + 3)
        indices.push(base + 0, base + 3, base + 2)
      } else {
        indices.push(base + 0, base + 3, base + 1)
        indices.push(base + 0, base + 2, base + 3)
      }
    }

    // North edge (gy=0, outward -Z), traverse +X — patternA.
    for (let gx = 0; gx < gridWidth - 1; gx++) {
      addWall(
        [xAt(gx), yAt(gx, 0), zMin],
        [xAt(gx + 1), yAt(gx + 1, 0), zMin],
        true,
      )
    }
    // South edge (gy=H-1, outward +Z), traverse +X — patternB.
    for (let gx = 0; gx < gridWidth - 1; gx++) {
      addWall(
        [xAt(gx), yAt(gx, gridHeight - 1), zMax],
        [xAt(gx + 1), yAt(gx + 1, gridHeight - 1), zMax],
        false,
      )
    }
    // East edge (gx=W-1, outward +X), traverse +Z — patternA.
    for (let gy = 0; gy < gridHeight - 1; gy++) {
      addWall(
        [xMax, yAt(gridWidth - 1, gy), zAt(gy)],
        [xMax, yAt(gridWidth - 1, gy + 1), zAt(gy + 1)],
        true,
      )
    }
    // West edge (gx=0, outward -X), traverse +Z — patternB.
    for (let gy = 0; gy < gridHeight - 1; gy++) {
      addWall(
        [xMin, yAt(0, gy), zAt(gy)],
        [xMin, yAt(0, gy + 1), zAt(gy + 1)],
        false,
      )
    }

    const geo = new THREE.BufferGeometry()
    geo.setAttribute(
      'position',
      new THREE.BufferAttribute(new Float32Array(positions), 3),
    )
    geo.setIndex(indices)
    // Winding is set so every group is front-facing from outside; with each
    // group using its own vertices, this yields smooth top + hard wall/base edges.
    geo.computeVertexNormals()

    return geo
  }, [gridWidth, gridHeight, elevations, minElevation, maxElevation, heightExaggeration, usedBounds])

  return (
    <mesh geometry={geometry}>
      {/* Matte near-white "printed plastic" look — shading comes from normals
          under the directional light, no textures or color. */}
      <meshStandardMaterial color="#F4F1ED" roughness={0.85} metalness={0} />
    </mesh>
  )
}

function Trails({
  trails,
  gridWidth,
  gridHeight,
  elevations,
  minElevation,
  maxElevation,
  usedBounds,
  heightExaggeration,
  activeCategories,
  lifts,
}: Required<Pick<TerrainMeshProps,
  | 'trails'
  | 'gridWidth'
  | 'gridHeight'
  | 'elevations'
  | 'minElevation'
  | 'maxElevation'
  | 'usedBounds'
  | 'heightExaggeration'
>> & { activeCategories: Category[]; lifts: LiftLine[] | null }) {
  // Map each [lng, lat] trail point into the SAME centered mesh coordinate space
  // the terrain uses (see Terrain: PlaneGeometry -> rotateX(-90) -> center()).
  // X/Z are unaffected by center() (symmetric), only Y shifts by heightSpan/2.
  const lines = useMemo(() => {
    const { minLat, maxLat, minLng, maxLng } = usedBounds
    const { planeWidth, planeHeight } = planeDims(usedBounds)
    const range = maxElevation - minElevation || 1
    const heightSpan = HEIGHT_RANGE * heightExaggeration
    const lngSpan = maxLng - minLng || 1
    const latSpan = maxLat - minLat || 1

    const clamp = (v: number, lo: number, hi: number) =>
      Math.max(lo, Math.min(hi, v))

    // Fraction (0..1) across the bbox -> centered mesh X/Z (height added later).
    // Row 0 of the raster = north = maxLat, so fy grows southward.
    const toMeshXZ = (fx: number, fy: number) => ({
      x: -planeWidth / 2 + fx * planeWidth,
      z: -planeHeight / 2 + fy * planeHeight,
    })

    // Bilinear height sample: blend the four surrounding grid vertices by
    // fractional distance instead of snapping to the nearest one. Returns the
    // final mesh-space Y (normalized + offset).
    const sampleMeshY = (fx: number, fy: number) => {
      const gxf = clamp(fx, 0, 1) * (gridWidth - 1)
      const gyf = clamp(fy, 0, 1) * (gridHeight - 1)
      const gx0 = Math.floor(gxf)
      const gy0 = Math.floor(gyf)
      const gx1 = Math.min(gx0 + 1, gridWidth - 1)
      const gy1 = Math.min(gy0 + 1, gridHeight - 1)
      const tx = gxf - gx0
      const ty = gyf - gy0
      const e = (gx: number, gy: number) =>
        elevations[gy * gridWidth + gx] ?? minElevation
      const top = e(gx0, gy0) + (e(gx1, gy0) - e(gx0, gy0)) * tx
      const bot = e(gx0, gy1) + (e(gx1, gy1) - e(gx0, gy1)) * tx
      const elevation = top + (bot - top) * ty
      const normalized = ((elevation - minElevation) / range) * heightSpan
      return normalized - heightSpan / 2 + TRAIL_Y_OFFSET
    }

    // Smooth -> project -> densify -> bilinear-sample a raw [lng, lat] polyline
    // into terrain-following mesh points. Shared by trails AND lifts so both get
    // identical de-noising and surface-hugging treatment.
    const drape = (rawCoordinates: number[][]) => {
      const smoothed = smoothCoords(rawCoordinates, TRAIL_SMOOTH_PASSES)
      const frac = smoothed.map(([lng, lat]) => ({
        fx: (lng - minLng) / lngSpan,
        fy: (maxLat - lat) / latSpan,
      }))
      const dense: { fx: number; fy: number }[] = []
      for (let i = 0; i < frac.length - 1; i++) {
        const a = frac[i]
        const b = frac[i + 1]
        const pa = toMeshXZ(a.fx, a.fy)
        const pb = toMeshXZ(b.fx, b.fy)
        const segLen = Math.hypot(pb.x - pa.x, pb.z - pa.z)
        const steps = Math.max(1, Math.ceil(segLen / MAX_TRAIL_SEGMENT))
        for (let s = 0; s < steps; s++) {
          const t = s / steps
          dense.push({
            fx: a.fx + (b.fx - a.fx) * t,
            fy: a.fy + (b.fy - a.fy) * t,
          })
        }
      }
      if (frac.length > 0) dense.push(frac[frac.length - 1])
      return dense.map(({ fx, fy }) => {
        const { x, z } = toMeshXZ(fx, fy)
        return [x, sampleMeshY(fx, fy), z] as [number, number, number]
      })
    }

    const result: { color: string; points: [number, number, number][] }[] = []

    // Trails, filtered to active color layers (skip 'other' / inactive).
    for (const trail of trails ?? []) {
      const cat = difficultyCategory(trail.difficulty)
      if (!cat || !activeCategories.includes(cat)) continue
      result.push({ color: colorFor(trail.difficulty), points: drape(trail.rawCoordinates) })
    }

    // Lifts (red), only when the layer is active.
    if (activeCategories.includes('lifts') && lifts) {
      for (const lift of lifts) {
        if (!lift.rawCoordinates || lift.rawCoordinates.length < 2) continue
        result.push({ color: LIFT_COLOR, points: drape(lift.rawCoordinates) })
      }
    }

    return result
  }, [trails, gridWidth, gridHeight, elevations, minElevation, maxElevation, usedBounds, heightExaggeration, activeCategories, lifts])

  // Each drei <Line> wraps a Line2 whose LineMaterial.linewidth is in screen px
  // (worldUnits=false). We mutate it per frame from the camera distance so the
  // lines read at a consistent size relative to the terrain at any zoom.
  const lineRefs = useRef<({ material: { linewidth: number } } | null)[]>([])

  useFrame(({ camera }) => {
    // OrbitControls target is the origin, so distance === |camera.position|.
    const dist = camera.position.length() || TRAIL_REF_DIST
    const width = THREE.MathUtils.clamp(
      (TRAIL_BASE_PX * TRAIL_REF_DIST) / dist,
      TRAIL_MIN_PX,
      TRAIL_MAX_PX,
    )
    const refs = lineRefs.current
    for (let i = 0; i < refs.length; i++) {
      const mat = refs[i]?.material
      if (mat) mat.linewidth = width
    }
  })

  return (
    <group>
      {lines.map((line, i) => (
        <Line
          key={i}
          ref={(el) => {
            lineRefs.current[i] = el as unknown as
              | { material: { linewidth: number } }
              | null
          }}
          points={line.points}
          color={line.color}
          // Starting px width; overridden live by the useFrame controller above.
          lineWidth={TRAIL_BASE_PX}
          dashed={false}
          worldUnits={false}
        />
      ))}
    </group>
  )
}

export default function TerrainMesh(props: TerrainMeshProps) {
  const heightExaggeration = props.heightExaggeration ?? 2.0
  const activeCategories = props.activeCategories ?? DEFAULT_CATEGORIES
  const lifts = props.lifts ?? null
  return (
    <Canvas className="h-full w-full" gl={{ antialias: true }} dpr={[1, 2]}>
      <PerspectiveCamera makeDefault position={[9, 8, 9]} fov={45} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[6, 12, 4]} intensity={1.35} />
      <Terrain
        gridWidth={props.gridWidth}
        gridHeight={props.gridHeight}
        elevations={props.elevations}
        minElevation={props.minElevation}
        maxElevation={props.maxElevation}
        heightExaggeration={heightExaggeration}
        usedBounds={props.usedBounds}
      />
      <Trails
        trails={props.trails}
        gridWidth={props.gridWidth}
        gridHeight={props.gridHeight}
        elevations={props.elevations}
        minElevation={props.minElevation}
        maxElevation={props.maxElevation}
        usedBounds={props.usedBounds}
        heightExaggeration={heightExaggeration}
        activeCategories={activeCategories}
        lifts={lifts}
      />
      <OrbitControls enablePan enableZoom enableRotate target={[0, 0, 0]} />
    </Canvas>
  )
}
