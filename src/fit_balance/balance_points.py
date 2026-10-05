from dataclasses import dataclass, fields

from .schemas import Measurements

# Guessed placeholder, not real anthropometric reference data (CURRENT_STATE.md
# "known gaps") — chosen so avg(...)/height lands near this value for a
# roughly average build. This ratio is unit-invariant (numerator and
# denominator scale together), so it holds regardless of the unit used, as
# long as Measurements is consistently in centimeters. Revisit before
# trusting frame_scale_dev.
WOMEN_FRAME_SCALE_BASELINE = 0.50

# torso_leg_balance baselines, in ratio-to-height. Public reference points,
# not a rigorous study (same caveat class as the frame-scale baselines
# above): back waist length ~15.5-16.25in / 39-41cm per ASTM misses sizing
# (~0.245 x a ~163cm average height); inseam ~0.45-0.46 x height per common
# sizing guidance. CURRENT_STATE.md "known gaps": torso (back waist length) and leg
# (inseam) are anchored at very different landmarks and are NEVER close in
# raw magnitude on a real body (back waist length is structurally about
# half of inseam) — a raw (torso-leg)/max(...) ratio is dominated by that
# structural gap and reads as "long legs" for essentially everyone,
# regardless of actual proportion. Comparing each measurement's deviation
# from its own baseline ratio (mirroring frame_scale_dev's approach) fixes
# that: it reads ~0 for baseline proportions and only diverges when a body
# is actually long/short-torsoed or long/short-legged relative to average.
TORSO_HEIGHT_RATIO_BASELINE = 0.245
LEG_HEIGHT_RATIO_BASELINE = 0.455

# Below this magnitude, a deviation from 0 is measurement noise, not a real
# proportion difference worth treating as an imbalance — matches the
# "near-balanced" threshold test_balance_points.py's worked-example
# assertions already use (e.g. "abs(...) < 0.05"). Applies only to the four
# axes below where 0 is neutral in both directions; waist_definition has its
# own asymmetric threshold instead (AXIS_REFERENCE below, 0.15) and is
# deliberately left out here — the two aren't the same kind of thing (see
# CURRENT_STATE.md).
IMBALANCE_DEADZONE = 0.05
DEADZONE_AXES = frozenset(
    {"shoulder_hip_balance", "bust_hip_balance", "torso_leg_balance", "frame_scale_dev"}
)

# Second magnitude-band boundary, used by quantize_axis() below to quantize
# a raw axis deviation into a small severity level (0 = within the deadzone
# / no deadzone, 1 = "notable", 2 = "pronounced") instead of summing raw,
# differently-scaled axis values directly — see docs/adr/0010. A
# starting proposal verified against all 5 CURRENT_STATE.md worked examples, not
# derived from external data — same judgment-call category as
# IMBALANCE_DEADZONE and waist_definition's 0.15 reference already are.
PRONOUNCED_THRESHOLD = 0.15

# Per-axis reference point quantize_axis() measures deviation from — each
# axis's own "neutral," not always literal 0. waist_definition's
# practically meaningful cinch threshold sits at 0.15, not 0 (CURRENT_STATE.md's
# formula comment, "~0/− = no natural cinch"); every other axis is already
# 0-neutral by construction, so it's left out here and quantize_axis()
# falls back to 0.0. Moved here from scoring.py's AXIS_RULES (decision 0015)
# so quantization happens once, at the source, instead of being recomputed
# per effect tag — see quantize() below.
AXIS_REFERENCE: dict[str, float] = {"waist_definition": 0.15}


def quantize_axis(value: float, axis: str) -> int:
    """Quantizes a raw axis deviation into a small severity level — 0
    (within the deadzone, or for axes with none), 1 ("notable"), or 2
    ("pronounced") — sign preserved. Raw, differently-scaled axis values
    aren't safely comparable (decision 0010); a small integer level is, by
    construction.

    waist_definition has no deadzone (it's not in DEADZONE_AXES, so
    `deadzone` below is 0.0) — matches decision 0007's reasoning (a
    favorable-direction threshold, not "0 is neutral both ways"). Since
    `magnitude` (an absolute value) can never be less than 0.0, this means
    waist_definition can never quantize to level 0, not even exactly at its
    own reference point: every possible value reads as either some degree
    of defined-waist asset or some degree of undefined-waist concern, with
    no neutral middle. That's a deliberate property of this one axis, not
    a bug — see decision 0015.
    """
    reference = AXIS_REFERENCE.get(axis, 0.0)
    deviation = value - reference
    deadzone = IMBALANCE_DEADZONE if axis in DEADZONE_AXES else 0.0
    magnitude = abs(deviation)
    level = 0 if magnitude < deadzone else 1 if magnitude < PRONOUNCED_THRESHOLD else 2
    return level if deviation >= 0 else -level


@dataclass(frozen=True)
class WomensBalancePoints:
    # + = shoulder wider than hip (broad-shoulder build), − = hip wider than
    # shoulder. Distinguishes a broad-shoulder/narrow-hip build from a
    # top-heavy-by-bust build that would otherwise look identical on
    # bust_hip_balance alone (CURRENT_STATE.md "known gaps"). Feeds top_hip_balance
    # (max of this and bust_hip_balance, decision 0009) — structured_shoulder
    # and puff_sleeve (decision 0012) react to it that way — and also has
    # its own dedicated AXIS_RULES entry, narrows_shoulder (decision 0013),
    # for techniques (scoop necklines) that specifically address shoulder
    # width rather than top volume generally.
    shoulder_hip_balance: float
    bust_hip_balance: float
    waist_definition: float
    torso_leg_balance: float
    frame_scale_dev: float

    def main_concern(self) -> list[str]:
        """Every balance point sharing the single highest cleared severity
        level (quantize_axis() above) — empty if nothing clears, one name
        for a clear winner, two or more on a genuine tie. Decision 0015:
        ties are surfaced rather than broken, since picking one via raw
        magnitude had the same cross-axis comparability problem decision
        0010 fixed for scoring (comparing differently-scaled raw floats
        directly isn't meaningful — quantize_axis()'s discrete levels are).

        waist_definition can never contribute a level of exactly 0 (see
        quantize_axis()'s docstring), so this can only be empty when every
        *other* axis is also silent — the four zero-neutral axes inside
        their deadzone — while waist_definition itself sits at its own
        mildest possible level, ±1. In practice this means the result is
        essentially never empty for a real body; waist_definition always
        has something to say.

        A favorable-sign name (e.g. a high waist_definition) is an asset,
        not a concern — callers should check that axis's sign before
        treating a returned name as a problem to fix.
        """
        levels = quantize(self)
        magnitudes = {f.name: abs(getattr(levels, f.name)) for f in fields(levels)}
        peak = max(magnitudes.values())
        if peak == 0:
            return []
        return [name for name, magnitude in magnitudes.items() if magnitude == peak]


@dataclass(frozen=True)
class QuantizedBalancePoints:
    """WomensBalancePoints' five axes, each reduced to quantize_axis()'s
    discrete severity level. The shared comparison basis for main_concern()
    above and scoring.py's axis-rule lookups, so both compare the same
    discrete levels instead of main_concern() comparing raw, differently-
    scaled magnitudes directly — see decision 0015."""

    shoulder_hip_balance: int
    bust_hip_balance: int
    waist_definition: int
    torso_leg_balance: int
    frame_scale_dev: int


def quantize(balance_points: WomensBalancePoints) -> QuantizedBalancePoints:
    return QuantizedBalancePoints(
        **{
            f.name: quantize_axis(getattr(balance_points, f.name), f.name)
            for f in fields(balance_points)
        }
    )


def compute_womens_balance_points(
    m: Measurements, *, frame_scale_baseline: float = WOMEN_FRAME_SCALE_BASELINE
) -> WomensBalancePoints:
    return WomensBalancePoints(
        shoulder_hip_balance=(m.shoulder - m.hip) / max(m.shoulder, m.hip),
        bust_hip_balance=(m.bust - m.hip) / max(m.bust, m.hip),
        waist_definition=1 - m.waist / ((m.bust + m.hip) / 2),
        torso_leg_balance=(
            (m.torso / m.height - TORSO_HEIGHT_RATIO_BASELINE)
            - (m.leg / m.height - LEG_HEIGHT_RATIO_BASELINE)
        ),
        # max(shoulder, bust), not bust alone: bust size is confounded by
        # breast tissue independent of actual frame/width, so it can
        # undercount a broad-shouldered, less-busty build. Whichever of the
        # two is actually wider drives the "how fuller does the top read"
        # signal; falls back to bust only when bust genuinely exceeds
        # shoulder (see CURRENT_STATE.md).
        frame_scale_dev=(max(m.shoulder, m.bust) + m.waist + m.hip) / 3 / m.height
        - frame_scale_baseline,
    )
