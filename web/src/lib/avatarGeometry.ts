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

// Front-view width from a circumference, via the classic anthropometric
// ellipse approximation: a body cross-section is wider than it is deep, so
// circumference isn't width * pi. A commonly cited approximation is a
// ~10:7 circumference-to-width ratio (width ≈ circumference * 7/10) —
// real depth varies by build, so this is an approximation, not exact.
const WIDTH_FROM_CIRCUMFERENCE = 0.7

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

export interface AvatarGeometry {
  widths: {
    neck: number
    shoulder: number
    bust: number
    waist: number
    hip: number
    ankle: number
  }
  torsoHeight: number
  legHeight: number
}

export function computeAvatarGeometry(m: Measurements): AvatarGeometry {
  const scale = TARGET_FIGURE_HEIGHT / m.height
  const widthOf = (circumference: number) => circumference * WIDTH_FROM_CIRCUMFERENCE * scale

  const shoulder = widthOf(m.shoulder)
  const hip = widthOf(m.hip)

  return {
    widths: {
      neck: shoulder * NECK_TO_SHOULDER_RATIO,
      shoulder,
      bust: widthOf(m.bust),
      waist: widthOf(m.waist),
      hip,
      ankle: hip * ANKLE_TO_HIP_RATIO,
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

export function toSvgPath(points: Keypoint[]): string {
  if (points.length === 0) return ''
  const [first, ...rest] = points
  const commands = rest.map((p) => `L ${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
  return `M ${first.x.toFixed(2)} ${first.y.toFixed(2)} ${commands.join(' ')} Z`
}
