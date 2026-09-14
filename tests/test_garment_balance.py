"""Tests for single-garment balance advice (garment_balance.py).

Presentation layer on top of the untouched scoring engine — reuses
resolve_outfit/score/recommend_techniques unchanged, no new AXIS_RULES
logic. See NOTES.md's "Single-garment balance advice" section and
docs/plans/single-garment-balance-advice.md.
"""

import pytest

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.garment_balance import suggest_balance
from fit_balance.garments import UnknownGarmentItemError
from tests.fixtures import BROAD_SHOULDER_NARROW_HIP, HOURGLASS_BALANCED, PEAR_FULLER


def test_structured_blazer_suggests_bottom_volume_from_other_slots():
    """structured_blazer (outerwear, adds_volume_top) avoids on a broad-
    shouldered body (decision 0012/0013's fixture) -- the one negative axis
    (top_hip_balance) should surface adds_volume_bottom items, none of them
    outerwear (the chosen item's own slot)."""
    bp = compute_womens_balance_points(BROAD_SHOULDER_NARROW_HIP)
    advice = suggest_balance(bp, "structured_blazer")

    assert advice.item.id == "structured_blazer"
    assert advice.verdict.recommendation == "avoid"

    assert len(advice.suggestions) == 1
    dimension = advice.suggestions[0]
    assert dimension.axis == "top_hip_balance"
    assert len(dimension.recommendations) == 1
    rec = dimension.recommendations[0]
    assert rec.tag == "adds_volume_bottom"
    assert rec.direction == "+"
    item_ids = {i.id for i in rec.items}
    assert item_ids  # non-empty
    assert all(i.slot != "outerwear" for i in rec.items)


def test_scoop_neck_on_narrow_shoulder_body_has_no_suggestions():
    """scoop_neck_top (narrows_shoulder, scored against shoulder_hip_balance
    directly, decision 0013) avoids on PEAR_FULLER (shoulder narrower than
    hip). shoulder_hip_balance isn't one of technique_advice's 4 reported
    DIMENSIONS, so this negative reason has no counteracting suggestion --
    proving that documented gap degrades gracefully instead of erroring."""
    bp = compute_womens_balance_points(PEAR_FULLER)
    advice = suggest_balance(bp, "scoop_neck_top")

    assert advice.verdict.recommendation == "avoid"
    assert advice.verdict.reasons[0].axis == "shoulder_hip_balance"
    assert advice.suggestions == []


def test_item_with_no_negative_reasons_has_no_suggestions():
    """sheath_dress (clings_to_waist/clings_to_hip) on HOURGLASS_BALANCED
    scores a positive-only verdict -- nothing to balance."""
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    advice = suggest_balance(bp, "sheath_dress")

    assert all(r.direction == "+" for r in advice.verdict.reasons)
    assert advice.suggestions == []


def test_unknown_item_id_raises():
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    with pytest.raises(UnknownGarmentItemError):
        suggest_balance(bp, "not_a_real_item")
