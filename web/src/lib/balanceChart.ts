import type { BalancePoints } from './types'

/**
 * Text for the badge on whichever row main_concern names. A favorable
 * waist_definition is an asset, not a concern (see balance_points.py's
 * main_concern() docstring) — labeling it "main concern" right next to
 * "an asset" is self-contradictory, so that one case gets its own badge
 * text. Every other axis never carries a favorable/asset framing, so it
 * always reads as "main concern".
 *
 * Lives in lib/ rather than next to BalancePointsChart so the component
 * file exports only components (React's fast refresh needs that).
 */
export function mainConcernBadgeText(axis: keyof BalancePoints, balanced: boolean): string {
  return axis === 'waist_definition' && balanced ? 'key asset' : 'main concern'
}
