import {
  applyEffectAdjustments,
  avatarOutline,
  computeAvatarGeometry,
  headEllipse,
  toSvgPath,
} from '../lib/avatarGeometry'
import type { Measurements } from '../lib/types'

interface AvatarProps {
  measurements: Measurements
  /** Positive ("helps") effect tags from a scored outfit's reasons — draws
   * a dashed overlay sketching the corrected line on top of the body
   * outline. Spike/prototype, see avatarGeometry.ts. */
  effectTags?: string[]
}

export function Avatar({ measurements, effectTags }: AvatarProps) {
  const geometry = computeAvatarGeometry(measurements)
  const path = toSvgPath(avatarOutline(geometry))
  const head = headEllipse(geometry)

  const garmentPath =
    effectTags && effectTags.length > 0
      ? toSvgPath(avatarOutline(applyEffectAdjustments(geometry, effectTags)))
      : null

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
      {garmentPath && (
        <path
          d={garmentPath}
          fill="none"
          stroke="#1f9d7a"
          strokeWidth={1.2}
          strokeDasharray="3 2"
          strokeLinejoin="round"
        />
      )}
    </svg>
  )
}
