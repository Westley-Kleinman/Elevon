// Mirror of src/lib/geoBounds.ts — keep the math identical between the two.
// Expands a raw lat/lng extent into a box that is square in TRUE PHYSICAL terms
// (equal ground distance in both axes), centered on the same midpoint.
export function squareBounds(minLat, maxLat, minLng, maxLng, paddingPercent) {
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

  // 3. Relative physical sizes (latitude is the unit; longitude scaled down).
  const cosLat = Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6)
  const physWidth = lngSpan * cosLat
  const physHeight = latSpan

  // 4. Grow the shorter physical side up to the longer one.
  const target = Math.max(physWidth, physHeight)
  const newLatSpan = target
  const newLngSpan = target / cosLat

  // 5. Re-center.
  return {
    minLat: centerLat - newLatSpan / 2,
    maxLat: centerLat + newLatSpan / 2,
    minLng: centerLng - newLngSpan / 2,
    maxLng: centerLng + newLngSpan / 2,
  }
}
