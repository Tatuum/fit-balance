import { avatarOutline, computeAvatarGeometry, toSvgPath } from '../lib/avatarGeometry'
import type { BalancePoints } from '../lib/types'

interface AvatarProps {
  balancePoints: BalancePoints
}

export function Avatar({ balancePoints }: AvatarProps) {
  const geometry = computeAvatarGeometry(balancePoints)
  const path = toSvgPath(avatarOutline(geometry))
  const height = 10 + geometry.torsoHeight + geometry.legHeight + 5

  return (
    <svg
      viewBox={`0 0 100 ${height}`}
      width={160}
      height={160 * (height / 100)}
      role="img"
      aria-label="Parametric silhouette reflecting the entered measurements"
    >
      <path d={path} fill="#c9b8ff" stroke="#5a4a99" strokeWidth={1} strokeLinejoin="round" />
    </svg>
  )
}
