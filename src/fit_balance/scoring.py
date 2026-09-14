from dataclasses import dataclass
from pathlib import Path

import yaml

from .balance_points import (
    DEADZONE_AXES,
    IMBALANCE_DEADZONE,
    PRONOUNCED_THRESHOLD,
    WomensBalancePoints,
)
from .schemas import GarmentAttributes, Reason, Verdict

_EFFECTS_PATH = Path(__file__).parent / "effects.yaml"


def load_effects_table() -> dict[str, list[str]]:
    with _EFFECTS_PATH.open() as f:
        return yaml.safe_load(f)


EFFECTS_TABLE = load_effects_table()


@dataclass(frozen=True)
class _AxisRule:
    axis: str
    weight: int
    reference: float = 0.0


# For each effect tag: which balance-point axis it interacts with, and how.
# contribution = weight * signed_level(balance_point_value, reference, axis)
# — a small integer severity level (see signed_level below), not a flat
# category match (NOTES.md "Core architecture" #3) and not the raw,
# differently-scaled balance-point value either (docs/decisions/0010).
# reference defaults to 0 (the formula's own neutral point);
# waist_definition's tags use 0.15 instead, since NOTES.md's formula comment
# ("~0/− = no natural cinch") implies the practically meaningful cinch
# threshold sits above literal zero.
#
# A tag present in effects.yaml but absent here is a known fact about the
# technique that isn't wired into scoring yet. clings_to_hip is deliberately
# left out: NOTES.md's "known gaps" flags it as too coarse (it doesn't
# distinguish hip-clinging, fine for most shapes, from waist/midsection-
# clinging, bad for an undefined waist) to score confidently in v0.
AXIS_RULES: dict[str, _AxisRule] = {
    "defines_waist": _AxisRule(axis="waist_definition", weight=1, reference=0.15),
    "clings_to_waist": _AxisRule(axis="waist_definition", weight=1, reference=0.15),
    # Mirrors defines_waist/clings_to_waist with the opposite sign: a boxy,
    # unshaped silhouette (oversized_top) doesn't just fail to define the
    # waist, it obscures whatever natural definition is already there. Only
    # a real cost once waist_definition clears the same 0.15 "there's
    # something worth showing" threshold those two use — hiding a waist
    # that was never defined to begin with isn't a loss.
    "hides_waist": _AxisRule(axis="waist_definition", weight=-1, reference=0.15),
    "elongates_leg": _AxisRule(axis="torso_leg_balance", weight=1),
    "shortens_torso": _AxisRule(axis="torso_leg_balance", weight=1),
    "elongates_torso": _AxisRule(axis="torso_leg_balance", weight=-1),
    "shortens_leg": _AxisRule(axis="torso_leg_balance", weight=-1),
    "reduces_bulk": _AxisRule(axis="frame_scale_dev", weight=1),
    "adds_bulk": _AxisRule(axis="frame_scale_dev", weight=-1),
    # top_hip_balance, not bust_hip_balance alone: these effects change how
    # wide the top of the silhouette reads, and shoulder width can drive
    # that just as much as bust does — bust_hip_balance alone can't tell a
    # broad-shouldered build from a balanced one (that's the exact
    # distinction shoulder_hip_balance exists for, see balance_points.py),
    # so scoring only against bust would recommend adding top volume onto
    # already-broad shoulders, and miss recommending bottom volume to
    # balance a broad-shouldered/narrow-bust build. See axis_value below.
    #
    # oversized_top lost this tag in decision 0011 (a boxy, uniformly loose
    # cut doesn't specifically widen the top the way structured/padded
    # shoulders would; that's already what adds_bulk models) — left this
    # rule dead until decision 0012 gave it real producers:
    # structured_shoulder and puff_sleeve (see garments.yaml's
    # structured_blazer/puff_sleeve_top).
    "adds_volume_top": _AxisRule(axis="top_hip_balance", weight=-1),
    # Mirrors adds_volume_top with the opposite sign: bottom volume (e.g.
    # wide-leg trousers) helps balance a top-heavy build (positive
    # top_hip_balance) and works against an already bottom-heavy one.
    "adds_volume_bottom": _AxisRule(axis="top_hip_balance", weight=1),
}

RECOMMENDED_THRESHOLD = 1
AVOID_THRESHOLD = -1
STRONG_AVOID_THRESHOLD = -3

# top_hip_balance isn't a stored WomensBalancePoints field — unlike the
# other axes, adds_volume_top/adds_volume_bottom care about whichever of
# shoulder or bust actually reads wider against hip, not one specific
# measurement, so it's computed on demand from the two real fields instead
# of being a field itself (which would double-count with them for
# main_concern()). Same "0 is neutral both ways" shape as shoulder_hip_balance
# and bust_hip_balance, so it gets the same deadzone treatment.
_TOP_HIP_BALANCE_AXIS = "top_hip_balance"
_SCORING_DEADZONE_AXES = DEADZONE_AXES | {_TOP_HIP_BALANCE_AXIS}


def axis_value(balance_points: WomensBalancePoints, axis: str) -> float:
    if axis == _TOP_HIP_BALANCE_AXIS:
        return max(balance_points.shoulder_hip_balance, balance_points.bust_hip_balance)
    return getattr(balance_points, axis)


def signed_level(value: float, reference: float, axis: str) -> int:
    """Quantizes a raw axis deviation into a small severity level — 0
    (within the deadzone, or for axes with none), 1 ("notable"), or 2
    ("pronounced") — sign preserved. Raw, differently-scaled axis values
    aren't safely comparable when summed across axes; a small integer level
    is, by construction (docs/decisions/0010).

    Same deadzone WomensBalancePoints.main_concern() uses for the four
    zero-neutral axes: below it, that axis isn't a real imbalance, so no
    technique should get credit or blame against it. waist_definition isn't
    in _SCORING_DEADZONE_AXES, so it gets no deadzone here either — matches
    decision 0007's reasoning (a favorable-direction threshold, not "0 is
    neutral both ways").
    """
    deviation = value - reference
    deadzone = IMBALANCE_DEADZONE if axis in _SCORING_DEADZONE_AXES else 0.0
    magnitude = abs(deviation)
    level = 0 if magnitude < deadzone else 1 if magnitude < PRONOUNCED_THRESHOLD else 2
    return level if deviation >= 0 else -level


def score(balance_points: WomensBalancePoints, garment: GarmentAttributes) -> Verdict:
    reasons: list[Reason] = []
    for technique in garment.techniques:
        for tag in EFFECTS_TABLE.get(technique, []):
            rule = AXIS_RULES.get(tag)
            if rule is None:
                continue
            value = axis_value(balance_points, rule.axis)
            contribution = rule.weight * signed_level(value, rule.reference, rule.axis)
            if contribution == 0:
                continue
            reasons.append(
                Reason(
                    tag=tag,
                    axis=rule.axis,
                    contribution=contribution,
                    direction="+" if contribution > 0 else "-",
                )
            )

    reasons.sort(key=lambda r: abs(r.contribution), reverse=True)
    total = sum(r.contribution for r in reasons)

    if total >= RECOMMENDED_THRESHOLD:
        recommendation = "recommended"
    elif total <= STRONG_AVOID_THRESHOLD:
        recommendation = "strong_avoid"
    elif total <= AVOID_THRESHOLD:
        recommendation = "avoid"
    else:
        recommendation = "neutral"

    return Verdict(recommendation=recommendation, score=total, reasons=reasons)
