from dataclasses import dataclass
from typing import Literal

from .balance_points import WomensBalancePoints
from .garments import GarmentItem, list_items
from .scoring import AXIS_RULES, EFFECTS_TABLE, axis_value, signed_level

# The 4 scored dimensions, independent of each other — no cross-axis
# combination or ranking, so none of the raw-magnitude-comparability
# problems a single combined Verdict runs into apply here. shoulder_hip_balance
# and bust_hip_balance aren't listed separately: AXIS_RULES only ever scores
# against the derived top_hip_balance (see scoring.py's axis_value), same
# "Top vs hip" combination BalancePointsChart.tsx already does for display.
DIMENSIONS: tuple[tuple[str, str], ...] = (
    ("waist_definition", "Waist definition"),
    ("top_hip_balance", "Horizontal balance"),
    ("torso_leg_balance", "Vertical proportion"),
    ("frame_scale_dev", "Frame scale"),
)


@dataclass(frozen=True)
class TechniqueExample:
    """One effect tag that would help ("+") or hurt ("-") this specific
    body on one dimension, plus the catalog items that produce it."""

    tag: str
    direction: Literal["+", "-"]
    items: list[GarmentItem]


@dataclass(frozen=True)
class DimensionAdvice:
    """One dimension's independent readout — never combined with the other
    3. `pronounced` is a per-dimension highlight (severity level 2), not a
    cross-dimension ranking: any number of dimensions (including zero) can
    be pronounced for a given body.

    `notable`/`direction` are the axis's own severity level and sign,
    exposed directly rather than left for a caller to infer from whether
    `recommendations` is empty — those aren't the same thing. A notable,
    directional reading can still have an empty `recommendations` list if
    a tag for that direction has no current catalog item behind it — that's
    a catalog gap, not the body being unremarkable on this axis, and callers
    describing "what this body reads like" need the real signal, not the
    coincidence of today's catalog coverage. (adds_volume_top was the
    standing example of this until decision 0012 gave it real items.)
    """

    axis: str
    label: str
    value: float
    notable: bool
    pronounced: bool
    direction: Literal["+", "-"] | None
    recommendations: list[TechniqueExample]


def recommend_techniques(balance_points: WomensBalancePoints) -> list[DimensionAdvice]:
    """For each of the 4 scored dimensions: which effect tags would help or
    hurt this body, and which catalog items use them — independent of any
    specific chosen outfit or combination. Every tag sharing an axis also
    shares that axis's reference (AXIS_RULES), so the severity level only
    needs computing once per dimension; which side a tag lands on is purely
    its weight's sign against that one level. A level of 0 (axis inside its
    deadzone) leaves every tag on that axis empty on both sides — "no
    strong trait" falls out naturally, no special-casing needed."""
    advice = []
    for axis, label in DIMENSIONS:
        value = axis_value(balance_points, axis)
        tags_on_axis = [(tag, rule) for tag, rule in AXIS_RULES.items() if rule.axis == axis]
        level = signed_level(value, tags_on_axis[0][1].reference, axis) if tags_on_axis else 0

        recommendations = []
        for tag, rule in tags_on_axis:
            if rule.weight * level == 0:
                continue
            direction: Literal["+", "-"] = "+" if rule.weight * level > 0 else "-"
            items = [
                item
                for item in list_items()
                if any(tag in EFFECTS_TABLE.get(t, []) for t in item.techniques)
            ]
            if items:
                recommendations.append(TechniqueExample(tag=tag, direction=direction, items=items))

        advice.append(
            DimensionAdvice(
                axis=axis,
                label=label,
                value=value,
                notable=level != 0,
                pronounced=abs(level) == 2,
                direction=("+" if level > 0 else "-") if level != 0 else None,
                recommendations=recommendations,
            )
        )
    return advice
