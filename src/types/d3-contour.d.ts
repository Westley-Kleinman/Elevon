// Minimal local typings for d3-contour (the package ships no .d.ts).
// Covers only the surface we use: contours().size().thresholds()(values).
declare module 'd3-contour' {
  /** GeoJSON-style MultiPolygon emitted per threshold. */
  export interface ContourMultiPolygon {
    type: 'MultiPolygon'
    /** The threshold (elevation) value this contour band represents. */
    value: number
    /** Polygons -> rings -> positions ([x, y] pairs in grid pixel space). */
    coordinates: number[][][][]
  }

  export interface Contours {
    (values: ArrayLike<number>): ContourMultiPolygon[]
    size(size: [number, number]): this
    smooth(smooth: boolean): this
    thresholds(thresholds: number[] | number): this
  }

  export function contours(): Contours
}
