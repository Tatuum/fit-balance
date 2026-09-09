import type { BalancePoints } from '../lib/types'

/**
 * Plain-language read of every balance point — no numeric scale, just
 * "Axis: status" with a colored dot. Green means nothing notable here
 * (balanced, or waist_definition reading as a defined asset); the muted dot
 * means this axis has a descriptive trait, which per NOTES.md is not a
 * problem to fix for any axis but waist_definition — no good/bad judgment
 * is baked into the color itself, only "notable vs not."
 *
 * shoulder_hip_balance and bust_hip_balance are combined into one "Top vs
 * hip" row rather than shown separately: NOTES.md documents them as
 * deliberately distinct balance points (a broad-shoulder/narrow-hip build
 * reads differently from a top-heavy-by-bust one, and bust_hip_balance
 * alone would conflate them), but showing "shoulder wider than hip" right
 * next to "hip wider than bust" as two independent lines reads as a
 * contradiction to anyone who doesn't already know shoulder and bust are
 * different measurements. Combining them into one sentence keeps both
 * signals (still two separate numbers underneath, still scored separately)
 * without the apparent self-contradiction.
 */

type Axis = keyof BalancePoints
type SingleAxis = Exclude<Axis, 'shoulder_hip_balance' | 'bust_hip_balance'>

const SINGLE_AXIS_ORDER: SingleAxis[] = ['waist_definition', 'torso_leg_balance', 'frame_scale_dev']

// Mirrors balance_points.IMBALANCE_DEADZONE (Python) — keep these two in
// sync. Below this magnitude, a deviation from 0 is measurement noise, not
// a real proportion difference, for the four axes where 0 is neutral in
// both directions.
const IMBALANCE_DEADZONE = 0.05

const isBalanced = (value: number) => Math.abs(value) < IMBALANCE_DEADZONE
const formatSigned = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(3)}`

type Lean = 'balanced' | 'wider' | 'narrower'

const leanOf = (value: number): Lean => (isBalanced(value) ? 'balanced' : value >= 0 ? 'wider' : 'narrower')

function describeTopVsHip(shoulderHip: number, bustHip: number): string {
  const shoulderLean = leanOf(shoulderHip)
  const bustLean = leanOf(bustHip)

  if (shoulderLean === 'balanced' && bustLean === 'balanced') return 'balanced'
  if (shoulderLean === 'balanced') {
    return bustLean === 'wider' ? 'bust wider than hip' : 'hip wider than bust'
  }
  if (bustLean === 'balanced') {
    return shoulderLean === 'wider' ? 'shoulder wider than hip' : 'hip wider than shoulder'
  }
  if (shoulderLean === bustLean) {
    return shoulderLean === 'wider' ? 'shoulder and bust wider than hip' : 'hip wider than shoulder and bust'
  }
  // Diverge: one wider than hip, the other narrower.
  return shoulderLean === 'wider'
    ? 'broader shoulders, but hip fuller than bust'
    : 'narrower shoulders, but bust fuller than hip'
}

interface AxisMeta {
  label: string
  isBalanced: (value: number) => boolean
  // Status text for the two states. "Not balanced" still splits by sign
  // (two distinct, equally-real traits, e.g. long-torso vs. long-legs).
  // waist_definition's favorable/unfavorable split is already fully
  // captured by isBalanced, so it ignores sign.
  describe: (value: number, balanced: boolean) => string
}

const describeBySign = (positive: string, negative: string) => (value: number, balanced: boolean) =>
  balanced ? 'balanced' : value >= 0 ? positive : negative

const AXIS_META: Record<SingleAxis, AxisMeta> = {
  waist_definition: {
    label: 'Waist definition',
    // NOTES.md documents this axis's own zero point loosely — "~0/− = no
    // natural cinch" — so literal 0 isn't the practically meaningful
    // threshold, and it isn't a symmetric deadzone either (favorable is
    // one-directional). Matches scoring.py's AXIS_RULES reference for
    // defines_waist/clings_to_waist: keep these two in sync.
    isBalanced: (value) => value >= 0.15,
    describe: (_value, balanced) => (balanced ? 'defined waist (an asset)' : 'little to no natural cinch'),
  },
  torso_leg_balance: {
    label: 'Torso vs leg',
    isBalanced,
    describe: describeBySign('long torso', 'long legs'),
  },
  frame_scale_dev: {
    label: 'Frame scale',
    isBalanced,
    describe: describeBySign('reads fuller for height', 'reads slighter for height'),
  },
}

interface BalancePointsChartProps {
  balancePoints: BalancePoints
  mainConcern: string | null
}

export function BalancePointsChart({ balancePoints, mainConcern }: BalancePointsChartProps) {
  const shoulderHip = balancePoints.shoulder_hip_balance
  const bustHip = balancePoints.bust_hip_balance
  const topVsHipBalanced = isBalanced(shoulderHip) && isBalanced(bustHip)
  const topVsHipIsMainConcern = mainConcern === 'shoulder_hip_balance' || mainConcern === 'bust_hip_balance'

  return (
    <div className="balance-chart">
      <div
        className={`balance-row${topVsHipIsMainConcern ? ' balance-row-main-concern' : ''}`}
        title={`Shoulder vs hip: ${formatSigned(shoulderHip)}, Bust vs hip: ${formatSigned(bustHip)}`}
      >
        <span className={`balance-dot balance-dot-${topVsHipBalanced ? 'balanced' : 'notable'}`} />
        <span className="balance-text">
          <span className="balance-label">Top vs hip:</span> {describeTopVsHip(shoulderHip, bustHip)}
        </span>
        {topVsHipIsMainConcern && <span className="balance-badge">main concern</span>}
      </div>
      {SINGLE_AXIS_ORDER.map((axis) => {
        const value = balancePoints[axis]
        const meta = AXIS_META[axis]
        const isMainConcern = axis === mainConcern
        const balanced = meta.isBalanced(value)
        const statusText = meta.describe(value, balanced)

        return (
          <div
            key={axis}
            className={`balance-row${isMainConcern ? ' balance-row-main-concern' : ''}`}
            title={`${meta.label}: ${formatSigned(value)}`}
          >
            <span className={`balance-dot balance-dot-${balanced ? 'balanced' : 'notable'}`} />
            <span className="balance-text">
              <span className="balance-label">{meta.label}:</span> {statusText}
            </span>
            {isMainConcern && <span className="balance-badge">main concern</span>}
          </div>
        )
      })}
    </div>
  )
}
