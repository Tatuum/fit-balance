"""The 5 worked examples from NOTES.md, now asserting on the full verdict.

This is the point where NOTES.md's "apple + bodycon" regression — a rule
change silently flipping a previously-correct verdict — becomes impossible
to reintroduce unnoticed.
"""

from fit_balance.balance_points import WomensBalancePoints, compute_womens_balance_points
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


def test_example_5_pear_fuller_oversized_skinny_is_neutral_with_tension():
    bp = compute_womens_balance_points(PEAR_FULLER)
    garment = GarmentAttributes(techniques=["oversized_top", "skinny_straight"])
    verdict = score(bp, garment)
    assert verdict.recommendation == "neutral"
    # NOTES.md: "shape wants some added volume on top; frame_scale wants
    # less overall bulk; oversized_top also hides this body's defined
    # waist" — a helping and a hurting reason both appear, and the hurting
    # side (including hiding a real asset) keeps the net from clearing
    # "recommended".
    assert any(r.direction == "+" for r in verdict.reasons)
    assert any(r.direction == "-" for r in verdict.reasons)
    assert any(r.tag == "hides_waist" and r.direction == "-" for r in verdict.reasons)


def test_clings_to_hip_is_a_known_fact_not_yet_scored():
    """NOTES.md known gap: clings_to_hip is too coarse (doesn't distinguish
    hip- from waist/midsection-clinging) to score confidently in v0 — it's
    in effects.yaml but intentionally absent from scoring.AXIS_RULES."""
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    garment = GarmentAttributes(techniques=["sheath_bodycon"])
    verdict = score(bp, garment)
    assert all(r.tag != "clings_to_hip" for r in verdict.reasons)


def test_small_bust_hip_imbalance_is_not_scored_as_an_imbalance():
    """Below the 0.05 deadzone, bust_hip_balance isn't a real imbalance —
    wide_leg (adds_volume_bottom) shouldn't score against or for it."""
    barely_off = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0.03,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    garment = GarmentAttributes(techniques=["wide_leg"])
    verdict = score(barely_off, garment)
    assert verdict.reasons == []
    assert verdict.score == 0


def test_adds_volume_bottom_mirrors_adds_volume_top_with_opposite_sign():
    """adds_volume_bottom (e.g. wide-leg trousers) is weighted opposite to
    adds_volume_top on the same top_hip_balance axis (max of
    shoulder_hip_balance and bust_hip_balance — see scoring.py): bottom
    volume helps balance a top-heavy build and works against an already
    bottom-heavy (pear) one.

    bottom_heavy sets shoulder_hip_balance to -0.2 too, not just
    bust_hip_balance: a neutral shoulder_hip_balance=0 would win the max()
    and mask a hip-heavy bust_hip_balance as "balanced", since a shoulder
    line that already matches hip means the top doesn't uniformly read
    narrow even if the bust alone is smaller than hip."""
    top_heavy = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0.2,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    bottom_heavy = WomensBalancePoints(
        shoulder_hip_balance=-0.2,
        bust_hip_balance=-0.2,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    garment = GarmentAttributes(techniques=["wide_leg"])
    assert score(top_heavy, garment).score > 0
    assert score(bottom_heavy, garment).score < 0


def test_adds_volume_top_works_against_an_already_broad_shoulder():
    """Broad shoulders should flip adds_volume_top negative even though
    bust_hip_balance alone reads as needing top volume: top_hip_balance is
    max(shoulder_hip_balance, bust_hip_balance), so the already-wide
    shoulder — not the narrower bust — decides it. It doesn't just fail to
    recommend oversized_top, it actively counts against it: the shoulder
    line already reads wide, so adding more volume there works against this
    body rather than doing nothing."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.2,
        bust_hip_balance=-0.2,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    garment = GarmentAttributes(techniques=["oversized_top"])
    verdict = score(bp, garment)
    assert any(r.tag == "adds_volume_top" and r.direction == "-" for r in verdict.reasons)


def test_deadzone_boundary_value_counts_as_notable_not_balanced():
    """A deviation exactly at IMBALANCE_DEADZONE (0.05) is not treated as
    balanced -- the boundary is exclusive (`magnitude < deadzone`), matching
    the pre-existing `abs(value) < IMBALANCE_DEADZONE` skip condition this
    replaced. See docs/decisions/0010."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0.05,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    verdict = score(bp, GarmentAttributes(techniques=["wide_leg"]))
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0].contribution == 1


def test_just_under_deadzone_is_still_balanced():
    bp = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0.049,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    verdict = score(bp, GarmentAttributes(techniques=["wide_leg"]))
    assert verdict.reasons == []
    assert verdict.score == 0


def test_pronounced_threshold_boundary_value_is_level_two():
    """A deviation exactly at PRONOUNCED_THRESHOLD (0.15) rounds up to the
    "pronounced" level 2, not level 1 -- the boundary is exclusive
    (`magnitude < PRONOUNCED_THRESHOLD`)."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0,
        waist_definition=0,
        torso_leg_balance=0.15,
        frame_scale_dev=0,
    )
    verdict = score(bp, GarmentAttributes(techniques=["high_rise"]))
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0].contribution == 2


def test_just_under_pronounced_threshold_is_level_one():
    bp = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0,
        waist_definition=0,
        torso_leg_balance=0.149,
        frame_scale_dev=0,
    )
    verdict = score(bp, GarmentAttributes(techniques=["high_rise"]))
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0].contribution == 1


def test_waist_definition_has_no_deadzone_any_deviation_scores():
    """Unlike the four zero-neutral axes, waist_definition gets no deadzone
    -- a deviation from its 0.15 reference as small as 0.01 still scores at
    level 1, matching decision 0007's reasoning (already excluded from the
    deadzone) that this change deliberately preserves rather than reopens."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0,
        bust_hip_balance=0,
        waist_definition=0.16,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    verdict = score(bp, GarmentAttributes(techniques=["belted_natural_waist"]))
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0].contribution == 1


def test_adds_volume_bottom_fires_for_broad_shoulders_even_with_balanced_bust():
    """A broad-shouldered build whose bust happens to match hip still
    benefits from bottom volume — bust_hip_balance alone would miss this
    entirely, since it reads as balanced on its own."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.2,
        bust_hip_balance=0.0,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    garment = GarmentAttributes(techniques=["wide_leg"])
    verdict = score(bp, garment)
    assert any(r.tag == "adds_volume_bottom" and r.direction == "+" for r in verdict.reasons)
