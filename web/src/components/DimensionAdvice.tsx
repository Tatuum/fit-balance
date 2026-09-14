import type { DimensionAdvice as DimensionAdviceData } from '../lib/types'

/**
 * Renders each of the 4 scored dimensions independently, never combined
 * into one verdict -- see NOTES.md's "Technique recommendations" section
 * for why: summing/comparing across differently-scaled axes is exactly
 * the problem this feature avoids by never doing it. `pronounced` is a
 * per-dimension highlight, not a cross-dimension ranking -- any number of
 * dimensions (including zero) can carry it for a given body.
 *
 * The plain-language description per axis is presentation-only wording
 * layered on top of the backend's `notable`/`direction`/`pronounced`
 * facts (mirrors how BalancePointsChart.tsx's AXIS_META does the same
 * kind of "value -> words" translation for its own panel) -- deliberately
 * driven by `notable`/`direction`, not by whether `recommendations`
 * happens to be non-empty, since those can diverge when a tag has no
 * current catalog item behind it (adds_volume_top, see technique_advice.py).
 */

const DESCRIBE: Record<string, (pronounced: boolean, direction: '+' | '-') => string> = {
  waist_definition: (pronounced, direction) =>
    direction === '+'
      ? pronounced
        ? 'strongly defined'
        : 'noticeably defined'
      : pronounced
        ? 'strongly undefined'
        : 'not clearly defined',
  top_hip_balance: (pronounced, direction) =>
    direction === '+'
      ? pronounced
        ? 'shoulders/bust notably wider than hip'
        : 'shoulders/bust a little wider than hip'
      : pronounced
        ? 'hip notably wider than shoulders/bust'
        : 'hip a little wider than shoulders/bust',
  torso_leg_balance: (pronounced, direction) =>
    direction === '+'
      ? pronounced
        ? 'noticeably long torso relative to legs'
        : 'torso a little longer than legs, relatively'
      : pronounced
        ? 'noticeably long legs relative to torso'
        : 'legs a little longer than torso, relatively',
  frame_scale_dev: (pronounced, direction) =>
    direction === '+'
      ? pronounced
        ? 'reads notably fuller for your height'
        : 'reads a little fuller for your height'
      : pronounced
        ? 'reads notably slighter for your height'
        : 'reads a little slighter for your height',
}

function describe(dimension: DimensionAdviceData): string {
  if (!dimension.notable || !dimension.direction) {
    return 'no strong trait — most techniques here are neutral for you'
  }
  return DESCRIBE[dimension.axis]?.(dimension.pronounced, dimension.direction) ?? ''
}

interface DimensionAdviceProps {
  dimensions: DimensionAdviceData[]
}

export function DimensionAdvice({ dimensions }: DimensionAdviceProps) {
  return (
    <div className="dimension-advice">
      {dimensions.map((dimension) => {
        const seek = dimension.recommendations.filter((r) => r.direction === '+')
        const avoid = dimension.recommendations.filter((r) => r.direction === '-')

        return (
          <div key={dimension.axis} className="dimension-card">
            <div className="dimension-header">
              <span className="dimension-label">{dimension.label}</span>
              {dimension.pronounced && <span className="dimension-badge">stands out</span>}
            </div>

            <p className="dimension-description">{describe(dimension)}</p>

            {seek.length > 0 && (
              <p className="dimension-seek">
                <span aria-hidden="true">✓</span> seek:{' '}
                {seek.map((r) => r.items.map((item) => item.label).join(', ')).join(', ')}
              </p>
            )}
            {avoid.length > 0 && (
              <p className="dimension-avoid">
                <span aria-hidden="true">✗</span> avoid:{' '}
                {avoid.map((r) => r.items.map((item) => item.label).join(', ')).join(', ')}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
