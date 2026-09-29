# 0012. Personal-fit spike: photo + self-reported tags, before Stage 4.5's closet feature

Date: 2026-09-23
Status: Active — Spike 0 done, Spike 1 next

**Spike 0 done** — 4 garments checked against the CLI across two
bodies, all agreed with judgment (including one deliberate AVOID case).
Narrow vocabulary coverage noted as an expected limitation, carried into
Spike 1 below rather than addressed now. **Spike 1 next.**

## Requirements

- A person can check whether the styling verdict for a garment they
  already own agrees with their own judgment of whether it fits them.
- A person can write a short reason for why they believe a garment
  fits, alongside the techniques they think it has.
- A photo of a garment can be used to suggest which styling techniques
  it has.
- A suggested set of techniques can be compared against the person's
  own picks, made beforehand so the suggestion doesn't bias them.
- Disagreements between the verdict and the person's own judgment can
  be reviewed to see whether they point at a real rule gap.
- No accounts, saved closet, or permanent storage are introduced by
  this work.

## Context

`ARCHITECTURE.md`'s Stage 4.5 plans a private photo-upload closet, but its
first deliverable needs auth + a database before anyone knows the
underlying idea actually works.

Two refinements narrowed the real risk:
1. The unproven bet isn't "can a model read a photo" — it's "does the
   scoring engine's verdict agree with how people already feel about
   clothes they own." Testable with zero AI.
2. A one-line reason + a pick from the closed vocabulary gives a second
   signal to check LLM-proposed tags against — free ground truth, as a
   byproduct of normal use.

**Relationship to `docs/plans/0003-garment-catalog-llm-classification.md`:**
that plan (not started) builds the shared catalog via LLM classification.
This spike is complementary — it validates *personal* photo + self-report
for Stage 4.5's closet, not the shared catalog — reusing the "tag
candidate" pattern but with its own artifacts (no shared DB, no
`scripts/ingest_garments.py` dependency).

**Doc footprint:** this file is the only new doc. Spike results stay plain
data. An ADR/`NOTES.md` update only happens if a spike surfaces a real
gap — the existing standing rule, not new overhead.

## How it fits into existing architecture

- **Stage/layer:** precursor validation for `ARCHITECTURE.md`'s Stage
  4.5, item 1 (private photo-upload closet) — run deliberately
  *before* that stage's real requirements (auth, database) get built,
  to de-risk the core assumption first.
- **Layering:** `scripts/spike_photo_tagging.py` sits outside every
  existing layer — not imported by `src/fit_balance/`, `api/`, or
  `web/` — matching the engine's "zero UI/network dependencies"
  property. Nothing here changes what an existing layer does.
- **Stack:** the new `anthropic` dependency matches Stage 4.5's own
  stack note ("a multimodal-capable LLM API, called directly, no
  orchestration framework") — not an unplanned addition, just used
  earlier than that stage formally starts.
- **Build order:** doesn't skip ahead. Stays out of Stage 4.5's own
  scope (no auth, no DB — see Out of scope) and stays out of Stage 5
  (CV) entirely — `ARCHITECTURE.md` is explicit that a multimodal LLM
  call describing a garment from a photo "is not a CV pipeline," which
  is exactly this spike's approach.
- **Conflicts found:** none.

## Decision

Validate with two small spikes — self-tagging first, then a photo + LLM
proposal — before touching auth/DB/UI. No change to `balance_points.py`,
`scoring.py`, or `effects.yaml` — a surfaced rule gap becomes its own
engine-change (ADR + `NOTES.md` update), not part of this plan.

## Technical plan

### Spike 0 — self-tagging, zero new code

Validates rule quality, independent of any extraction step.

- Use the existing `fit-balance score` CLI (`src/fit_balance/cli.py`) as-is.
  For 5-10 real garments you own and believe fit you: pick techniques from
  the existing closed vocabulary in `src/fit_balance/effects.yaml`, run
  `uv run fit-balance score --shoulder ... --technique <tag> ...` with your
  own measurements, and write one sentence on *why* you think it fits.
- Log each item: techniques picked, one-line reason, the CLI's verdict, and
  whether it agrees with your existing belief. Keep this as plain data, not
  a new doc — e.g. `data/personal_fit_spike.json` (gitignored, like the
  catalog plan's derived files) or just working notes you keep yourself.
  This is throwaway by design; it doesn't need a permanent markdown record.
- Decision point: if a disagreement traces to a real, explainable rule gap
  (not just self-report bias — see Caveat below), that's a signal to open a
  normal engine-change (separate ADR). If the rules mostly agree, move to
  Spike 1.

No new code, no dependencies, no test changes — this step is pure usage of
what already exists.

### Spike 1 — add the photo + LLM proposal, still no persistence

Validates whether an LLM can map a real garment photo into the existing
technique vocabulary well enough to be useful, graded against your own
picks instead of a hand-built labeled set.

**New files**
- `scripts/spike_photo_tagging.py` — not imported by the app; offline
  utility, same posture as the (not-yet-built)
  `scripts/ingest_garments.py` in the catalog-classification plan.
- `tests/test_spike_photo_tagging.py` — unit tests for the two pure
  functions below.

**Data shape**
- `SpikeResult(BaseModel)`: `techniques: list[str]`,
  `uncertain_note: str | None = None`. Same "validate at the boundary"
  pattern `schemas.py` already uses — the LLM's reply is untrusted
  input like any other.

**Functions**
- `build_prompt(vocabulary: list[str]) -> str` (pure)
  - Input: the closed vocabulary (reuse
    `scoring.load_effects_table()`'s keys, don't hardcode a duplicate
    list).
  - Output: a prompt string embedding that vocabulary +
    `SpikeResult`'s JSON schema.
- `parse_response(raw: str) -> SpikeResult` (pure)
  - Input: the raw LLM reply text.
  - Output: a validated `SpikeResult`, via
    `SpikeResult.model_validate_json(...)` — pydantic parses and
    validates together, raising a clear error on malformed output
    instead of a silent bad parse.
- `tag_photo(image_path: Path) -> SpikeResult` (network call)
  - Input: path to a garment photo.
  - Output: a `SpikeResult` — reads the image, sends it + the built
    prompt to Claude Sonnet, hands the reply to `parse_response`.
  - Why Sonnet, not a cheaper model: stronger vision, per the
    ShelfScanner article's own finding that smaller models missed
    more detail on real photos. This is the first check of whether
    the idea works at all, not yet a cost-optimization pass.

**Dependencies**
- New `spike = ["anthropic>=0.40"]` optional dependency group in
  `pyproject.toml` — nothing already in the project covers the
  Anthropic SDK.
- Needs `ANTHROPIC_API_KEY` locally; never run in CI, same as the
  catalog plan's ingestion script.

**Tests**
- `build_prompt`/`parse_response`: unit-tested with a stubbed
  response, no network needed for `pytest`/`./check.sh`.
- `tag_photo`: not unit-tested — needs a real API key/network.

**Manual usage**
- For the same items (or new ones), the script prints the LLM's
  proposed techniques.
- Pick your own techniques *before* looking at its proposal (avoids
  anchoring), then compare.
- Extend the Spike 0 plain-data log with an "LLM proposed" field and
  an agree/disagree note — still data, not a doc.

### Spike 2 (not built now, noted only)

If Spike 1 shows photo-only extraction struggling, feed the one-sentence
rationale into the same prompt so the LLM reconciles photo + words. Not
scheduled — revisit only if Spike 1's results warrant it.

## Caveat to keep in mind (not a blocker)

In both spikes, the same person picks the tags and judges whether the
verdict "feels right," which can bias toward flattering self-description or
anchor on whatever the checklist shows first. This doesn't invalidate a
clean run, but a clean run only shows the rules aren't *obviously* wrong —
not that they're provably correct.

## Out of scope

No auth, no persistent database, no closet UI, no changes to `scoring.py`
/`balance_points.py`/`effects.yaml`, no integration with the shared
garment-catalog classification effort. All of that stays exactly as
already planned in `ARCHITECTURE.md`'s Stage 4.5 / the catalog-classification plan.

## Steps

- [x] Step 1 — Spike 0: self-tag 5–10 owned garments via the CLI, log
      techniques + reason + verdict + agreement.
- [x] Step 2 — Commit this plan file (the only new doc this plan adds).
- [ ] Step 3 — Spike 1: `scripts/spike_photo_tagging.py` + its
      stubbed-response test, one commit.
- [ ] Step 4 — If either spike surfaces a real rule/vocabulary gap: a
      separate, independent engine-change commit (ADR + `NOTES.md`
      update) — not bundled into this plan's commits.

## Verification

- Spike 0: `uv run fit-balance score ...` already has test coverage
  (`tests/test_scoring.py`); this step just exercises it manually with real
  inputs — nothing new to automate.
- Spike 1: `uv run pytest tests/test_spike_photo_tagging.py` passes with a
  stubbed LLM response (no network/key needed). `./check.sh` stays green
  throughout — the script and its test are additive, nothing existing
  changes behavior.
- Manual: `ANTHROPIC_API_KEY=... uv run python scripts/spike_photo_tagging.py <path-to-photo>` prints proposed techniques for a real photo.

## Updates

<Dated notes for any decision that changed mid-implementation.>
