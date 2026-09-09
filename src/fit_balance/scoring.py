from dataclasses import dataclass
from pathlib import Path

import yaml

from .balance_points import DEADZONE_AXES, IMBALANCE_DEADZONE, WomensBalancePoints
from .schemas import GarmentAttributes, Reason, Verdict

_EFFECTS_PATH = Path(__file__).parent / "effects.yaml"


def load_effects_table() -> dict[str, list[str]]:
    with _EFFECTS_PATH.open() as f:
        return yaml.safe_load(f)


EFFECTS_TABLE = load_effects_table()


@dataclass(frozen=True)
class _AxisRule:
    axis: str
    weight: float
    reference: float = 0.0


# For each effect tag: which balance-point axis it interacts with, and how.
# contribution = weight * (balance_point_value - reference) — scaled by
# distance from "reference", not a flat category match (NOTES.md "Core
# architecture" #3). reference defaults to 0 (the formula's own neutral
# point); waist_definition's tags use 0.15 instead, since NOTES.md's formula
# comment ("~0/− = no natural cinch") implies the practically meaningful
# cinch threshold sits above literal zero.
#
# A tag present in effects.yaml but absent here is a known fact about the
# technique that isn't wired into scoring yet. clings_to_hip is deliberately
# left out: NOTES.md's "known gaps" flags it as too coarse (it doesn't
# distinguish hip-clinging, fine for most shapes, from waist/midsection-
# clinging, bad for an undefined waist) to score confidently in v0.
AXIS_RULES: dict[str, _AxisRule] = {
    "defines_waist": _AxisRule(axis="waist_definition", weight=1.0, reference=0.15),
    "clings_to_waist": _AxisRule(axis="waist_definition", weight=1.0, reference=0.15),
    # Mirrors defines_waist/clings_to_waist with the opposite sign: a boxy,
    # unshaped silhouette (oversized_top) doesn't just fail to define the
    # waist, it obscures whatever natural definition is already there. Only
    # a real cost once waist_definition clears the same 0.15 "there's
    # something worth showing" threshold those two use — hiding a waist
    # that was never defined to begin with isn't a loss.
    "hides_waist": _AxisRule(axis="waist_definition", weight=-1.0, reference=0.15),
    "elongates_leg": _AxisRule(axis="torso_leg_balance", weight=1.0),
    "shortens_torso": _AxisRule(axis="torso_leg_balance", weight=1.0),
    "elongates_torso": _AxisRule(axis="torso_leg_balance", weight=-1.0),
    "shortens_leg": _AxisRule(axis="torso_leg_balance", weight=-1.0),
    "reduces_bulk": _AxisRule(axis="frame_scale_dev", weight=1.0),
    "adds_bulk": _AxisRule(axis="frame_scale_dev", weight=-1.0),
    "adds_volume_top": _AxisRule(axis="bust_hip_balance", weight=-1.0),
    # Mirrors adds_volume_top with the opposite sign: bottom volume (e.g.
    # wide-leg trousers) helps balance a top-heavy build (positive
    # bust_hip_balance) and works against an already bottom-heavy one.
    "adds_volume_bottom": _AxisRule(axis="bust_hip_balance", weight=1.0),
}

RECOMMENDED_THRESHOLD = 0.1
AVOID_THRESHOLD = -0.1
STRONG_AVOID_THRESHOLD = -0.3


def score(balance_points: WomensBalancePoints, garment: GarmentAttributes) -> Verdict:
    reasons: list[Reason] = []
    for technique in garment.techniques:
        for tag in EFFECTS_TABLE.get(technique, []):
            rule = AXIS_RULES.get(tag)
            if rule is None:
                continue
            value = getattr(balance_points, rule.axis)
            # Same deadzone WomensBalancePoints.main_concern() uses: below
            # it, this axis isn't a real imbalance, so no technique should
            # get credit or blame against it.
            if rule.axis in DEADZONE_AXES and abs(value) < IMBALANCE_DEADZONE:
                continue
            contribution = rule.weight * (value - rule.reference)
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
