# fit-balance: Roadmap

Full project history, renumbered as small, independently-shippable
phases. `[x]` shipped, `[~]` partially shipped / in progress, `[ ]`
not started. See `docs/plans/README.md` for the pre-`specs/` record
these are drawn from.

- [x] **Phase 1 — Balance-point calculator + worked-example tests.**
  Pure functions for the women's v0 formula set; the 5 CURRENT_STATE.md worked
  examples as parametrized `pytest` cases. Verified: `pytest` passes
  with all 5 worked examples green; `ruff check` clean.
  (docs/project_docs/phase1-balance-points.md)
- [x] **Phase 2 — Effects table + scoring engine.** `effects.yaml`
  (technique → effect tags) + `scoring.py` producing
  `(verdict, reasons[])`. Verified: `pytest` passes with all 5 worked
  examples green; `ruff check` clean.
  (docs/project_docs/phase2-scoring.md)
- [x] **Phase 4 — FastAPI `/score` endpoint.** Reuses the pydantic
  models unchanged as request/response bodies. Verified: `POST /score`
  via curl/HTTPie returns the same verdict as calling `score()`
  directly for the same inputs (schema reuse guarantees this).
  (docs/project_docs/phase4-api.md)
- [x] **Phase 5 — React/TS web app + parametric SVG avatar.**
  Measurement/garment form → API → geometry-only avatar. Verified:
  manually loaded the web app and confirmed the avatar updates with
  measurement changes. (docs/project_docs/phase5-avatar.md)
- [x] **Phase 6 — Manual garment-item catalog.** (docs/plans/0001)
- [x] **Phase 8 — Single-garment "try it on" balance advice.**
  (docs/plans/0005)
- [x] **Phase 9 — Per-dimension technique recommendations** with
  garment examples. (docs/plans/0006)
- [x] **Phase 10 — Discrete severity-level scoring**, replacing
  continuous cross-axis summation. (docs/plans/0007, ADR 0010)
- [~] **Phase 11 — Corrected overlay avatar (spike).** A dashed
  outline sketching a garment's effect on the silhouette, drawn in the
  single-garment panel. Hand-tuned, not yet validated for visual
  accuracy. (docs/plans/0009)
- [ ] **Phase 12 — Real, LLM-classified garment catalog**, replacing
  the hand-authored `garments.yaml`. Deferred. (docs/plans/0003)
- [~] **Phase 13 — Personal-fit spike:** photo + self-reported tags,
  ahead of the private-closet idea below. Spikes 0 and 1 done; results
  and open follow-ups (`a_line` prompt, `crew_neck`, Spike 2) are in
  docs/plans/0012.
- [ ] **Phase 14 — Deploy v1.** Public API + web app, with the live link
  and a screenshot in the README. No photo upload, auth, or database.

AI-assisted features (photo-upload closet, grounded explanations, a
personal RAG corpus, a tool-calling assistant) aren't committed
phases yet — see `specs/architecture.md`'s "Future development"
section for the early direction. Also unscheduled: multi-garment
outfit parsing, to "recreate this inspo look, adjusted for my
proportions."
