import { describe, expect, it } from 'vitest'
import {
  applyInput,
  initialFormState,
  MEASUREMENT_RANGES,
  parseMeasurement,
  rangeMessage,
} from './measurements'
import type { Measurements } from './types'

const KEYS = Object.keys(MEASUREMENT_RANGES) as (keyof Measurements)[]

describe('parseMeasurement', () => {
  it('returns the number for an in-range value, including decimals', () => {
    expect(parseMeasurement('waist', '68.6')).toBe(68.6)
    expect(parseMeasurement('height', '165')).toBe(165)
  })

  it.each(KEYS)('accepts both bounds of %s (inclusive)', (key) => {
    const { min, max } = MEASUREMENT_RANGES[key]
    expect(parseMeasurement(key, String(min))).toBe(min)
    expect(parseMeasurement(key, String(max))).toBe(max)
  })

  it.each(KEYS)('rejects just outside either bound of %s', (key) => {
    const { min, max } = MEASUREMENT_RANGES[key]
    expect(parseMeasurement(key, String(min - 0.1))).toBeNull()
    expect(parseMeasurement(key, String(max + 0.1))).toBeNull()
  })

  it('rejects the values that used to get through', () => {
    expect(parseMeasurement('waist', '1')).toBeNull()
    expect(parseMeasurement('shoulder', '0')).toBeNull()
    expect(parseMeasurement('height', '0')).toBeNull()
    expect(parseMeasurement('height', '-5')).toBeNull()
  })

  it('rejects an empty or blank field instead of reading it as 0', () => {
    expect(parseMeasurement('height', '')).toBeNull()
    expect(parseMeasurement('height', '   ')).toBeNull()
  })

  it('rejects text that is not a number', () => {
    expect(parseMeasurement('hip', 'abc')).toBeNull()
    expect(parseMeasurement('hip', 'Infinity')).toBeNull()
  })
})

describe('applyInput', () => {
  const start = initialFormState({
    shoulder: 92,
    bust: 91.4,
    waist: 68.6,
    hip: 94,
    torso: 40.5,
    leg: 75,
    height: 165.1,
  })

  it('starts with every draft equal to its default and nothing invalid', () => {
    expect(start.drafts.height).toBe('165.1')
    for (const key of KEYS) {
      expect(parseMeasurement(key, start.drafts[key])).not.toBeNull()
    }
  })

  it('updates the draft and the measurement for a valid value', () => {
    const next = applyInput(start, 'waist', '70')
    expect(next.drafts.waist).toBe('70')
    expect(next.measurements.waist).toBe(70)
    expect(next.measurements.hip).toBe(start.measurements.hip)
  })

  it('keeps the typed text but not the value when a field is cleared', () => {
    const next = applyInput(start, 'height', '')
    expect(next.drafts.height).toBe('')
    expect(next.measurements.height).toBe(165.1)
  })

  it('returns the same measurements object when the input is invalid', () => {
    // Effects depend on this object's identity: same object, no new request.
    expect(applyInput(start, 'waist', '1').measurements).toBe(start.measurements)
    expect(applyInput(start, 'height', '').measurements).toBe(start.measurements)
  })

  it('recovers: a valid value after an invalid one updates the measurement', () => {
    const cleared = applyInput(start, 'height', '')
    const retyped = applyInput(cleared, 'height', '170')
    expect(retyped.drafts.height).toBe('170')
    expect(retyped.measurements.height).toBe(170)
  })

  it('does not mutate the previous state', () => {
    const before = JSON.stringify(start)
    applyInput(start, 'waist', '70')
    expect(JSON.stringify(start)).toBe(before)
  })
})

describe('rangeMessage', () => {
  it('names the field range', () => {
    expect(rangeMessage('height')).toBe('Enter 120–230 cm')
  })
})
