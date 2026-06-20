// GeoPackage / WKB LineString + MultiLineString parsing, extracted verbatim from
// the proven extract-trails.mjs logic so trail and lift extraction share one
// implementation. Handles GP header + envelope skipping, little/big endian, and
// both EWKB and ISO-WKB Z/M dimensionality (the geomType masking fix).

export function parseGpkgGeometry(blob) {
  if (blob[0] !== 0x47 || blob[1] !== 0x50) return null // not 'GP' magic

  const flags = blob[3]
  const envelopeIndicator = (flags >> 1) & 0x07
  const envelopeSizes = [0, 32, 48, 48, 64]
  const envelopeBytes = envelopeSizes[envelopeIndicator] ?? 0

  const wkbStart = 8 + envelopeBytes
  return parseWkb(blob, wkbStart)
}

// Decode a WKB geometry type integer into its base type plus dimensionality.
// Handles both EWKB (high-bit flags 0x80000000 = Z, 0x40000000 = M) and
// ISO WKB (type + 1000 = Z, + 2000 = M, + 3000 = ZM).
export function decodeGeomType(geomType) {
  let hasZ = (geomType & 0x80000000) !== 0
  let hasM = (geomType & 0x40000000) !== 0

  // Strip EWKB flag bits, leaving the (possibly ISO-encoded) base value.
  let g = geomType & 0x0fffffff

  if (g >= 1000) {
    const thousand = Math.floor(g / 1000)
    if (thousand === 1) hasZ = true
    else if (thousand === 2) hasM = true
    else if (thousand === 3) { hasZ = true; hasM = true }
    g = g % 1000
  }

  return { baseType: g, hasZ, hasM }
}

export function parseWkb(blob, offset) {
  const view = new DataView(blob.buffer, blob.byteOffset, blob.byteLength)
  const byteOrder = view.getUint8(offset)
  const little = byteOrder === 1
  let pos = offset + 1

  const geomType = view.getUint32(pos, little)
  pos += 4

  const { baseType, hasZ, hasM } = decodeGeomType(geomType)

  const lines = []

  // Number of extra ordinates per point beyond X/Y (e.g. Z elevation, M measure).
  // Ski-run/lift geometries are 3D, so each point is X,Y,Z (24 bytes) — we must
  // read and discard the extra ordinates or every subsequent point misaligns.
  function readLineString(isLittle, extraOrdinates) {
    const numPoints = view.getUint32(pos, isLittle); pos += 4
    const pts = []
    for (let i = 0; i < numPoints; i++) {
      const x = view.getFloat64(pos, isLittle); pos += 8
      const y = view.getFloat64(pos, isLittle); pos += 8
      pos += extraOrdinates * 8 // skip Z and/or M
      pts.push([x, y])
    }
    return pts
  }

  const extra = (hasZ ? 1 : 0) + (hasM ? 1 : 0)

  if (baseType === 2) {
    lines.push(readLineString(little, extra))
  } else if (baseType === 5) {
    const numLines = view.getUint32(pos, little); pos += 4
    for (let i = 0; i < numLines; i++) {
      const innerByteOrder = view.getUint8(pos); pos += 1
      const innerLittle = innerByteOrder === 1
      const innerType = view.getUint32(pos, innerLittle); pos += 4
      const innerDims = decodeGeomType(innerType)
      const innerExtra = (innerDims.hasZ ? 1 : 0) + (innerDims.hasM ? 1 : 0)
      lines.push(readLineString(innerLittle, innerExtra))
    }
  } else {
    return null
  }

  return lines
}
