from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import yaml

from .balance_points import QuantizedBalancePoints, WomensBalancePoints, quantize
from .schemas import GarmentAttributes, Reason, Verdict

_EFFECTS_PATH = Path(__file__).parent / "effects.yaml"


def load_effects_table() -> dict[str, list[str]]:
    with _EFFECTS_PATH.open() as f:
        return cast(dict[str, list[str]], yaml.safe_load(f))


EFFECTS_TABLE = load_effects_table()


@dataclass(frozen=True)
class _AxisRule:
    axis: str
    weight: int


# For each effect tag: which balance-point axis it interacts with, and how.
# contribution = weight * axis_level(quantized_balance_points, axis) — a
# small integer severity level (see axis_level/quantize_axis below), not a
# flat category match (CURRENT_STATE.md "Core architecture" #3) and not the
# raw, differently-scaled balance-point value either (docs/adr/0010).
# Quantization — including waist_definition's 0.15 reference point, since
# CURRENT_STATE.md's formula comment ("~0/− = no natural cinch") implies the
# practically meaningful cinch threshold sits above literal zero — happens
# once, upstream, in balance_points.quantize() (decision 0015); this table
# only needs each tag's axis and direction.
#
# A tag present in effects.yaml but absent here is a known fact about the
# technique that isn't wired into scoring yet. clings_to_hip is deliberately
# left out: CURRENT_STATE.md's "known gaps" flags it as too coarse (it doesn't
# distinguish hip-clinging, fine for most shapes, from waist/midsection-
# clinging, bad for an undefined waist) to score confidently in v0.
AXIS_RULES: dict[str, _AxisRule] = {
    "defines_waist": _AxisRule(axis="waist_definition", weight=1),
    "clings_to_waist": _AxisRule(axis="waist_definition", weight=1),
    # Mirrors defines_waist/clings_to_waist with the opposite sign: a boxy,
    # unshaped silhouette (oversized_top) doesn't just fail to define the
    # waist, it obscures whatever natural definition is already there. Only
    # a real cost once waist_definition clears the same 0.15 "there's
    # something worth showing" threshold those two use — hiding a waist
    # that was never defined to begin with isn't a loss.
    "hides_waist": _AxisRule(axis="waist_definition", weight=-1),
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
    # Unlike the two rules above, scored directly against shoulder_hip_balance
    # rather than the derived top_hip_balance — a technique that narrows the
    # shoulder line itself (e.g. a scoop neckline) only helps a body whose
    # top-heaviness actually comes from broad shoulders, not one that's
    # top-heavy from a fuller bust with balanced shoulders (those would
    # otherwise look identical through top_hip_balance's max()). Decision
    # 0013 — closes the shoulder_hip_balance gap CURRENT_STATE.md flagged since
    # decision 0002.
    "narrows_shoulder": _AxisRule(axis="shoulder_hip_balance", weight=1),
}

RECOMMENDED_THRESHOLD = 1
AVOID_THRESHOLD = -1
STRONG_AVOID_THRESHOLD = -3

# top_hip_balance isn't a stored WomensBalancePoints field — unlike the
# other axes, adds_volume_top/adds_volume_bottom care about whichever of
# shoulder or bust actually reads wider against hip, not one specific
# measurement, so it's computed on demand from the two real fields instead
# of being a field itself (which would double-count with them for
# main_concern()). quantize-then-max equals max-then-quantize here (decision
# 0015): quantize_axis() is monotonic, and shoulder_hip_balance/
# bust_hip_balance already share the same deadzone/reference treatment, so
# taking the max of their two already-quantized levels (axis_level below)
# gives the identical result scoring always wanted for this derived axis.
_TOP_HIP_BALANCE_AXIS = "top_hip_balance"


def axis_value(balance_points: WomensBalancePoints, axis: str) -> float:
    """The raw, continuous value for one axis — display only (e.g.
    technique_advice.DimensionAdvice.value). Not used for scoring itself;
    see axis_level below for the quantized equivalent score() reads."""
    if axis == _TOP_HIP_BALANCE_AXIS:
        return max(balance_points.shoulder_hip_balance, balance_points.bust_hip_balance)
    return cast(float, getattr(balance_points, axis))


def axis_level(quantized: QuantizedBalancePoints, axis: str) -> int:
    """The quantized severity level for one axis — what score() and
    technique_advice.py actually compare/sum, pre-computed once per body by
    balance_points.quantize() rather than recomputed per effect tag."""
    if axis == _TOP_HIP_BALANCE_AXIS:
        return max(quantized.shoulder_hip_balance, quantized.bust_hip_balance)
    return cast(int, getattr(quantized, axis))


def score(balance_points: WomensBalancePoints, garment: GarmentAttributes) -> Verdict:
    quantized = quantize(balance_points)
    reasons: list[Reason] = []
    for technique in garment.techniques:
        for tag in EFFECTS_TABLE.get(technique, []):
            rule = AXIS_RULES.get(tag)
            if rule is None:
                continue
            contribution = rule.weight * axis_level(quantized, rule.axis)
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

    recommendation: Literal["recommended", "neutral", "avoid", "strong_avoid"]
    if total >= RECOMMENDED_THRESHOLD:
        recommendation = "recommended"
    elif total <= STRONG_AVOID_THRESHOLD:
        recommendation = "strong_avoid"
    elif total <= AVOID_THRESHOLD:
        recommendation = "avoid"
    else:
        recommendation = "neutral"

    return Verdict(recommendation=recommendation, score=total, reasons=reasons)
