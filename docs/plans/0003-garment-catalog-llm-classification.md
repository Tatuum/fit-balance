# 0003. Real, LLM-classified garment catalog (replaces hand-authored `garments.yaml`)

Date: 2026-09-11
Status: Not started — deferred, `garments.yaml` is still hand-authored

**Not started.** Planned only — `garments.yaml` is still the live
19-item hand-authored catalog.

## Context

The garment catalog (`src/fit_balance/garments.yaml`, 19 items) is currently
hand-typed: a human picks an item name and manually assigns which of the 11
`effects.yaml` techniques it uses. This is the weakest part of the project
for portfolio purposes — nothing is *inferred*, there's no real data, and the
backend does no reasoning over it; it's a lookup table.

The fix: source garment entries from real product text (titles/descriptions
of actual retail listings) and use an LLM to classify each one into the
existing closed technique/effect-tag vocabulary — with a human-reviewed
escape hatch for techniques that don't fit anything that exists yet. This
turns the catalog into a genuine data pipeline (ingest → classify → store →
serve) instead of a static lookup, and doubles as this project's first real
persistence layer (SQLite), setback for a possible future personalization
feature (not in scope here).

Decided with the user going in:
1. **Source**: real garment product text, LLM-classified — not a live paid
   API, not photo/CV (stage 5 stays explicitly out of scope per CLAUDE.md).
2. **Vocabulary**: classification stays within the current 11 techniques by
   default; anything that doesn't fit becomes a human-reviewed "tag
   candidate," never auto-wired into `effects.yaml`/`AXIS_RULES`.
3. **Scale**: ~40-60 items — deliberately small enough that
   `recommend.py`'s combinatorial enumeration and the frontend's
   radio-button-per-slot picker both keep working unchanged.
4. **Storage**: a real database (SQLite), not just a bigger generated file.

## Architecture

```
data/raw_garments.json   (hand-collected real listings, committed)
data/gold_garments.json  (hand-labeled eval fixture, committed)
        │  offline, needs ANTHROPIC_API_KEY, never run by tests/CI
        ▼
scripts/ingest_garments.py  ──uses──►  src/fit_balance/classify.py
        │
        ▼
data/garments_seed.json  (classified result + tag_candidates, committed)
        │  deterministic rebuild, no network, runs at import/test-setup
        ▼
src/fit_balance/db.py  ──►  data/fit_balance.db (sqlite, gitignored, derived)
        │
        ▼
src/fit_balance/garments.py   (SAME public interface as today)
        │
        ▼
recommend.py, api/main.py, cli.py   — unchanged
```

Two things share the sqlite file but behave differently:
- `garment_items`/`garment_item_techniques`: a **derived cache** of
  `garments_seed.json` — rebuilt whenever the seed's content hash changes.
- `tag_candidates`: **real stateful data** (human accept/reject decisions) —
  re-ingestion upserts new/updated candidates but never overwrites an
  already-`accepted`/`rejected` row.

## Dataset

Hand-collect ~40-60 real product titles + descriptions from public retailer
listings (favor descriptions that actually use fit/silhouette language —
"bodycon," "empire waist," "wide-leg" — over generic fabric-care text),
spread across all 4 slots. Store as `data/raw_garments.json`:
`{id, title, description, slot, source_url, source_retailer, collected_at}`.
`id` and `slot` are assigned by the human at collection time (slot is a
simple, deterministic category — not the LLM's job); only technique/effect
classification is probabilistic.

Rejected a downloadable public dataset (Kaggle H&M/DeepFashion/etc.):
requires account auth (violates "no keys needed to reproduce"), is
image-centric with thin free text, and at 100k+ rows needs a curation pass
anyway — at that point hand-picking is less total work and higher signal.

`data/gold_garments.json`: 15-20 hand-labeled items (same text, human-written
`expected_techniques`) for the eval harness — kept independent of whatever
the classifier actually outputs, so the eval isn't circular.

## New/modified files

**`src/fit_balance/classify.py`** (new) — `build_prompt()` embeds the closed
vocabulary (imported from `scoring.EFFECTS_TABLE`) and requests structured
output: `techniques: list[str]` (constrained to existing keys),
`tag_candidate: {proposed_name, suggested_effects, reasoning} | null`,
`reasoning: str`. `classify_item()` calls the Anthropic API (a cheap model —
Haiku is enough for short structured classification). Prompt-building and
response-parsing are pure functions, unit-tested with a stubbed response, no
network needed for `pytest`.

**`scripts/ingest_garments.py`** (new, not imported by the app) — reads
`data/raw_garments.json`, skips items already classified against an
unchanged content hash (idempotent reruns), calls `classify.classify_item()`,
writes `data/garments_seed.json`. Upserts `tag_candidates` by id (merges
`example_item_ids`, bumps `last_seen_at`) without a `status` field in the
seed itself — status only ever lives in the DB, so reruns can't clobber a
human review decision. Warns (doesn't fail) on zero-technique classifications
so a thin raw description gets flagged for re-collection.

**`scripts/eval_classifier.py`** (new) — runs `classify.classify_item()`
against `data/gold_garments.json`, reports per-tag and macro
precision/recall/F1 against `expected_techniques` (set-based, multi-label).
Thin pytest wrapper `tests/test_classifier_eval.py`, skipped unless
`ANTHROPIC_API_KEY` is set, asserting a minimum macro-F1 — not part of the
default `pytest`/`check.sh` run, but a real regression gate once a threshold
is picked from the first live run. This is the strongest AI-engineering
portfolio signal in the feature — a reproducible, numeric eval, not a vibe
check.

**`src/fit_balance/db.py`** (new) — plain `sqlite3` (no ORM — the workload
is a ~40-60-row read-mostly catalog plus a small review queue; SQLAlchemy
would be a real dependency and migration surface for something stdlib
handles in ~150 lines). Schema: `garment_items`, `garment_item_techniques`
(junction table), `tag_candidates` (id, proposed_name, suggested_effects,
reasoning, example_item_ids, status ∈ pending/accepted/rejected,
first_seen_at/last_seen_at/reviewed_at/reviewer_note), `schema_meta`
(tracks the seed's content hash so `ensure_built()` knows whether to
rebuild). DB path via `FIT_BALANCE_DB_PATH` env var, default
`data/fit_balance.db` — gitignored, fully derived, rebuilt from the
committed seed on first run/test-setup.

**`src/fit_balance/garments.py`** (modified) — swap YAML-loading for
`db.ensure_built()` + `db.load_catalog()`; delete `load_garments_table`,
`GARMENTS_TABLE`, `_GARMENTS_PATH`. Delete `garments.yaml` (fully
superseded — recoverable via git history if ever needed). Extract the
dedup/merge logic out of `resolve_outfit` into a standalone
`merge_techniques(items: list[GarmentItem]) -> GarmentAttributes`, so tests
can build hand-crafted `GarmentItem`s and exercise scoring/attribution
without depending on real catalog ids. `GarmentItem`, `get_item`,
`attribute_reasons`, `AttributedReason`, `UnknownGarmentItemError` keep
their exact interface — `recommend.py` and `api/main.py` need no changes.

**`src/fit_balance/cli.py`** (modified) — new `candidates` sub-app:
`list [--status pending]`, `show <id>`, `accept <id> [--note]`,
`reject <id> [--note]`. `accept` only records the review decision in
`tag_candidates.status` — it never touches `effects.yaml`; it prints
guidance to run the `new-decision` skill and wire the tag in manually,
preserving the same deliberate-vocabulary-growth gate as decisions 0003/0006.

**`docs/decisions/0010-classified-garment-catalog-and-tag-candidate-review.md`**
(new, via the `new-decision` skill) — context/decision/consequences for:
catalog now sourced from real text via LLM classification into the existing
vocabulary only; a human-reviewed `tag_candidates` queue for anything that
doesn't fit; accepting a candidate never auto-edits the vocabulary.
Update `NOTES.md`'s "Garment catalog" section to describe the new flow and
link to 0010, in the same commit that changes `garments.py`'s behavior (per
CLAUDE.md's decide-in-writing-as-part-of-the-same-change rule).

**`pyproject.toml`** — new optional `ingest = ["anthropic>=0.40"]` group,
not part of `dev`/`api`, so `uv run pytest`/`./check.sh` never need it
installed.

## Test changes

- `tests/test_garments.py`: `test_catalog_covers_all_known_techniques`
  (exact `==` equality) → rewritten as `catalog_techniques <= set(EFFECTS_TABLE)`
  (subset, not 1:1 — real data won't necessarily hit every technique).
  `test_resolve_outfit_dedupes_identical_technique_across_items`,
  `test_attribution_reuses_worked_example_5`,
  `test_attribution_lists_both_items_when_tags_overlap`: rewritten to build
  small hand-crafted `GarmentItem` fixtures directly and call
  `merge_techniques()`/`score()`/`attribute_reasons()`, independent of real
  catalog ids — this is what keeps these regression tests meaningful once
  the catalog's exact contents are no longer hand-picked.
  `test_wide_leg_and_rise_items_resolve_to_expected_techniques`: deleted
  (pins the specific old hand-authored catalog, no longer meaningful).
  `test_catalog_has_no_empty_technique_lists`: kept as-is.
- `tests/test_recommend.py`: drop the hardcoded `== 140` combo count,
  compute expected count from live slot counts (already partly done).
- `tests/test_api.py` + new `tests/conftest.py`: add a fixture that
  monkeypatches `fit_balance.garments.CATALOG` to a small deterministic
  dict for the worked-example-5 API test (since `resolve_outfit`/`list_items`
  read the module-level `CATALOG` dynamically, this needs no `api/main.py`
  change).
- New: `tests/test_classify.py` (pure prompt/parse, stubbed response, no
  network), `tests/test_db.py` (schema creation, `ensure_built` idempotency
  and rebuild-on-change, and specifically that `tag_candidates` upsert
  preserves an already-reviewed row's status across a reseed — use
  `tmp_path`-scoped DB files), `tests/test_candidates_cli.py` (Typer
  `CliRunner` against an isolated tmp DB).

## Sequencing (one commit per logical piece, per CLAUDE.md workflow)

1. `data/raw_garments.json` + `data/gold_garments.json` + `.gitignore`
   entries for `data/fit_balance.db`/`data/eval_results/` + a schema-sanity
   test for both JSON files. Largest manual-effort step; do it first.
2. `src/fit_balance/classify.py` (+ unit tests) + `scripts/ingest_garments.py`
   + `scripts/eval_classifier.py` + the new `ingest` dependency group. No
   behavior change to the running app yet.
3. Run ingestion locally (needs your own `ANTHROPIC_API_KEY` — not
   something executable during planning) and commit the resulting
   `data/garments_seed.json`; run the eval script against the gold set and
   sanity-check the macro-F1 before wiring anything downstream to it.
4. `src/fit_balance/db.py`, `garments.py`'s loading swap + `merge_techniques`
   extraction, delete `garments.yaml`. Bundle the `0010` decision doc +
   `NOTES.md` update into this same commit (behavior actually changes here).
   Update `test_garments.py`/`test_recommend.py`/`test_api.py`/`conftest.py`
   in the same commit — `./check.sh` must pass.
5. `cli.py`'s `candidates` sub-app + its tests.
6. `tests/test_classifier_eval.py` wired to a real threshold picked from
   step 3's numbers — separate small commit.

## Known tradeoffs (flagged, not blocking)

- The old tests demonstrated worked-example-5 reproduced *through real
  catalog items*; under real classified data that can't be guaranteed by
  construction, so regression coverage moves to fixture-injected
  `GarmentItem`s instead. Deliberate, not a rigor downgrade — flag if this
  matters enough to hand-pick 1-2 raw items to try to preserve it.
- A fresh clone needs one run (app start or `pytest`) to materialize
  `data/fit_balance.db` from the committed seed — instant/local/deterministic,
  but the `.db` file itself is never committed.
- Real slot distribution across 40-60 items may be uneven, so
  `enumerate_outfit_combinations()`'s count will likely exceed today's 140 —
  expected, not a bug; `recommend.py` itself stays unchanged per the scale
  decision already made.

## Verification

- `./check.sh` green after step 4 and again after step 5 (pytest, ruff,
  `tsc --noEmit`, `vitest run`).
- `uv run fit-balance candidates list` shows any tag candidates surfaced by
  real ingestion; `accept`/`reject` round-trip correctly against a tmp DB in
  tests, and against the real DB manually.
- `uv run uvicorn api.main:app --reload` + the existing web UI: `/garments`
  still renders the radio-button picker correctly (id/label/slot shape
  unchanged), `/score-outfit` and `/recommend-outfits` still return sane
  verdicts for the new catalog.
- `ANTHROPIC_API_KEY=... uv run pytest tests/test_classifier_eval.py -v`
  reports macro-F1 against the gold set.
