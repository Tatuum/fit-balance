import { useEffect, useState } from 'react'
import { Avatar } from './components/Avatar'
import { BalancePointsChart } from './components/BalancePointsChart'
import { MeasurementGuide } from './components/MeasurementGuide'
import { getGarments, recommendOutfits, scoreOutfit } from './lib/api'
import { groupBySlot, SLOTS } from './lib/garments'
import type {
  GarmentSummary,
  Measurements,
  RecommendOutfitsResponse,
  ScoreOutfitResponse,
  Slot,
} from './lib/types'
import './App.css'

const SLOT_LABELS: Record<Slot, string> = {
  dress: 'Dress',
  top: 'Top',
  bottom: 'Bottom',
  outerwear: 'Outerwear',
}

// Measurement method for each field. torso/leg follow the convention
// documented in NOTES.md's "known gaps" (ISO 8559 / tailoring practice):
// back waist length and inseam, anchored at different landmarks — they are
// not meant to sum to height.
const MEASUREMENT_HELP: Record<keyof Measurements, string> = {
  shoulder:
    'Shoulder circumference: wrap the tape around the fullest part of the shoulders/upper ' +
    'arms — not the tailoring point-to-point shoulder width.',
  bust: 'Fullest point of the bust, measured straight around.',
  waist: 'Natural waistline (narrowest point of the torso), measured straight around.',
  hip: 'Fullest point of the hips, measured straight around.',
  torso: 'Back waist length: nape of neck (C7 vertebra) straight down to the natural waist.',
  leg: 'Inseam: crotch straight down to the floor.',
  height: 'Standing height, measured barefoot.',
}

const DEFAULT_MEASUREMENTS: Measurements = {
  shoulder: 92.0,
  bust: 91.4,
  waist: 68.6,
  hip: 94.0,
  torso: 40.5,
  leg: 75.0,
  height: 165.1,
}

const DEFAULT_SELECTION: Record<Slot, string | null> = {
  dress: 'belted_sheath_dress',
  top: null,
  bottom: null,
  outerwear: null,
}

const RECOMMENDATION_LABEL: Record<string, string> = {
  recommended: 'Recommended',
  neutral: 'Neutral',
  avoid: 'Avoid',
  strong_avoid: 'Strong avoid',
}

function App() {
  const [measurements, setMeasurements] = useState<Measurements>(DEFAULT_MEASUREMENTS)
  const [garments, setGarments] = useState<GarmentSummary[]>([])
  const [garmentsError, setGarmentsError] = useState<string | null>(null)
  const [selectedItemIds, setSelectedItemIds] = useState<Record<Slot, string | null>>(
    DEFAULT_SELECTION,
  )
  const [result, setResult] = useState<ScoreOutfitResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState<RecommendOutfitsResponse | null>(null)
  const [recommendError, setRecommendError] = useState<string | null>(null)
  const [recommendLoading, setRecommendLoading] = useState(false)

  useEffect(() => {
    getGarments()
      .then(setGarments)
      .catch((err) => setGarmentsError(err instanceof Error ? err.message : String(err)))
  }, [])

  useEffect(() => {
    const handle = setTimeout(() => {
      setRecommendLoading(true)
      recommendOutfits(measurements, 5)
        .then((response) => {
          setRecommendations(response)
          setRecommendError(null)
        })
        .catch((err) => {
          setRecommendError(err instanceof Error ? err.message : String(err))
          setRecommendations(null)
        })
        .finally(() => setRecommendLoading(false))
    }, 500)
    return () => clearTimeout(handle)
  }, [measurements])

  const updateMeasurement = (key: keyof Measurements) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value)
    setMeasurements((prev) => ({ ...prev, [key]: value }))
  }

  const selectItem = (slot: Slot, itemId: string | null) => {
    setSelectedItemIds((prev) => ({ ...prev, [slot]: itemId }))
  }

  const itemIds = Object.values(selectedItemIds).filter((id): id is string => id !== null)
  const labelById = Object.fromEntries(garments.map((g) => [g.id, g.label]))
  const groupedGarments = groupBySlot(garments)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await scoreOutfit(measurements, itemIds)
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
        Enter measurements (cm) and build an outfit (one item per slot) to see the verdict, the
        reasons behind it, and a parametric silhouette — no photorealism, just proportions.
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
            <legend>Recommended for you</legend>
            {recommendLoading && <p>Scoring your best-fitting outfits…</p>}
            {recommendError && <p className="error">Couldn't load recommendations: {recommendError}</p>}
            {recommendations && (
              <ol className="recommendations">
                {recommendations.recommendations.map((rec) => (
                  <li key={rec.item_ids.join('+')} className="recommendation">
                    <span className="recommendation-labels">{rec.labels.join(' + ')}</span>
                    <span className={`verdict verdict-${rec.verdict.recommendation}`}>
                      {RECOMMENDATION_LABEL[rec.verdict.recommendation]} ({rec.verdict.score.toFixed(3)})
                    </span>
                  </li>
                ))}
                {recommendations.recommendations.length === 0 && <li>No candidate outfits found.</li>}
              </ol>
            )}
          </fieldset>

          {garmentsError && <p className="error">Couldn't load garment catalog: {garmentsError}</p>}

          {SLOTS.map((slot) => (
            <fieldset key={slot}>
              <legend>{SLOT_LABELS[slot]}</legend>
              <label className="checkbox">
                <input
                  type="radio"
                  name={`slot-${slot}`}
                  checked={selectedItemIds[slot] === null}
                  onChange={() => selectItem(slot, null)}
                />
                None
              </label>
              {groupedGarments[slot].map((item) => (
                <label key={item.id} className="checkbox">
                  <input
                    type="radio"
                    name={`slot-${slot}`}
                    checked={selectedItemIds[slot] === item.id}
                    onChange={() => selectItem(slot, item.id)}
                  />
                  {item.label}
                </label>
              ))}
            </fieldset>
          ))}

          <button type="submit" disabled={loading || itemIds.length === 0}>
            {loading ? 'Scoring…' : 'Score outfit'}
          </button>
        </form>

        <div className="results">
          {error && <p className="error">{error}</p>}

          {result && (
            <>
              <Avatar
                measurements={measurements}
                effectTags={result.verdict.reasons
                  .filter((reason) => reason.direction === '+')
                  .map((reason) => reason.tag)}
              />
              <p className={`verdict verdict-${result.verdict.recommendation}`}>
                {RECOMMENDATION_LABEL[result.verdict.recommendation]} (score:{' '}
                {result.verdict.score.toFixed(3)})
              </p>
              <BalancePointsChart
                balancePoints={result.balance_points}
                mainConcern={result.main_concern}
              />
              <ul className="reasons">
                {result.verdict.reasons.map((reason, index) => (
                  <li
                    key={`${reason.tag}-${index}`}
                    className={reason.direction === '+' ? 'helps' : 'hurts'}
                  >
                    {reason.direction} {reason.tag} ({reason.axis}, {reason.contribution.toFixed(3)})
                    {reason.item_ids.length > 0 && (
                      <span className="reason-source">
                        {' '}
                        — from: {reason.item_ids.map((id) => labelById[id] ?? id).join(', ')}
                      </span>
                    )}
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
