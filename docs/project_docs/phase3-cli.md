# Phase 3 — CLI validation

Lets you type in a set of body measurements and a garment's techniques
and see the verdict, the reasons behind it, and the underlying balance
points printed to a terminal. This is the "confirm the rules feel
right on real inputs" step between the engine (phases 1–2) and any web
or API work.

**Files:** `src/fit_balance/cli.py`

### 1. The `score` command

A single Typer command, `fit-balance score`, installed as the
project's console-script entry point (`fit-balance =
"fit_balance.cli:app"` in `pyproject.toml`). Body measurements are
individual required float options (`--shoulder`, `--bust`, `--waist`,
`--hip`, `--torso`, `--leg`, `--height`, all in cm); garment techniques
are a repeatable option:

```python
technique: list[str] = typer.Option(
    ..., "--technique", "-t",
    help="Garment technique, e.g. sheath_bodycon (repeat for multiple)",
)
```

The command builds a `Measurements` and a `GarmentAttributes` from
those options, then calls the same `compute_womens_balance_points()`
and `score()` the API and web layers call later — no separate
CLI-only logic, so a result seen here is guaranteed to match what
phase 4's API returns for the same inputs.

### 2. Verdict + reasons display

The recommendation prints color-coded by outcome:

```python
_RECOMMENDATION_STYLE = {
    "recommended": "green",
    "neutral": "yellow",
    "avoid": "red",
    "strong_avoid": "bold red",
}
```

Below it, a `rich` table lists every fired `Reason` (effect tag,
balance-point axis, signed contribution), sorted strongest-first by
`score()` itself — the CLI doesn't re-sort. If no effect tagged the
garment fired (all contributions landed in the scoring deadzone, or no
`AXIS_RULES` entry existed for a tag), the table is skipped in favor of
a plain "No scored effects fired for this garment." line, so an empty
table is never mistaken for "still loading."

### 3. Balance-points display and the "main concern" label

A second table prints all five balance-point axes with their signed
values, annotating whichever one `balance_points.main_concern()` picks
out:

```python
if axis_name != main_concern:
    label = axis_name
elif axis_name == "waist_definition" and value >= _WAIST_DEFINITION_ASSET_THRESHOLD:
    label = f"{axis_name} (key asset)"
else:
    label = f"{axis_name} (main concern)"
```

`waist_definition` gets special-cased: a favorable (high) value is
labeled "key asset" rather than "main concern," since `main_concern()`
just picks the largest-magnitude axis and doesn't know that
`waist_definition` is asymmetric (see
`docs/project_docs/phase1-balance-points.md`'s `main_concern()`
section). `_WAIST_DEFINITION_ASSET_THRESHOLD` is
`AXIS_RULES["defines_waist"].reference` imported from `scoring.py`
rather than a second hardcoded constant — the same "is this waist
favorable" threshold `scoring.py`'s `defines_waist`/`clings_to_waist`
rules and the web's `BalancePointsChart.tsx` (`AXIS_META.waist_definition.isBalanced`)
also use.

### Testing / verification

No automated CLI tests. Verification was manual: running `uv run
fit-balance score ...` against each of the 5 CURRENT_STATE.md worked examples
and confirming the printed recommendation and reasons matched what
`tests/test_scoring.py` already asserts — the CLI is a display layer
over `score()`, which the phase 1–2 test suites cover directly.

### Gotchas / open questions

- The original plan (`specs/architecture.md`'s phase 3) also proposed
  an optional Jupyter notebook for interactively tuning `effects.yaml`
  weights. It was never built; the CLI alone has served the
  "confirm rules feel right" validation role so far.
