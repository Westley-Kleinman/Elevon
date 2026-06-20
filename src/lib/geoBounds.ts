export interface Bounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

/**
 * Expand a raw lat/lng extent into a bounding box that is square in TRUE
 * PHYSICAL terms (equal distance on the ground in both axes), centered on the
 * same midpoint.
 *
 * Steps:
 *   1. Pad each side by `paddingPercent` of that axis' span (matches the old
 *      TRAIL_BBOX_PADDING behavior).
 *   2. Measure the padded lat span (height) and lng span.
 *   3. Longitude degrees shrink with latitude: 1° lng ≈ cos(lat) × 1° lat in
 *      physical width. Convert the lng span to a relative physical width.
 *   4. The larger physical dimension becomes the target. Expand the smaller one
 *      (back in degree-space, undoing the cosine for longitude) so both axes
 *      cover the same physical distance.
 *   5. Re-center on the original midpoint and return the square box.
 *
 * The cosine uses the center latitude — exact enough for resort-scale boxes.
 */
export function squareBounds(
  minLat: number,
  maxLat: number,
  minLng: number,
  maxLng: number,
  paddingPercent: number,
): Bounds {
  // 1. Pad each side by a fraction of its own span.
  const latPad = (maxLat - minLat) * paddingPercent
  const lngPad = (maxLng - minLng) * paddingPercent
  const pMinLat = minLat - latPad
  const pMaxLat = maxLat + latPad
  const pMinLng = minLng - lngPad
  const pMaxLng = maxLng + lngPad

  // 2. Padded spans + center.
  const latSpan = pMaxLat - pMinLat
  const lngSpan = pMaxLng - pMinLng
  const centerLat = (pMinLat + pMaxLat) / 2
  const centerLng = (pMinLng + pMaxLng) / 2

  // 3. Relative physical sizes (latitude is the unit; longitude is scaled down).
  const cosLat = Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6)
  const physWidth = lngSpan * cosLat
  const physHeight = latSpan

  // 4. Grow the shorter physical side up to the longer one.
  const target = Math.max(physWidth, physHeight)
  const newLatSpan = target // physHeight = latSpan directly
  const newLngSpan = target / cosLat // undo cosine to get lng degrees

  // 5. Re-center.
  return {
    minLat: centerLat - newLatSpan / 2,
    maxLat: centerLat + newLatSpan / 2,
    minLng: centerLng - newLngSpan / 2,
    maxLng: centerLng + newLngSpan / 2,
  }
}
