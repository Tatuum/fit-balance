import type { Measurements } from './types'

/**
 * Allowed range per measurement, in cm, inclusive. Mirrors the
 * `Field(ge=..., le=...)` bounds on `Measurements` in
 * src/fit_balance/schemas.py — keep the two in sync; the API is the
 * authority and answers 422 outside these. Wide sanity limits, not survey
 * data: they reject typos and impossible values, not unusual bodies.
 */
export const MEASUREMENT_RANGES: Record<keyof Measurements, { min: number; max: number }> = {
  shoulder: { min: 60, max: 160 },
  bust: { min: 60, max: 180 },
  waist: { min: 40, max: 180 },
  hip: { min: 60, max: 200 },
  torso: { min: 25, max: 60 },
  leg: { min: 50, max: 110 },
  height: { min: 120, max: 230 },
}

/**
 * The number typed into a measurement field, or null if it is empty, not a
 * number, or outside the field's range. Pure so it is unit-testable apart
 * from the form.
 */
export function parseMeasurement(key: keyof Measurements, text: string): number | null {
  if (text.trim() === '') return null
  const value = Number(text)
  const { min, max } = MEASUREMENT_RANGES[key]
  return Number.isFinite(value) && value >= min && value <= max ? value : null
}

export function rangeMessage(key: keyof Measurements): string {
  const { min, max } = MEASUREMENT_RANGES[key]
  return `Enter ${min}–${max} cm`
}

/**
 * The form's two views of the measurements. `drafts` is the text exactly as
 * typed in each field, so a field can sit empty or out of range. `measurements`
 * is always the last *valid* set — what the avatar, the advice request and
 * GarmentBalance use — so a bad value never reaches them.
 */
export interface FormState {
  drafts: Record<keyof Measurements, string>
  measurements: Measurements
}

export function initialFormState(defaults: Measurements): FormState {
  const keys = Object.keys(defaults) as (keyof Measurements)[]
  return {
    drafts: Object.fromEntries(keys.map((key) => [key, String(defaults[key])])) as FormState['drafts'],
    measurements: defaults,
  }
}

/**
 * Applies one field edit. The draft always takes the typed text; the
 * measurement only changes if the text parses to a valid number. When it
 * doesn't, `measurements` is returned as the same object, so effects that
 * depend on it do not re-run and no request is sent.
 */
export function applyInput(state: FormState, key: keyof Measurements, text: string): FormState {
  const drafts = { ...state.drafts, [key]: text }
  const value = parseMeasurement(key, text)
  if (value === null) return { drafts, measurements: state.measurements }
  return { drafts, measurements: { ...state.measurements, [key]: value } }
}
