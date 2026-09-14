/**
 * Static "how to measure" illustration, styled after standard body-
 * measurement clipart: a front-facing outline with a full-height arrow,
 * horizontal bust/waist/hip bands, and an inseam arrow between the legs.
 * Fixed reference figure — not driven by user data.
 *
 * torso (back waist length) isn't drawn here: it's a measurement taken
 * along the back (nape of neck to waist), which a front-view outline can't
 * honestly depict, so it's explained in the caption instead.
 */

// Right-half outline keypoints, neck down to the crotch on the centerline.
// The body path mirrors these across x=50 to close the full silhouette.
const RIGHT_OUTLINE: [number, number][] = [
  [54, 26], // neck
  [74, 33], // shoulder
  [80, 55], // outer arm, upper
  [77, 82], // outer arm, wrist
  [81, 90], // hand, outer
  [73, 93], // hand, tip
  [68, 85], // hand, inner
  [62, 60], // inner arm, elbow
  [59, 40], // armpit
  [59, 48], // chest / bust level
  [54, 72], // waist level
  [61, 95], // hip level
  [64, 150], // outer knee
  [62, 200], // outer ankle
  [68, 206], // outer foot
  [66, 210], // toe
  [55, 208], // inner foot
  [53, 200], // inner ankle
  [51, 150], // inner knee
]
// Below hip level (y=95, the "hip level" outline point above), not at it —
// the hip measurement is the fullest point of the hips/glutes, while the
// crotch (where inseam starts) is where the legs fork, noticeably lower.
const CROTCH: [number, number] = [50, 118]

const HEAD = { cx: 50, cy: 14, r: 13 }
const FEET_Y = 210
const BODYHEIGHT_X = -15
const LABEL_X = 95

// SHOULDER sits over the upper arm (between the shoulder point and armpit),
// not literally at the shoulder-point outline coordinate — the tape wraps
// around the fullest part of the shoulders/upper arms, not the seam.
const BANDS = [
  { y: 36, leftEdge: 100 - 77, label: 'SHOULDER' },
  { y: 48, leftEdge: 100 - 59, label: 'BUST' },
  { y: 72, leftEdge: 100 - 54, label: 'WAIST' },
  { y: 95, leftEdge: 100 - 61, label: 'HIP' },
]

// Rounds every corner of a closed polygon into a smooth curve: each vertex
// becomes a quadratic-curve control point, pulling the line toward (rather
// than through) it, with the curve itself passing through the midpoint of
// each edge. Simple and numerically stable (no Catmull-Rom overshoot at
// the sharper turns like the armpit/wrist) — a body outline reads as a
// natural, hand-drawn silhouette instead of the straight-segment polygon
// this replaces.
//
// `sharp` vertex indices are drawn as an exact straight-line pass-through
// instead of rounded — the crotch needs this: rounding it (cutting the
// corner toward each inner-leg midpoint) bulges the curve out sideways
// across the big vertical gap down to the knees, tangling visually with
// the INSEAM arrow drawn straight down from that same point.
function smoothClosedPath(points: [number, number][], sharp: Set<number> = new Set()): string {
  const n = points.length
  const midpoint = (a: [number, number], b: [number, number]): [number, number] => [
    (a[0] + b[0]) / 2,
    (a[1] + b[1]) / 2,
  ]
  const start = sharp.has(n - 1) ? points[n - 1] : midpoint(points[n - 1], points[0])
  const segments = points.map((point, i) => {
    if (sharp.has(i)) {
      return `L ${point[0]} ${point[1]}`
    }
    const next = points[(i + 1) % n]
    const m = midpoint(point, next)
    return `Q ${point[0]} ${point[1]} ${m[0]} ${m[1]}`
  })
  return `M ${start[0]} ${start[1]} ${segments.join(' ')} Z`
}

function buildBodyPath(): string {
  const left = [...RIGHT_OUTLINE].reverse().map(([x, y]) => [100 - x, y] as [number, number])
  const points = [...RIGHT_OUTLINE, CROTCH, ...left]
  return smoothClosedPath(points, new Set([RIGHT_OUTLINE.length]))
}

export function MeasurementGuide() {
  const bodyPath = buildBodyPath()

  return (
    <figure className="measurement-guide">
      <svg
        viewBox="-35 -8 170 238"
        width={260}
        height={260 * (238 / 170)}
        role="img"
        aria-label="Diagram showing where to take each body measurement"
      >
        <defs>
          <marker
            id="mg-arrow"
            viewBox="0 0 10 10"
            refX={5}
            refY={5}
            markerWidth={6}
            markerHeight={6}
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 Z" fill="#111" />
          </marker>
        </defs>

        <circle cx={HEAD.cx} cy={HEAD.cy} r={HEAD.r} fill="none" stroke="#111" strokeWidth={1.5} />
        <path d={bodyPath} fill="none" stroke="#111" strokeWidth={1.5} strokeLinejoin="round" />

        {/* BODYHEIGHT */}
        <line
          x1={BODYHEIGHT_X}
          y1={HEAD.cy - HEAD.r}
          x2={BODYHEIGHT_X}
          y2={FEET_Y}
          stroke="#111"
          strokeWidth={1}
          markerStart="url(#mg-arrow)"
          markerEnd="url(#mg-arrow)"
        />
        <text
          x={BODYHEIGHT_X - 4}
          y={(HEAD.cy - HEAD.r + FEET_Y) / 2}
          fontSize={7}
          fontWeight="bold"
          fill="#111"
          textAnchor="middle"
          transform={`rotate(-90 ${BODYHEIGHT_X - 4} ${(HEAD.cy - HEAD.r + FEET_Y) / 2})`}
        >
          BODYHEIGHT
        </text>

        {/* BUST / WAIST / HIP */}
        {BANDS.map(({ y, leftEdge, label }) => (
          <g key={label}>
            <line x1={leftEdge} y1={y} x2={LABEL_X} y2={y} stroke="#111" strokeWidth={1} />
            <text x={LABEL_X + 2} y={y + 2.5} fontSize={7} fontWeight="bold" fill="#111">
              {label}
            </text>
          </g>
        ))}

        {/* INSEAM */}
        <line
          x1={50}
          y1={CROTCH[1]}
          x2={50}
          y2={FEET_Y}
          stroke="#111"
          strokeWidth={1}
          markerStart="url(#mg-arrow)"
          markerEnd="url(#mg-arrow)"
        />
        <text x={50} y={225} fontSize={7} fontWeight="bold" fill="#111" textAnchor="middle">
          INSEAM
        </text>
      </svg>
      <figcaption>
        <strong>shoulder</strong>: straight around the fullest part of the shoulders/upper arms —
        not the seam-to-seam shoulder width tailors use. <strong>bust/waist/hip</strong>: straight
        around, at the fullest (bust/hip) or narrowest (waist) point.{' '}
        <strong>inseam</strong> (leg): crotch straight down to the floor.{' '}
        <strong>bodyheight</strong>: standing, barefoot.{' '}
        <strong>torso</strong> (not pictured — it's a back measurement): nape of neck (C7
        vertebra) straight down to the natural waist, along the back.
      </figcaption>
    </figure>
  )
}
