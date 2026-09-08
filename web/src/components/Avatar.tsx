import { avatarOutline, computeAvatarGeometry, toSvgPath } from '../lib/avatarGeometry'
import type { Measurements } from '../lib/types'

interface AvatarProps {
  measurements: Measurements
}

export function Avatar({ measurements }: AvatarProps) {
  const geometry = computeAvatarGeometry(measurements)
  const path = toSvgPath(avatarOutline(geometry))
  const height = 10 + geometry.torsoHeight + geometry.legHeight + 5

  return (
    <svg
      viewBox={`0 0 100 ${height}`}
      width={160}
      height={160 * (height / 100)}
      role="img"
      aria-label="To-scale silhouette drawn from your measurements"
    >
      <path d={path} fill="#c9b8ff" stroke="#5a4a99" strokeWidth={1} strokeLinejoin="round" />
    </svg>
  )
}
