# Phase 5 — React/TS web app + parametric SVG avatar

Renders a to-scale visual silhouette from a user's measurements. A
pure geometric mapping from measurements to shape — no photorealism,
no shape category, per NOTES.md.

**Files:** `web/src/lib/avatarGeometry.ts`, `web/src/components/Avatar.tsx`

### 1. Avatar geometry from measurements

`computeAvatarGeometry()` (`avatarGeometry.ts`) turns a `Measurements`
into widths, a head size, and torso/leg heights — every value derived
from the entered cm numbers through one shared scale factor, not from
balance-point ratios:

```ts
const scale = TARGET_FIGURE_HEIGHT / m.height
const widthOf = (circumference: number) => circumference * WIDTH_FROM_CIRCUMFERENCE * scale
```

`WIDTH_FROM_CIRCUMFERENCE = 0.32` treats each circumference as an
ellipse cross-section rather than a circle (`circumference / π ≈
0.318`, nudged up slightly for real torso depth). Two inputs aren't
measured at all: neck and ankle are drawn as a fixed ratio of a nearby
measured width (`NECK_TO_SHOULDER_RATIO = 0.45`,
`ANKLE_TO_HIP_RATIO = 0.3`), and the head is sized off total figure
height using the classic figure-drawing convention of ~7.5
head-heights per body, not off the already-inflated shoulder width.
None of these three are scored or meant to be anthropometrically
exact — they exist for visual completeness only.

### 2. Outline and SVG path

`avatarOutline()` places seven keypoints down the right half of the
body (neck, shoulder, bust, waist, hip, knee, ankle) at heights
derived from `torsoHeight`/`legHeight`, then mirrors them to build the
full silhouette. `toSvgPath()` turns that keypoint list into a closed
curve — each segment a Catmull-Rom spline converted to an equivalent
cubic Bezier — so the rendered line passes through every keypoint as a
smooth body outline instead of a faceted polygon. Both functions are
pure (no DOM, no React), which is what keeps them unit-testable
independent of how they're eventually rendered.

### 3. Rendering

`Avatar.tsx` is a thin wrapper: call `computeAvatarGeometry()`, build
the path with `toSvgPath(avatarOutline(...))` and the head with
`headEllipse()`, and render both into an `<svg>` sized to the
figure's own height so the viewBox always frames the whole silhouette
regardless of the user's actual height.

### Testing / verification

`web/src/lib/avatarGeometry.test.ts` covers `computeAvatarGeometry`,
`headEllipse`, and `avatarOutline`/`toSvgPath` directly, independent of
React. Manual verification: load the web app and confirm the avatar
updates with measurement changes.

### Gotchas / open questions

- `Avatar.tsx` also accepts an optional `effectTags` prop that draws a
  dashed "corrected line" overlay via `applyEffectAdjustments()`. That
  overlay is a later, spike-quality addition (Phase 11 — hourglass
  silhouette goal, unwired) hand-tuned for visual legibility only, not
  part of what this phase shipped — out of scope for this doc.
