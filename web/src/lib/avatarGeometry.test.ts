import { describe, expect, it } from 'vitest'
import { avatarOutline, computeAvatarGeometry, toSvgPath } from './avatarGeometry'
import type { BalancePoints } from './types'

const NEUTRAL: BalancePoints = {
  shoulder_hip_balance: 0,
  bust_hip_balance: 0,
  waist_definition: 0,
  torso_leg_balance: 0,
  frame_scale_dev: 0,
}

describe('computeAvatarGeometry', () => {
  it('returns the base silhouette when all balance points are neutral', () => {
    const geometry = computeAvatarGeometry(NEUTRAL)
    expect(geometry.widths.bust).toBe(geometry.widths.hip)
    expect(geometry.torsoHeight).toBeCloseTo(55)
    expect(geometry.legHeight).toBeCloseTo(85)
  })

  it('widens the bust relative to the hip when bust_hip_balance is positive', () => {
    const geometry = computeAvatarGeometry({ ...NEUTRAL, bust_hip_balance: 0.15 })
    expect(geometry.widths.bust).toBeGreaterThan(geometry.widths.hip)
  })

  it('widens the hip relative to the bust when bust_hip_balance is negative (pear)', () => {
    const geometry = computeAvatarGeometry({ ...NEUTRAL, bust_hip_balance: -0.15 })
    expect(geometry.widths.hip).toBeGreaterThan(geometry.widths.bust)
  })

  it('widens the shoulder when shoulder_hip_balance is positive (broad-shoulder build)', () => {
    const geometry = computeAvatarGeometry({ ...NEUTRAL, shoulder_hip_balance: 0.15 })
    const base = computeAvatarGeometry(NEUTRAL)
    expect(geometry.widths.shoulder).toBeGreaterThan(base.widths.shoulder)
  })

  it('narrows the shoulder when shoulder_hip_balance is negative (pear)', () => {
    const geometry = computeAvatarGeometry({ ...NEUTRAL, shoulder_hip_balance: -0.15 })
    const base = computeAvatarGeometry(NEUTRAL)
    expect(geometry.widths.shoulder).toBeLessThan(base.widths.shoulder)
  })

  it('narrows the waist as waist_definition increases', () => {
    const defined = computeAvatarGeometry({ ...NEUTRAL, waist_definition: 0.26 })
    const undefined_ = computeAvatarGeometry({ ...NEUTRAL, waist_definition: 0.06 })
    expect(defined.widths.waist).toBeLessThan(undefined_.widths.waist)
  })

  it('grows the torso relative to the legs as torso_leg_balance increases', () => {
    const geometry = computeAvatarGeometry({ ...NEUTRAL, torso_leg_balance: 0.2 })
    expect(geometry.torsoHeight).toBeGreaterThan(55)
    expect(geometry.legHeight).toBeLessThan(85)
  })

  it('scales every width up as frame_scale_dev increases', () => {
    const fuller = computeAvatarGeometry({ ...NEUTRAL, frame_scale_dev: 0.1 })
    const base = computeAvatarGeometry(NEUTRAL)
    expect(fuller.widths.shoulder).toBeGreaterThan(base.widths.shoulder)
    expect(fuller.widths.hip).toBeGreaterThan(base.widths.hip)
  })

  it('clamps extreme balance-point values to a sane, positive range', () => {
    const geometry = computeAvatarGeometry({
      shoulder_hip_balance: 50,
      bust_hip_balance: 50,
      waist_definition: 50,
      torso_leg_balance: 50,
      frame_scale_dev: 50,
    })
    for (const width of Object.values(geometry.widths)) {
      expect(width).toBeGreaterThan(0)
    }
    expect(geometry.torsoHeight).toBeGreaterThan(0)
    expect(geometry.legHeight).toBeGreaterThan(0)
  })
})

describe('avatarOutline + toSvgPath', () => {
  it('produces a symmetric, closed outline', () => {
    const geometry = computeAvatarGeometry(NEUTRAL)
    const points = avatarOutline(geometry)
    expect(points.length).toBe(14)
    // First point (right neck) and last point (left neck) should mirror around x=50.
    const first = points[0]
    const last = points[points.length - 1]
    expect(first.y).toBe(last.y)
    expect(first.x - 50).toBeCloseTo(50 - last.x)
  })

  it('renders a valid closed SVG path string', () => {
    const geometry = computeAvatarGeometry(NEUTRAL)
    const path = toSvgPath(avatarOutline(geometry))
    expect(path.startsWith('M ')).toBe(true)
    expect(path.endsWith('Z')).toBe(true)
    expect(path).toContain('L ')
  })

  it('returns an empty string for an empty outline', () => {
    expect(toSvgPath([])).toBe('')
  })
})
