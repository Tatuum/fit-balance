# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

fit-balance is an explainable styling-recommendation engine: instead of a black-box
body-shape label or a photorealistic try-on render, it surfaces *why* a garment
technique works with or against a user's proportions, with editable, inspectable
reasons behind every verdict. Full architecture, formulas, and rationale live in
`NOTES.md` — read it before making design decisions; it is the source of truth,
not this file.

As of now this repo is design notes only — no code, no chosen stack, no manifest
files exist yet.

## Standing rules (from NOTES.md)

- **Balance points, not shape categories, drive scoring.** Continuous signed
  numbers (e.g. `bust_hip_balance`, `waist_definition`) are the internal model.
  A shape label (pear/hourglass/apple/rectangle) may be shown to the user as a
  display string, but must never be used in the scoring logic itself.
- **Follow the build order — do not jump ahead to image/CV work:**
  1. Pure-function balance-point calculator, with the 5 worked examples in
     NOTES.md encoded as automated tests. No UI, no images.
  2. `effects.yaml` + scoring function returning `(verdict, reasons[])`.
  3. CLI/notebook to validate the rules feel right on real inputs.
  4. Only then: a parametric SVG avatar (no photorealism).
  5. Only then: garment-photo attribute extraction (pose estimation/segmentation).
  6. Later: multi-garment outfit parsing.
- **Worked examples must be automated tests, not eyeballed.** Rule changes have
  silently regressed prior-correct worked examples before (the "apple + bodycon"
  case in NOTES.md). Once step 1 exists, any change to the balance-point or
  scoring logic must be checked against the full worked-example test suite.
