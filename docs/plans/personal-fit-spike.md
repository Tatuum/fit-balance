# Personal-fit spike: photo + self-reported tags, before Stage 4.5's closet feature

Status: **Spike 0 done** — 4 garments checked against the CLI across two
bodies, all agreed with judgment (including one deliberate AVOID case).
Narrow vocabulary coverage noted as an expected limitation, carried into
Spike 1 below rather than addressed now. **Spike 1 next.**

## Context

`plan.md`'s Stage 4.5 already plans a private photo-upload closet: user
uploads a garment photo, a multimodal LLM extracts technique tags, user
reviews/edits, then the unchanged scoring engine produces a verdict. That
plan's first deliverable requires building auth + a persistent database
before anyone knows whether the underlying idea works at all.

Two refinements changed the shape of the riskiest question:

1. The system's actual unproven bet isn't "can a model read a photo" — it's
   "does the deterministic scoring engine's verdict agree with how real
   people already feel about clothes they own and like." That can be tested
   with zero AI.
2. Asking the user for a short reason + letting them pick from the existing
   closed technique vocabulary (instead of trusting free text or a photo
   alone) gives a second, independent signal to cross-check LLM-proposed
   tags against — and it's free ground truth, since it's collected as a
   byproduct of using the feature, not hand-labeled separately.

This plan stages that validation as two small spikes, done before touching
auth/DB/UI. It does **not** change `balance_points.py`, `scoring.py`, or
`effects.yaml` — if a spike surfaces a real rule or vocabulary gap, that
becomes its own separate engine-change (ADR via `new-decision` + a
`NOTES.md` worked-example update), not part of this plan.

**Relationship to `docs/plans/garment-catalog-llm-classification.md`:**
that plan (not started) builds the shared, retail-text-sourced garment
catalog via LLM classification, with a `tag_candidates` review queue for
anything outside the closed vocabulary. This spike is complementary, not a
duplicate: it validates *personal* photo + self-report as a future input
path for Stage 4.5's private closet, not the shared catalog. Both share the
same pattern — closed vocabulary, human-reviewed escape hatch for
unmatched effects — so this plan reuses that pattern's terminology (a "tag
candidate" is anything a spike surfaces that doesn't map cleanly) but keeps
its own artifacts (no shared DB, no dependency on
`scripts/ingest_garments.py`).

**Doc footprint:** this file is the only new documentation this plan adds.
Spike results are plain data (or informal notes), not new docs. An ADR and
`NOTES.md` update only happen later, and only if a spike actually surfaces
a real rule/vocabulary gap — that's the existing standing rule for any
engine change, not new overhead from this plan.

## Spike 0 — self-tagging, zero new code

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
  (not just self-report bias — see caveat below), that's a signal to open a
  normal engine-change (separate ADR). If the rules mostly agree, move to
  Spike 1.

No new code, no dependencies, no test changes — this step is pure usage of
what already exists.

## Spike 1 — add the photo + LLM proposal, still no persistence

Validates whether an LLM can map a real garment photo into the existing
technique vocabulary well enough to be useful, graded against your own
picks instead of a hand-built labeled set.

- New file `scripts/spike_photo_tagging.py` — not imported by the app,
  same "offline utility" posture as the (not-yet-built)
  `scripts/ingest_garments.py` in the catalog-classification plan. Three
  pieces:
  - `SpikeResult(BaseModel)`: `techniques: list[str]`,
    `uncertain_note: str | None = None` — same "validate at the boundary"
    pattern `schemas.py` already uses; the LLM's reply is untrusted input
    like any other.
  - `build_prompt(vocabulary: list[str]) -> str` (pure): embeds the closed
    vocabulary (reuse `scoring.load_effects_table()`'s keys, don't
    hardcode a duplicate list) and `SpikeResult`'s JSON schema, asking for
    a reply matching that shape.
  - `parse_response(raw: str) -> SpikeResult` (pure): extracts the JSON
    from the reply and calls `SpikeResult.model_validate_json(...)` —
    pydantic handles parsing and validation together, raising a clear
    error on malformed output instead of a silent bad parse.
  - `tag_photo(image_path: Path) -> SpikeResult`: the actual network
    call — reads the image, sends it + the built prompt to Claude Sonnet
    (stronger vision capability than a cheaper model, per the ShelfScanner
    article's own finding that smaller models missed more detail on real
    photos — this is the first check of whether the idea works at all, not
    yet a cost-optimization pass), hands the reply to `parse_response`.
- `build_prompt`/`parse_response` are unit-tested with a stubbed response
  (`tests/test_spike_photo_tagging.py`), no network needed for
  `pytest`/`./check.sh`. `tag_photo` itself isn't unit-tested (needs a real
  API key/network).
- Usage: for the same items (or new ones), the script prints the LLM's
  proposed techniques. Pick your own techniques *before* looking at its
  proposal (avoids anchoring), then compare. Extend the same plain-data log
  from Spike 0 with a "LLM proposed" field and an agree/disagree note —
  still data, not a doc.
- Needs `ANTHROPIC_API_KEY` locally; never run in CI, same as the catalog
  plan's ingestion script. New `spike = ["anthropic>=0.40"]` optional
  dependency group in `pyproject.toml` — nothing already in the project
  covers the Anthropic SDK.

## Spike 2 (not built now, noted only)

If Spike 1 shows photo-only extraction struggling, feed the one-sentence
rationale into the same prompt so the LLM reconciles photo + words. Not
scheduled — revisit only if Spike 1's results warrant it.

## Explicitly out of scope for this plan

No auth, no persistent database, no closet UI, no changes to `scoring.py`
/`balance_points.py`/`effects.yaml`, no integration with the shared
garment-catalog classification effort. All of that stays exactly as
already planned in `plan.md`'s Stage 4.5 / the catalog-classification plan.

## Caveat to keep in mind (not a blocker)

In both spikes, the same person picks the tags and judges whether the
verdict "feels right," which can bias toward flattering self-description or
anchor on whatever the checklist shows first. This doesn't invalidate a
clean run, but a clean run only shows the rules aren't *obviously* wrong —
not that they're provably correct.

## Sequencing / commits

1. Spike 0: no commit needed unless you want the raw data saved
   (`data/personal_fit_spike.json`, gitignored or committed, your call) —
   no new doc either way.
2. This plan file, committed as `docs/plans/personal-fit-spike.md` — the
   only new documentation this plan adds.
3. Spike 1: `scripts/spike_photo_tagging.py` + its stubbed-response test,
   one commit. Run it locally against your own `ANTHROPIC_API_KEY` (not
   something to execute during planning/implementation review).
4. If either spike surfaces a real rule/vocabulary gap: a separate,
   independent engine-change commit (ADR + `NOTES.md` update), following
   the existing CLAUDE.md workflow — not bundled into this plan's commits.

## Verification

- Spike 0: `uv run fit-balance score ...` already has test coverage
  (`tests/test_scoring.py`); this step just exercises it manually with real
  inputs — nothing new to automate.
- Spike 1: `uv run pytest tests/test_spike_photo_tagging.py` passes with a
  stubbed LLM response (no network/key needed). `./check.sh` stays green
  throughout — the script and its test are additive, nothing existing
  changes behavior.
- Manual: `ANTHROPIC_API_KEY=... uv run python scripts/spike_photo_tagging.py <path-to-photo>` prints proposed techniques for a real photo.
