import { useEffect, useState } from 'react'
import { Avatar } from './components/Avatar'
import { DimensionAdvice } from './components/DimensionAdvice'
import { GarmentBalance } from './components/GarmentBalance'
import { MeasurementGuide } from './components/MeasurementGuide'
import { getTechniqueRecommendations } from './lib/api'
import type { Measurements, TechniqueRecommendationsResponse } from './lib/types'
import './App.css'

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

function App() {
  const [measurements, setMeasurements] = useState<Measurements>(DEFAULT_MEASUREMENTS)
  const [techniqueAdvice, setTechniqueAdvice] = useState<TechniqueRecommendationsResponse | null>(
    null,
  )
  const [techniqueAdviceError, setTechniqueAdviceError] = useState<string | null>(null)

  useEffect(() => {
    const handle = setTimeout(() => {
      getTechniqueRecommendations(measurements)
        .then((response) => {
          setTechniqueAdvice(response)
          setTechniqueAdviceError(null)
        })
        .catch((err) => {
          setTechniqueAdviceError(err instanceof Error ? err.message : String(err))
          setTechniqueAdvice(null)
        })
    }, 500)
    return () => clearTimeout(handle)
  }, [measurements])

  const updateMeasurement = (key: keyof Measurements) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value)
    setMeasurements((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="app">
      <h1>fit-balance</h1>
      <p className="subtitle">
        Enter measurements (cm) to see a to-scale silhouette and which garment techniques work
        with or against your proportions — no photorealism, just proportions.
      </p>

      <div className="layout">
        <div className="form">
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
        </div>

        <div className="results">
          <Avatar measurements={measurements} />

          <section className="technique-advice-section">
            <h2>What to look for</h2>
            {techniqueAdviceError && (
              <p className="error">Couldn't load technique advice: {techniqueAdviceError}</p>
            )}
            {techniqueAdvice && <DimensionAdvice dimensions={techniqueAdvice.dimensions} />}
          </section>

          <GarmentBalance measurements={measurements} />
        </div>
      </div>
    </div>
  )
}

export default App
