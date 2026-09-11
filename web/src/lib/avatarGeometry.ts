import type { Measurements } from './types'

/**
 * Turns real measurements into a to-scale silhouette — every width and
 * length is derived directly from the entered cm values (via one shared
 * scale factor), not from balance-point ratios. No photorealism, per
 * NOTES.md, but the proportions are the user's actual proportions, not an
 * exaggerated schematic. Every function here is pure (no DOM, no React) so
 * the mapping from measurements to shape is unit-testable on its own,
 * independent of how it's eventually rendered.
 */

// Front-view width from a circumference. Treating the cross-section as a
// circle gives width = circumference / pi ≈ circumference * 0.318; a real
// torso is wider than it is deep (an ellipse, not a circle), which pushes
// the width up a bit from that circular baseline, but nowhere near
// circumference * 0.7 — that would mean the body is barely deeper than a
// flat plane. 0.32 keeps the ellipse correction modest and real depth still
// varies by build, so this stays an approximation, not exact.
const WIDTH_FROM_CIRCUMFERENCE = 0.32

// Target total rendered height (SVG units). Every user's figure scales to
// roughly this size regardless of their actual height, so the avatar stays
// a consistent on-screen size while every internal proportion (widths vs.
// torso vs. leg) stays true-to-scale relative to each other.
const TARGET_FIGURE_HEIGHT = 200

// Neck and ankle aren't measured inputs (Measurements has no neck/ankle
// circumference) — drawn as a simple fixed proportion of a nearby measured
// width, for visual completeness only. Not scored, not meant to be
// anthropometrically accurate.
const NECK_TO_SHOULDER_RATIO = 0.45
const ANKLE_TO_HIP_RATIO = 0.3

// Head isn't a measured input either. Rather than size it off the
// (circumference-derived, and so already-inflated) shoulder width, it's
// sized off total figure height using the classic figure-drawing convention
// of a body being ~7.5 head-heights tall — that stays proportionate however
// wide or narrow the rest of the figure is drawn.
const HEAD_HEIGHTS_PER_FIGURE = 7.5
const HEAD_ASPECT_RATIO = 1.3 // head height ≈ 1.3x head width (egg-shaped, taller than wide)

export interface AvatarGeometry {
  widths: {
    neck: number
    shoulder: number
    bust: number
    waist: number
    hip: number
    ankle: number
  }
  head: {
    width: number
    height: number
  }
  torsoHeight: number
  legHeight: number
}

export function computeAvatarGeometry(m: Measurements): AvatarGeometry {
  const scale = TARGET_FIGURE_HEIGHT / m.height
  const widthOf = (circumference: number) => circumference * WIDTH_FROM_CIRCUMFERENCE * scale

  const shoulder = widthOf(m.shoulder)
  const hip = widthOf(m.hip)
  const headHeight = TARGET_FIGURE_HEIGHT / HEAD_HEIGHTS_PER_FIGURE

  return {
    widths: {
      neck: shoulder * NECK_TO_SHOULDER_RATIO,
      shoulder,
      bust: widthOf(m.bust),
      waist: widthOf(m.waist),
      hip,
      ankle: hip * ANKLE_TO_HIP_RATIO,
    },
    head: {
      width: headHeight / HEAD_ASPECT_RATIO,
      height: headHeight,
    },
    torsoHeight: m.torso * scale,
    legHeight: m.leg * scale,
  }
}

export interface Keypoint {
  x: number
  y: number
}

const CENTER_X = 50
const Y_NECK = 5
const Y_SHOULDER = 10

export interface Ellipse {
  cx: number
  cy: number
  rx: number
  ry: number
}

/** Head ellipse, resting with its chin at the neck keypoint. */
export function headEllipse(geometry: AvatarGeometry): Ellipse {
  const rx = geometry.head.width / 2
  const ry = geometry.head.height / 2
  return { cx: CENTER_X, cy: Y_NECK - ry, rx, ry }
}

/** Right-half keypoints, top to bottom, mirrored to build the full outline. */
export function avatarOutline(geometry: AvatarGeometry): Keypoint[] {
  const { widths, torsoHeight, legHeight } = geometry
  const yBust = Y_SHOULDER + torsoHeight * 0.3
  const yWaist = Y_SHOULDER + torsoHeight * 0.65
  const yHip = Y_SHOULDER + torsoHeight
  const yKnee = yHip + legHeight * 0.5
  const yAnkle = yHip + legHeight

  const right: Keypoint[] = [
    { x: CENTER_X + widths.neck / 2, y: Y_NECK },
    { x: CENTER_X + widths.shoulder / 2, y: Y_SHOULDER },
    { x: CENTER_X + widths.bust / 2, y: yBust },
    { x: CENTER_X + widths.waist / 2, y: yWaist },
    { x: CENTER_X + widths.hip / 2, y: yHip },
    { x: CENTER_X + widths.ankle * 0.9, y: yKnee },
    { x: CENTER_X + widths.ankle / 2, y: yAnkle },
  ]
  const left: Keypoint[] = [...right].reverse().map((p) => ({ x: CENTER_X - (p.x - CENTER_X), y: p.y }))
  return [...right, ...left]
}

/**
 * Renders the outline as a smooth closed curve rather than a straight-edged
 * polygon, so the silhouette reads as a body rather than a faceted schematic.
 * Each segment is a Catmull-Rom spline (through the point and its neighbors)
 * converted to an equivalent cubic Bezier — a standard way to get a curve
 * that actually passes through every keypoint, not just approaches it.
 */
export function toSvgPath(points: Keypoint[]): string {
  if (points.length === 0) return ''
  const n = points.length
  const at = (i: number) => points[((i % n) + n) % n]

  const commands = points.map((_, i) => {
    const p0 = at(i - 1)
    const p1 = at(i)
    const p2 = at(i + 1)
    const p3 = at(i + 2)
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 }
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 }
    return `C ${c1.x.toFixed(2)} ${c1.y.toFixed(2)} ${c2.x.toFixed(2)} ${c2.y.toFixed(2)} ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`
  })

  const first = points[0]
  return `M ${first.x.toFixed(2)} ${first.y.toFixed(2)} ${commands.join(' ')} Z`
}

// Spike: how much each (positive/"helps") effect tag nudges specific
// silhouette widths, to sketch "what would the corrected line look like"
// on top of the body outline, reusing the same width→outline pipeline
// above rather than a real garment-geometry model. Hand-tuned for visual
// legibility only — not derived from anything, and only covers tags with
// an obvious width-based reading (waist/shoulder/bust/hip/ankle). Tags
// about torso/leg length (elongates_leg etc.) aren't represented yet —
// that needs a keypoint-position shift, not a width multiplier.
const EFFECT_WIDTH_ADJUSTMENTS: Record<string, Partial<Record<keyof AvatarGeometry['widths'], number>>> = {
  defines_waist: { waist: 0.8 },
  clings_to_waist: { waist: 0.92 },
  clings_to_hip: { hip: 0.95 },
  hides_waist: { waist: 1.18 },
  adds_volume_top: { shoulder: 1.15, bust: 1.15 },
  adds_bulk: { shoulder: 1.08, bust: 1.08, waist: 1.08 },
  reduces_bulk: { shoulder: 0.94, bust: 0.94, waist: 0.94 },
  adds_volume_bottom: { hip: 1.15, ankle: 1.15 },
}

/** Nudges silhouette widths per a scored outfit's effect tags — multiple
 * tags touching the same width compound multiplicatively. Unknown tags
 * are ignored (no-op), not an error. */
export function applyEffectAdjustments(geometry: AvatarGeometry, effectTags: string[]): AvatarGeometry {
  const widths = { ...geometry.widths }
  for (const tag of effectTags) {
    const adjustment = EFFECT_WIDTH_ADJUSTMENTS[tag]
    if (!adjustment) continue
    for (const [key, multiplier] of Object.entries(adjustment)) {
      widths[key as keyof typeof widths] *= multiplier
    }
  }
  return { ...geometry, widths }
}
