import { useEffect, useState } from 'react'
import { balanceGarment, getGarments } from '../lib/api'
import { groupBySlot, SLOTS } from '../lib/garments'
import type { BalanceGarmentResponse, GarmentSummary, Measurements, Slot } from '../lib/types'
import { Avatar } from './Avatar'
import { DimensionAdvice } from './DimensionAdvice'

const SLOT_LABELS: Record<Slot, string> = {
  dress: 'Dress',
  top: 'Top',
  bottom: 'Bottom',
  outerwear: 'Outerwear',
}

const RECOMMENDATION_LABEL: Record<string, string> = {
  recommended: 'Recommended',
  neutral: 'Neutral',
  avoid: 'Avoid',
  strong_avoid: 'Strong avoid',
}

// The 4 dimensions technique_advice.py's DIMENSIONS labels, plus
// shoulder_hip_balance -- narrows_shoulder (decision 0013) can produce a
// Reason on that axis directly, and nothing else labels it anywhere today.
const AXIS_LABELS: Record<string, string> = {
  waist_definition: 'Waist definition',
  top_hip_balance: 'Horizontal balance',
  torso_leg_balance: 'Vertical proportion',
  frame_scale_dev: 'Frame scale',
  shoulder_hip_balance: 'Shoulder-hip balance',
}

interface GarmentBalanceProps {
  measurements: Measurements
}

export function GarmentBalance({ measurements }: GarmentBalanceProps) {
  const [garments, setGarments] = useState<GarmentSummary[]>([])
  const [garmentsError, setGarmentsError] = useState<string | null>(null)
  const [selectedItemId, setSelectedItemId] = useState<string>('')
  const [advice, setAdvice] = useState<BalanceGarmentResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getGarments()
      .then(setGarments)
      .catch((err) => setGarmentsError(err instanceof Error ? err.message : String(err)))
  }, [])

  useEffect(() => {
    if (!selectedItemId) {
      setAdvice(null)
      setError(null)
      return
    }
    const handle = setTimeout(() => {
      balanceGarment(measurements, selectedItemId)
        .then((response) => {
          setAdvice(response)
          setError(null)
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : String(err))
          setAdvice(null)
        })
    }, 500)
    return () => clearTimeout(handle)
  }, [measurements, selectedItemId])

  const groupedGarments = groupBySlot(garments)

  return (
    <section className="garment-balance-section">
      <h2>Try on a garment</h2>
      {garmentsError && <p className="error">Couldn't load garment catalog: {garmentsError}</p>}
      <select value={selectedItemId} onChange={(e) => setSelectedItemId(e.target.value)}>
        <option value="">Choose a garment…</option>
        {SLOTS.map((slot) => (
          <optgroup key={slot} label={SLOT_LABELS[slot]}>
            {groupedGarments[slot].map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>

      {error && <p className="error">Couldn't load balance advice: {error}</p>}

      {advice && (
        <div className="garment-balance-result">
          <Avatar measurements={measurements} effectTags={advice.verdict.reasons.map((r) => r.tag)} />
          <p className={`verdict verdict-${advice.verdict.recommendation}`}>
            {RECOMMENDATION_LABEL[advice.verdict.recommendation]} (score:{' '}
            {advice.verdict.score.toFixed(3)})
          </p>
          <ul className="reasons">
            {advice.verdict.reasons.map((reason) => (
              <li key={reason.tag} className={reason.direction === '+' ? 'helps' : 'hurts'}>
                {reason.tag.replace(/_/g, ' ')} — {AXIS_LABELS[reason.axis] ?? reason.axis}
              </li>
            ))}
            {advice.verdict.reasons.length === 0 && <li>No scored effects fired.</li>}
          </ul>

          {advice.suggestions.length > 0 && (
            <div className="garment-balance-suggestions">
              <h3>How to balance it</h3>
              <DimensionAdvice dimensions={advice.suggestions} />
            </div>
          )}
        </div>
      )}
    </section>
  )
}
