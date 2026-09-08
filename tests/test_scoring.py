"""The 5 worked examples from NOTES.md, now asserting on the full verdict.

This is the point where NOTES.md's "apple + bodycon" regression — a rule
change silently flipping a previously-correct verdict — becomes impossible
to reintroduce unnoticed.
"""

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.schemas import GarmentAttributes
from fit_balance.scoring import score
from tests.fixtures import (
    APPLE_LONG_TORSO,
    HOURGLASS_BALANCED,
    PEAR_FULLER,
    RECTANGLE_LONG_TORSO_PETITE,
)


def test_example_1_hourglass_bodycon_belt_is_recommended():
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    garment = GarmentAttributes(techniques=["sheath_bodycon", "belted_natural_waist"])
    verdict = score(bp, garment)
    assert verdict.recommendation == "recommended"
    assert any(r.tag == "defines_waist" and r.direction == "+" for r in verdict.reasons)


def test_example_2_apple_bodycon_belt_is_avoid():
    bp = compute_womens_balance_points(APPLE_LONG_TORSO)
    garment = GarmentAttributes(techniques=["sheath_bodycon", "belted_natural_waist"])
    verdict = score(bp, garment)
    assert verdict.recommendation == "avoid"


def test_example_3_rectangle_petite_drop_waist_is_strong_avoid():
    bp = compute_womens_balance_points(RECTANGLE_LONG_TORSO_PETITE)
    garment = GarmentAttributes(techniques=["drop_waist"])
    verdict = score(bp, garment)
    assert verdict.recommendation == "strong_avoid"
    assert all(r.direction == "-" for r in verdict.reasons)


def test_example_4_rectangle_petite_empire_vertical_is_recommended():
    bp = compute_womens_balance_points(RECTANGLE_LONG_TORSO_PETITE)
    garment = GarmentAttributes(techniques=["empire_waistline", "vertical_detail"])
    verdict = score(bp, garment)
    assert verdict.recommendation == "recommended"


def test_example_5_pear_fuller_oversized_skinny_is_recommended_with_tension():
    bp = compute_womens_balance_points(PEAR_FULLER)
    garment = GarmentAttributes(techniques=["oversized_top", "skinny_straight"])
    verdict = score(bp, garment)
    assert verdict.recommendation == "recommended"
    # NOTES.md: "shape wants some added volume on top; frame_scale wants
    # less overall bulk — surface both" — both a helping and a hurting
    # reason must appear, not just a net positive score.
    assert any(r.direction == "+" for r in verdict.reasons)
    assert any(r.direction == "-" for r in verdict.reasons)


def test_clings_to_hip_is_a_known_fact_not_yet_scored():
    """NOTES.md known gap: clings_to_hip is too coarse (doesn't distinguish
    hip- from waist/midsection-clinging) to score confidently in v0 — it's
    in effects.yaml but intentionally absent from scoring.AXIS_RULES."""
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    garment = GarmentAttributes(techniques=["sheath_bodycon"])
    verdict = score(bp, garment)
    assert all(r.tag != "clings_to_hip" for r in verdict.reasons)
