import { describe, expect, it } from 'vitest'
import { avatarOutline, computeAvatarGeometry, headEllipse, toSvgPath } from './avatarGeometry'
import type { Measurements } from './types'

const BASE: Measurements = {
  shoulder: 92.0,
  bust: 91.4,
  waist: 68.6,
  hip: 94.0,
  torso: 40.5,
  leg: 75.0,
  height: 165.1,
}

describe('computeAvatarGeometry', () => {
  it('is invariant under uniformly scaling every measurement (proportions, not absolute size, drive geometry)', () => {
    const base = computeAvatarGeometry(BASE)
    const scaledUp: Measurements = Object.fromEntries(
      Object.entries(BASE).map(([key, value]) => [key, value * 1.5]),
    ) as unknown as Measurements
    const scaled = computeAvatarGeometry(scaledUp)

    expect(scaled.widths.bust).toBeCloseTo(base.widths.bust)
    expect(scaled.torsoHeight).toBeCloseTo(base.torsoHeight)
    expect(scaled.legHeight).toBeCloseTo(base.legHeight)
  })

  it('gives a larger bust measurement a wider drawn bust, all else equal', () => {
    const smaller = computeAvatarGeometry(BASE)
    const larger = computeAvatarGeometry({ ...BASE, bust: BASE.bust + 20 })
    expect(larger.widths.bust).toBeGreaterThan(smaller.widths.bust)
  })

  it('gives a larger hip measurement a wider drawn hip, all else equal', () => {
    const smaller = computeAvatarGeometry(BASE)
    const larger = computeAvatarGeometry({ ...BASE, hip: BASE.hip + 20 })
    expect(larger.widths.hip).toBeGreaterThan(smaller.widths.hip)
  })

  it('draws a longer torso measurement as a taller torso', () => {
    const shorter = computeAvatarGeometry(BASE)
    const longer = computeAvatarGeometry({ ...BASE, torso: BASE.torso + 10 })
    expect(longer.torsoHeight).toBeGreaterThan(shorter.torsoHeight)
  })

  it('draws a longer leg measurement as a taller leg', () => {
    const shorter = computeAvatarGeometry(BASE)
    const longer = computeAvatarGeometry({ ...BASE, leg: BASE.leg + 10 })
    expect(longer.legHeight).toBeGreaterThan(shorter.legHeight)
  })

  it('derives neck from shoulder and ankle from hip (unmeasured, proportional only)', () => {
    const geometry = computeAvatarGeometry(BASE)
    expect(geometry.widths.neck).toBeLessThan(geometry.widths.shoulder)
    expect(geometry.widths.ankle).toBeLessThan(geometry.widths.hip)
  })

  it('produces only positive widths and lengths for realistic inputs', () => {
    const geometry = computeAvatarGeometry(BASE)
    for (const width of Object.values(geometry.widths)) {
      expect(width).toBeGreaterThan(0)
    }
    expect(geometry.torsoHeight).toBeGreaterThan(0)
    expect(geometry.legHeight).toBeGreaterThan(0)
  })
})

describe('headEllipse', () => {
  it('sits centered, directly above the neck keypoint', () => {
    const geometry = computeAvatarGeometry(BASE)
    const head = headEllipse(geometry)
    expect(head.cx).toBe(50)
    expect(head.rx).toBeGreaterThan(0)
    expect(head.ry).toBeGreaterThan(0)
    // Chin (bottom of the ellipse) should land at or above the neck keypoint's y.
    const [neckPoint] = avatarOutline(geometry)
    expect(head.cy + head.ry).toBeLessThanOrEqual(neckPoint.y)
  })

  it('is invariant under uniformly scaling every measurement', () => {
    const base = headEllipse(computeAvatarGeometry(BASE))
    const scaledUp: Measurements = Object.fromEntries(
      Object.entries(BASE).map(([key, value]) => [key, value * 1.5]),
    ) as unknown as Measurements
    const scaled = headEllipse(computeAvatarGeometry(scaledUp))

    expect(scaled.rx).toBeCloseTo(base.rx)
    expect(scaled.ry).toBeCloseTo(base.ry)
  })
})

describe('avatarOutline + toSvgPath', () => {
  it('produces a symmetric, closed outline', () => {
    const geometry = computeAvatarGeometry(BASE)
    const points = avatarOutline(geometry)
    expect(points.length).toBe(14)
    // First point (right neck) and last point (left neck) should mirror around x=50.
    const first = points[0]
    const last = points[points.length - 1]
    expect(first.y).toBe(last.y)
    expect(first.x - 50).toBeCloseTo(50 - last.x)
  })

  it('renders a valid closed SVG path string made of smooth curves', () => {
    const geometry = computeAvatarGeometry(BASE)
    const path = toSvgPath(avatarOutline(geometry))
    expect(path.startsWith('M ')).toBe(true)
    expect(path.endsWith('Z')).toBe(true)
    expect(path).toContain('C ')
    expect(path).not.toContain('L ')
  })

  it('returns an empty string for an empty outline', () => {
    expect(toSvgPath([])).toBe('')
  })
})
