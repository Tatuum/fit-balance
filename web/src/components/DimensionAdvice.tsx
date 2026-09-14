import type { DimensionAdvice as DimensionAdviceData } from '../lib/types'

/**
 * Renders each of the 4 scored dimensions independently, never combined
 * into one verdict -- see NOTES.md's "Technique recommendations" section
 * for why: summing/comparing across differently-scaled axes is exactly
 * the problem this feature avoids by never doing it. `pronounced` is a
 * per-dimension highlight, not a cross-dimension ranking -- any number of
 * dimensions (including zero) can carry it for a given body.
 */

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

            {seek.length === 0 && avoid.length === 0 ? (
              <p className="dimension-empty">No strong trait — most techniques here are neutral for you.</p>
            ) : (
              <>
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
              </>
            )}
          </div>
        )
      })}
    </div>
  )
}
