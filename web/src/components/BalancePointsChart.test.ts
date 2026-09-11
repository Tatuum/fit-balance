import { describe, expect, it } from 'vitest'
import { mainConcernBadgeText } from './BalancePointsChart'

describe('mainConcernBadgeText', () => {
  it('labels a favorable (balanced) waist_definition as a key asset, not a concern', () => {
    expect(mainConcernBadgeText('waist_definition', true)).toBe('key asset')
  })

  it('labels an unfavorable waist_definition as a main concern', () => {
    expect(mainConcernBadgeText('waist_definition', false)).toBe('main concern')
  })

  it('never uses the asset framing for other axes, regardless of balanced state', () => {
    expect(mainConcernBadgeText('torso_leg_balance', true)).toBe('main concern')
    expect(mainConcernBadgeText('frame_scale_dev', false)).toBe('main concern')
  })
})
