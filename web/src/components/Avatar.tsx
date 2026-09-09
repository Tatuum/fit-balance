import { avatarOutline, computeAvatarGeometry, headEllipse, toSvgPath } from '../lib/avatarGeometry'
import type { Measurements } from '../lib/types'

interface AvatarProps {
  measurements: Measurements
}

export function Avatar({ measurements }: AvatarProps) {
  const geometry = computeAvatarGeometry(measurements)
  const path = toSvgPath(avatarOutline(geometry))
  const head = headEllipse(geometry)

  const top = head.cy - head.ry
  const bottom = 10 + geometry.torsoHeight + geometry.legHeight + 5
  const height = bottom - top

  return (
    <svg
      viewBox={`0 ${top} 100 ${height}`}
      width={160}
      height={160 * (height / 100)}
      role="img"
      aria-label="To-scale silhouette drawn from your measurements"
    >
      <ellipse
        cx={head.cx}
        cy={head.cy}
        rx={head.rx}
        ry={head.ry}
        fill="#c9b8ff"
        stroke="#5a4a99"
        strokeWidth={1}
      />
      <path d={path} fill="#c9b8ff" stroke="#5a4a99" strokeWidth={1} strokeLinejoin="round" />
    </svg>
  )
}
