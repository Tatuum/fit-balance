# Web app overview

How the whole `web/` app works today: what each component owns, where
state lives, and which API endpoint feeds which part of the page. The
avatar's geometry has its own write-up
([`phase5-avatar.md`](phase5-avatar.md)); this file covers everything
around it. The reasoning behind the scoring and advice the page shows
lives in `CURRENT_STATE.md`, not here.

**Files:** `web/src/App.tsx`, `web/src/components/*.tsx`,
`web/src/lib/api.ts`, `web/src/lib/types.ts`, `web/src/lib/garments.ts`,
`web/src/lib/measurements.ts`

### 1. Component tree

`main.tsx` mounts `<App />` into the `#root` div in `index.html`.
`App` is the only component that owns the measurements; everything
else receives them as props.

```
App                        owns: form {measurements, drafts}, techniqueAdvice, techniqueAdviceError
 ├─ MeasurementGuide       static "how to measure" diagram + caption (no props)
 ├─ Avatar                 props: measurements → to-scale silhouette
 ├─ DimensionAdvice        props: dimensions  (from POST /technique-recommendations)
 └─ GarmentBalance         props: measurements
      │                    owns: garments, garmentsError, selectedItemId, advice, error
      ├─ Avatar            props: measurements + effectTags → dashed overlay
      └─ DimensionAdvice   props: dimensions  (the verdict's `suggestions`)

BalancePointsChart         built and tested, rendered nowhere
```

The page has two columns. The left holds a `fieldset` of seven
`type="number"` inputs (`step="0.1"`, with `min` and `max`), one per
field of `Measurements`, starting from `DEFAULT_MEASUREMENTS` in
`App.tsx`. A field that is empty or out of range is marked and shows
"Enter 120–230 cm" style text; see section 3. The right holds the
avatar, a "What to look for" section (`DimensionAdvice`), and the
"Try on a garment" section (`GarmentBalance`).

### 2. State and data flow

| Where | State | Starts as | Changed by |
|---|---|---|---|
| `App` | `form` = `{ measurements, drafts }` | `initialFormState(DEFAULT_MEASUREMENTS)` | the seven inputs' `onChange`, through `applyInput` |
| `App` | `techniqueAdvice` | `null` | the debounced `/technique-recommendations` call |
| `App` | `techniqueAdviceError` | `null` | same call, on failure |
| `GarmentBalance` | `garments` | `[]` | `GET /garments`, once on mount |
| `GarmentBalance` | `selectedItemId` | `''` | the dropdown |
| `GarmentBalance` | `advice`, `error` | `null` | the debounced `/balance-garment` call |

Two flows run from one keystroke in a measurement field:

```
keystroke → setForm(applyInput) → App re-renders (a new valid value changes form.measurements)
   ├─ Avatar redraws immediately (pure maths, no network)
   ├─ App effect: wait 500 ms → POST /technique-recommendations → DimensionAdvice
   └─ GarmentBalance effect: if a garment is selected,
      wait 500 ms → POST /balance-garment → verdict, reasons, overlay avatar
```

Both effects use the same pattern: `setTimeout(..., 500)` started by the
effect and `clearTimeout` returned as its cleanup, so a burst of typing
produces one request after the user stops. The effect re-runs whenever
`measurements` changes (and, in `GarmentBalance`, `selectedItemId`).
With no garment selected, the second effect clears `advice` and `error`
and sends nothing.

`updateMeasurement(key)` in `App.tsx` returns the `onChange` handler for
one field. It passes the typed text to `applyInput` in
`lib/measurements.ts`: `setForm((prev) => applyInput(prev, key, text))`.
`form.measurements` is always the last valid set and is what everything
else reads; `form.drafts` holds each field's text as typed, so a field
can be empty or out of range without that value reaching the avatar or
the API. `applyInput` returns the same `measurements` object when the
text is invalid, so the advice effect does not re-run and no request is
sent.

### 3. API client and types

`lib/api.ts` has one function per endpoint the page uses:

| Function | Request | Used by |
|---|---|---|
| `getTechniqueRecommendations(measurements)` | `POST /technique-recommendations`, body `{measurements}` | `App` |
| `getGarments()` | `GET /garments` | `GarmentBalance` |
| `balanceGarment(measurements, itemId)` | `POST /balance-garment`, body `{measurements, item_id}` | `GarmentBalance` |

The base URL is `import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'`.
A non-2xx response throws `new Error("<name> request failed: <status>")`;
the callers' `.catch` turns that into the error message shown on the
page. `POST /score` exists on the API but has no client function,
because no component calls it.

`lib/types.ts` mirrors the API's response shapes by hand (`Measurements`,
`Verdict`, `Reason`, `DimensionAdvice`, `BalanceGarmentResponse`, and so
on). It is not generated from the Python models and not checked at
runtime, so a change to a response model in `api/main.py` or
`schemas.py` needs the matching edit here.

`lib/measurements.ts` holds the input rules. `MEASUREMENT_RANGES` gives
each field's inclusive range in cm (for example height 120 to 230),
mirroring the `Field(ge=..., le=...)` bounds on `Measurements` in
`schemas.py`, which answers 422 outside them. `parseMeasurement(key,
text)` returns the number, or `null` for an empty field, non-numeric
text or an out-of-range value; `rangeMessage(key)` builds the text shown
under a marked field. The bounds are wide sanity limits chosen by the
project owner, not survey data.

### 4. Components

**`MeasurementGuide`** draws a fixed front-view outline with arrows and
labelled bands for height, shoulder, bust, waist, hip and inseam. Torso
(back waist length) is explained in the caption only, since a front view
can't show it. The body path is built from the right half of the outline
mirrored across `x = 50`, then smoothed with quadratic curves.

**`Avatar`** takes `measurements` and an optional `effectTags`. It
computes the silhouette in `avatarGeometry.ts` (see `phase5-avatar.md`).
When `effectTags` is non-empty it also draws a dashed outline whose
widths are nudged per tag by `applyEffectAdjustments()`. Only
`GarmentBalance` passes tags, so the main avatar is always the plain
silhouette.

**`DimensionAdvice`** renders one card per dimension: its label, a
"stands out" badge when `pronounced`, a plain-language sentence, and
"seek" and "avoid" lists of catalog item labels. The sentence comes from
the `DESCRIBE` table in the file, keyed by axis and chosen from the
backend's `notable`, `direction` and `pronounced` fields. It is wording
only; no scoring logic lives in the component.

**`GarmentBalance`** is the "Try on a garment" section. It fills a
`<select>` from `getGarments()`, grouped into `<optgroup>`s by slot
(`groupBySlot` and `SLOTS` in `lib/garments.ts`, in the order top,
bottom, dress, outerwear). Once an item is chosen it shows the
recommendation, the score, one line per reason (helps or hurts, with the
axis label from `AXIS_LABELS`), the overlay avatar, and, when the
verdict has suggestions, a "How to balance it" block reusing
`DimensionAdvice`.

**`BalancePointsChart`** turns the five balance points into plain-language
rows with a "main concern" or "key asset" badge. It has a test and is not
rendered by any component.

### Testing / verification

`vitest` covers the pure code only: `lib/avatarGeometry.test.ts`,
`lib/garments.test.ts`, `lib/measurements.test.ts` (the range checks and
`applyInput`) and `components/BalancePointsChart.test.ts` (the badge text
helper). There are no render tests for `App`, `GarmentBalance`
or `DimensionAdvice`. `./check.sh` runs `tsc --noEmit` and `vitest run`
for `web/`. Manual verification: run the API and `npm run dev`, change a
measurement, and confirm the avatar and advice update; pick a garment and
confirm the verdict appears. `npm run lint` (oxlint) is not part of
`check.sh` or CI.

### Gotchas / open questions

- **Ranges are kept in two places.** `MEASUREMENT_RANGES` in
  `lib/measurements.ts` and the bounds in `schemas.py` must match; the
  API enforces its own, so a drift shows up as a 422 for a value the form
  accepted.
- **Debounce doesn't cancel an in-flight request.** The cleanup clears
  the timer only. A slow earlier response can arrive after a newer one
  and overwrite it, in both effects.
- **Hand-kept copies of backend values.** `BalancePointsChart.tsx`
  mirrors `IMBALANCE_DEADZONE = 0.05` and the waist threshold `0.15`
  from the Python engine, and `GarmentBalance.tsx`'s `AXIS_LABELS`
  repeats the labels in `technique_advice.py`'s `DIMENSIONS` plus one for
  `shoulder_hip_balance`. Each carries a "keep in sync" comment, but
  nothing enforces it.
- **Lint warnings.** oxlint reports `GarmentBalance` calling a setter
  synchronously inside an effect, and `BalancePointsChart` exporting a
  non-component alongside a component.
