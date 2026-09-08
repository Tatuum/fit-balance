import type { BalancePoints } from '../lib/types'

/**
 * Diverging-bar view of every balance point: how far this body reads from
 * neutral (0) on each axis, and which direction. Geometry (which side of
 * center a bar extends) carries the polarity; color reinforces it — it
 * never stands in for the sign alone, every value also has a signed text
 * label. No shape label, no good/bad judgment baked into color: most axes
 * are purely descriptive (which side is bigger), not a problem to fix — see
 * NOTES.md. The one axis with a favorable direction (waist_definition) is
 * still drawn the same way; its caption says so in words, not in color.
 */

type Axis = keyof BalancePoints

const AXIS_ORDER: Axis[] = [
  'shoulder_hip_balance',
  'bust_hip_balance',
  'waist_definition',
  'torso_leg_balance',
  'frame_scale_dev',
]

const AXIS_META: Record<Axis, { label: string; positive: string; negative: string }> = {
  shoulder_hip_balance: {
    label: 'Shoulder vs hip',
    positive: '+ shoulder wider than hip',
    negative: '− hip wider than shoulder',
  },
  bust_hip_balance: {
    label: 'Bust vs hip',
    positive: '+ bust wider than hip',
    negative: '− hip wider than bust',
  },
  waist_definition: {
    label: 'Waist definition',
    positive: '+ defined waist (an asset)',
    negative: '− little to no natural cinch',
  },
  torso_leg_balance: {
    label: 'Torso vs leg',
    positive: '+ long torso',
    negative: '− long legs',
  },
  frame_scale_dev: {
    label: 'Frame scale',
    positive: '+ reads fuller for height',
    negative: '− reads slighter for height',
  },
}

// Typical human range for these ratios (seen across the worked examples:
// roughly ±0.15-0.26) plus headroom — a fixed domain so bars are
// comparable at a glance instead of rescaling every render.
const DOMAIN = 0.4

const formatValue = (value: number) => (value >= 0 ? `+${value.toFixed(3)}` : value.toFixed(3))

interface BalancePointsChartProps {
  balancePoints: BalancePoints
  mainConcern: string
}

export function BalancePointsChart({ balancePoints, mainConcern }: BalancePointsChartProps) {
  const domain = Math.max(DOMAIN, ...AXIS_ORDER.map((axis) => Math.abs(balancePoints[axis])))

  return (
    <div className="balance-chart">
      <div className="balance-legend">
        <span className="balance-legend-item">
          <span className="balance-swatch balance-swatch-positive" /> above neutral
        </span>
        <span className="balance-legend-item">
          <span className="balance-swatch balance-swatch-negative" /> below neutral
        </span>
      </div>
      {AXIS_ORDER.map((axis) => {
        const value = balancePoints[axis]
        const meta = AXIS_META[axis]
        const isMainConcern = axis === mainConcern
        const magnitudePct = (Math.abs(value) / domain) * 50
        return (
          <div
            key={axis}
            className={`balance-row${isMainConcern ? ' balance-row-main-concern' : ''}`}
          >
            <div className="balance-label">
              {meta.label}
              {isMainConcern && <span className="balance-badge">main concern</span>}
            </div>
            <div
              className="balance-track"
              title={`${meta.label}: ${formatValue(value)} — ${value >= 0 ? meta.positive : meta.negative}`}
            >
              <div className="balance-center" />
              <div
                className={`balance-fill balance-fill-${value >= 0 ? 'positive' : 'negative'}`}
                style={
                  value >= 0
                    ? { left: '50%', width: `${magnitudePct}%` }
                    : { right: '50%', width: `${magnitudePct}%` }
                }
              />
            </div>
            <div className="balance-value">{formatValue(value)}</div>
            <div className="balance-caption">
              {meta.positive} · {meta.negative}
            </div>
          </div>
        )
      })}
    </div>
  )
}
