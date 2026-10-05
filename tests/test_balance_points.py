"""The 5 worked examples from CURRENT_STATE.md, encoded as regression tests.

The garment + verdict parts of each example are tested separately in
test_scoring.py; this file covers only the balance-point layer.
"""

import pytest

from fit_balance.balance_points import (
    WomensBalancePoints,
    compute_womens_balance_points,
    quantize_axis,
)
from fit_balance.schemas import Measurements
from tests.fixtures import (
    APPLE_LONG_TORSO,
    HOURGLASS_BALANCED,
    PEAR_FULLER,
    RECTANGLE_LONG_TORSO_PETITE,
)


def test_hourglass_balanced_frame():
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    assert abs(bp.shoulder_hip_balance) < 0.05, "hourglass: shoulder and hip should be near-balanced"
    assert abs(bp.bust_hip_balance) < 0.05, "hourglass: bust and hip should be near-balanced"
    assert bp.waist_definition > 0.2, "hourglass: waist should read as a defined asset"
    assert abs(bp.torso_leg_balance) < 0.05, "hourglass: torso/leg at baseline, no long/short trait"
    assert abs(bp.frame_scale_dev) < 0.05, "frame_scale=balanced"
    assert bp.main_concern() == ["waist_definition"]


def test_frame_scale_dev_uses_the_wider_of_shoulder_or_bust():
    """A broad-shouldered, less-busty build should read at least as full as
    an equally-broad-busted one with a narrow shoulder — bust alone would
    undercount the former."""
    base = Measurements(
        shoulder=90.0, bust=90.0, waist=70.0, hip=95.0, torso=40.0, leg=75.0, height=165.0
    )
    baseline = compute_womens_balance_points(base)
    broad_shoulder = compute_womens_balance_points(base.model_copy(update={"shoulder": 110.0}))
    narrow_shoulder = compute_womens_balance_points(base.model_copy(update={"shoulder": 70.0}))

    assert broad_shoulder.frame_scale_dev > baseline.frame_scale_dev
    # Shrinking the shoulder below bust shouldn't change anything — bust
    # (still 90.0) is the wider of the two either way.
    assert narrow_shoulder.frame_scale_dev == baseline.frame_scale_dev


def test_apple_long_torso():
    bp = compute_womens_balance_points(APPLE_LONG_TORSO)
    assert bp.waist_definition < 0.15, "apple: little to no natural waist"
    assert bp.torso_leg_balance > 0.1, "torso_leg=long_torso"
    # Decision 0014: main_concern() now compares quantize_axis() levels
    # instead of raw magnitude. Before, torso_leg_balance (0.1239 raw) won
    # outright over waist_definition (0.0929 raw) by sheer raw number, with
    # frame_scale_dev (0.0687 raw) not even close. Quantized, all three
    # land at the same level-1 ("notable") severity -- waist_definition's
    # own 0.15 reference and frame_scale_dev's 0.05 deadzone both bring them
    # up to parity with torso_leg_balance -- a genuine 3-way tie the old
    # raw-magnitude comparison couldn't see, now surfaced instead of masked.
    assert bp.main_concern() == ["waist_definition", "torso_leg_balance", "frame_scale_dev"]


def test_rectangle_long_torso_petite():
    bp = compute_womens_balance_points(RECTANGLE_LONG_TORSO_PETITE)
    assert abs(bp.bust_hip_balance) < 0.05, "rectangle: bust and hip should be near-balanced"
    assert bp.waist_definition < 0.15, "rectangle: little to no natural waist"
    assert bp.torso_leg_balance > 0.1, "torso_leg=long_torso"
    assert bp.frame_scale_dev > 0, "petite height reads fuller for the same measurements"


def test_pear_fuller_frame():
    bp = compute_womens_balance_points(PEAR_FULLER)
    assert bp.shoulder_hip_balance < -0.1, "pear: hip notably wider than shoulder"
    assert bp.bust_hip_balance < -0.1, "pear: hip notably wider than bust"
    assert abs(bp.torso_leg_balance) < 0.05, "pear: torso/leg at baseline, no long/short trait"
    assert bp.frame_scale_dev > 0.05, "frame_scale=fuller"


@pytest.mark.parametrize(
    "measurements",
    [HOURGLASS_BALANCED, APPLE_LONG_TORSO, RECTANGLE_LONG_TORSO_PETITE, PEAR_FULLER],
)
def test_main_concern_is_a_subset_of_the_five_axes(measurements):
    bp = compute_womens_balance_points(measurements)
    assert set(bp.main_concern()) <= {
        "shoulder_hip_balance",
        "bust_hip_balance",
        "waist_definition",
        "torso_leg_balance",
        "frame_scale_dev",
    }


def test_main_concern_is_never_empty_because_waist_definition_has_no_neutral_point():
    """All four zero-neutral axes sit inside the 0.05 deadzone, but
    waist_definition = 0.0 isn't silence — it's a real, pronounced (level
    -2) fact: this body has zero natural waist cinch. Decision 0014:
    main_concern() can no longer return an empty list for a body like this,
    because quantize_axis() can never bring waist_definition down to level
    0, not even at its own 0.15 reference point (see quantize_axis()'s
    docstring) -- there's no "nothing to say" case for this one axis."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.02,
        bust_hip_balance=-0.03,
        waist_definition=0.0,
        torso_leg_balance=0.01,
        frame_scale_dev=-0.02,
    )
    assert bp.main_concern() == ["waist_definition"]


def test_main_concern_ignores_small_deviations_on_the_four_zero_neutral_axes():
    """A deviation just under the deadzone doesn't count as a main concern,
    even though it's the largest raw number present -- shoulder_hip_balance
    (0.04) stays excluded. waist_definition is set to its own 0.15
    reference point, the mildest value it can ever take, specifically to
    show it still surfaces regardless (decision 0014) -- there's no value
    that silences it, so it's the sole result here even though its raw
    deviation from 0.15 is exactly 0."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.04,
        bust_hip_balance=0.0,
        waist_definition=0.15,
        torso_leg_balance=0.0,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() == ["waist_definition"]


def test_main_concern_still_fires_once_a_deviation_clears_the_deadzone():
    """0.06 just clears shoulder_hip_balance's 0.05 deadzone, landing it at
    the same level (1, "notable") waist_definition's own 0.15-reference
    floor always sits at -- so both come back together, a tie by
    construction rather than shoulder_hip_balance winning alone."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.06,
        bust_hip_balance=0.0,
        waist_definition=0.15,
        torso_leg_balance=0.0,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() == ["shoulder_hip_balance", "waist_definition"]


def test_main_concern_leaves_waist_definition_without_a_deadzone():
    """waist_definition has its own asymmetric reference (AXIS_REFERENCE,
    0.15), not this deadzone — even a small nonzero deviation from that
    reference should still win over axes zeroed out by the deadzone."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.02,
        bust_hip_balance=0.0,
        waist_definition=0.01,
        torso_leg_balance=0.0,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() == ["waist_definition"]


def test_main_concern_surfaces_a_genuine_tie():
    """Two axes landing on the same highest cleared severity level (2,
    "pronounced") both come back, instead of one being arbitrarily
    preferred (decision 0014). waist_definition is deliberately set to its
    own 0.15 reference point -- its mildest possible level, 1 -- so it
    doesn't join this tie: level 1 loses to the two axes at level 2."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.2,
        bust_hip_balance=0.0,
        waist_definition=0.15,
        torso_leg_balance=-0.2,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() == ["shoulder_hip_balance", "torso_leg_balance"]


def test_quantize_axis_deadzone_boundary_is_notable_not_balanced():
    """A deviation exactly at IMBALANCE_DEADZONE (0.05) is not treated as
    balanced -- the boundary is exclusive (`magnitude < deadzone`). Mirrors
    decision 0010's original boundary test for this same comparison,
    now at quantize_axis()'s own seam rather than only through score()."""
    assert quantize_axis(0.05, "shoulder_hip_balance") == 1


def test_quantize_axis_just_under_deadzone_is_balanced():
    assert quantize_axis(0.049, "shoulder_hip_balance") == 0


def test_quantize_axis_pronounced_threshold_boundary_is_level_two():
    """A deviation exactly at PRONOUNCED_THRESHOLD (0.15) rounds up to
    level 2, not level 1 -- the boundary is exclusive
    (`magnitude < PRONOUNCED_THRESHOLD`). Mirrors decision 0010's original
    boundary test for this same comparison."""
    assert quantize_axis(0.15, "torso_leg_balance") == 2


def test_quantize_axis_just_under_pronounced_threshold_is_level_one():
    assert quantize_axis(0.149, "torso_leg_balance") == 1


def test_quantize_axis_waist_definition_has_no_deadzone():
    """Unlike the four zero-neutral axes, waist_definition gets no
    deadzone -- a deviation from its 0.15 reference as small as 0.01 still
    scores at level 1. Mirrors decision 0010's original test for this
    property."""
    assert quantize_axis(0.16, "waist_definition") == 1


def test_quantize_axis_waist_definition_at_its_own_reference_is_still_level_one():
    """Even a deviation of exactly 0 isn't level 0 for waist_definition --
    see quantize_axis()'s docstring: this axis has no neutral point at
    all, not even at its own reference (decision 0014)."""
    assert quantize_axis(0.15, "waist_definition") == 1
