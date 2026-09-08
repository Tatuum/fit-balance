import { useState } from 'react'
import { Avatar } from './components/Avatar'
import { MeasurementGuide } from './components/MeasurementGuide'
import { scoreGarment } from './lib/api'
import type { Measurements, ScoreResponse } from './lib/types'
import './App.css'

// Keep in sync with src/fit_balance/effects.yaml — there's no endpoint to
// list known techniques yet, so this v0 duplicates the technique names by
// hand.
const KNOWN_TECHNIQUES = [
  'sheath_bodycon',
  'belted_natural_waist',
  'drop_waist',
  'empire_waistline',
  'vertical_detail',
  'oversized_top',
  'skinny_straight',
]

// Measurement method for each field. torso/leg follow the convention
// documented in NOTES.md's "known gaps" (ISO 8559 / tailoring practice):
// back waist length and inseam, anchored at different landmarks — they are
// not meant to sum to height.
const MEASUREMENT_HELP: Record<keyof Measurements, string> = {
  bust: 'Fullest point of the bust, measured straight around.',
  waist: 'Natural waistline (narrowest point of the torso), measured straight around.',
  hip: 'Fullest point of the hips, measured straight around.',
  torso: 'Back waist length: nape of neck (C7 vertebra) straight down to the natural waist.',
  leg: 'Inseam: crotch straight down to the floor.',
  height: 'Standing height, measured barefoot.',
}

const DEFAULT_MEASUREMENTS: Measurements = {
  bust: 91.4,
  waist: 68.6,
  hip: 94.0,
  torso: 68.6,
  leg: 68.6,
  height: 165.1,
}

const RECOMMENDATION_LABEL: Record<string, string> = {
  recommended: 'Recommended',
  neutral: 'Neutral',
  avoid: 'Avoid',
  strong_avoid: 'Strong avoid',
}

function App() {
  const [measurements, setMeasurements] = useState<Measurements>(DEFAULT_MEASUREMENTS)
  const [techniques, setTechniques] = useState<Set<string>>(
    new Set(['sheath_bodycon', 'belted_natural_waist']),
  )
  const [result, setResult] = useState<ScoreResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const updateMeasurement = (key: keyof Measurements) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value)
    setMeasurements((prev) => ({ ...prev, [key]: value }))
  }

  const toggleTechnique = (technique: string) => {
    setTechniques((prev) => {
      const next = new Set(prev)
      if (next.has(technique)) {
        next.delete(technique)
      } else {
        next.add(technique)
      }
      return next
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await scoreGarment(measurements, { techniques: [...techniques] })
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>fit-balance</h1>
      <p className="subtitle">
        Enter measurements (cm) and garment techniques to see the verdict, the reasons behind it,
        and a parametric silhouette — no photorealism, just proportions.
      </p>

      <div className="layout">
        <form onSubmit={handleSubmit} className="form">
          <fieldset>
            <legend>Measurements (cm)</legend>
            <MeasurementGuide />
            {(Object.keys(DEFAULT_MEASUREMENTS) as (keyof Measurements)[]).map((key) => (
              <label key={key}>
                <span className="help-icon" title={MEASUREMENT_HELP[key]}>
                  {key} <span aria-hidden="true">ⓘ</span>
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={measurements[key]}
                  onChange={updateMeasurement(key)}
                />
              </label>
            ))}
          </fieldset>

          <fieldset>
            <legend>Garment techniques</legend>
            {KNOWN_TECHNIQUES.map((technique) => (
              <label key={technique} className="checkbox">
                <input
                  type="checkbox"
                  checked={techniques.has(technique)}
                  onChange={() => toggleTechnique(technique)}
                />
                {technique}
              </label>
            ))}
          </fieldset>

          <button type="submit" disabled={loading || techniques.size === 0}>
            {loading ? 'Scoring…' : 'Score'}
          </button>
        </form>

        <div className="results">
          {error && <p className="error">{error}</p>}

          {result && (
            <>
              <Avatar balancePoints={result.balance_points} />
              <p className={`verdict verdict-${result.verdict.recommendation}`}>
                {RECOMMENDATION_LABEL[result.verdict.recommendation]} (score:{' '}
                {result.verdict.score.toFixed(3)})
              </p>
              <p className="main-concern">Main concern: {result.main_concern}</p>
              <ul className="reasons">
                {result.verdict.reasons.map((reason) => (
                  <li key={reason.tag} className={reason.direction === '+' ? 'helps' : 'hurts'}>
                    {reason.direction} {reason.tag} ({reason.axis}, {reason.contribution.toFixed(3)})
                  </li>
                ))}
                {result.verdict.reasons.length === 0 && <li>No scored effects fired.</li>}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
