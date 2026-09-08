import type { BalancePoints } from './types'

/**
 * Turns balance-point values into a generic, proportion-accurate silhouette
 * — no photorealism, per NOTES.md. Every function here is pure (no DOM, no
 * React) so the mapping from balance points to shape is unit-testable on
 * its own, independent of how it's eventually rendered.
 */

const BASE_WIDTHS = {
  neck: 10,
  shoulder: 20,
  bust: 18,
  waist: 15,
  hip: 18,
  ankle: 6,
}

const BASE_TORSO_HEIGHT = 55
const BASE_LEG_HEIGHT = 85

// How strongly each balance point perturbs the base silhouette. Tuned for a
// visually legible v0, not calibrated against real anthropometric data.
const SENSITIVITY = {
  bustHipBalance: 1.5,
  waistDefinition: 1.0,
  torsoLegBalance: 0.6,
  frameScaleDev: 1.5,
}

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))

export interface AvatarGeometry {
  widths: typeof BASE_WIDTHS
  torsoHeight: number
  legHeight: number
}

export function computeAvatarGeometry(bp: BalancePoints): AvatarGeometry {
  const scale = clamp(1 + SENSITIVITY.frameScaleDev * bp.frame_scale_dev, 0.6, 1.6)
  const bustFactor = clamp(1 + SENSITIVITY.bustHipBalance * bp.bust_hip_balance, 0.5, 1.6)
  const hipFactor = clamp(1 - SENSITIVITY.bustHipBalance * bp.bust_hip_balance, 0.5, 1.6)
  const waistFactor = clamp(1 - SENSITIVITY.waistDefinition * bp.waist_definition, 0.5, 1.2)
  const torsoLegFactor = clamp(SENSITIVITY.torsoLegBalance * bp.torso_leg_balance, -0.5, 0.5)

  return {
    widths: {
      neck: BASE_WIDTHS.neck * scale,
      shoulder: BASE_WIDTHS.shoulder * scale,
      bust: BASE_WIDTHS.bust * bustFactor * scale,
      waist: BASE_WIDTHS.waist * waistFactor * scale,
      hip: BASE_WIDTHS.hip * hipFactor * scale,
      ankle: BASE_WIDTHS.ankle * scale,
    },
    torsoHeight: BASE_TORSO_HEIGHT * (1 + torsoLegFactor),
    legHeight: BASE_LEG_HEIGHT * (1 - torsoLegFactor),
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
