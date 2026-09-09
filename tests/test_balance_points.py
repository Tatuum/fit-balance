"""The 5 worked examples from NOTES.md, encoded as regression tests.

The garment + verdict parts of each example are tested separately in
test_scoring.py; this file covers only the balance-point layer.
"""

import pytest

from fit_balance.balance_points import WomensBalancePoints, compute_womens_balance_points
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
    assert bp.main_concern() == "waist_definition"


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
def test_main_concern_is_one_of_the_five_axes(measurements):
    bp = compute_womens_balance_points(measurements)
    assert bp.main_concern() in (
        "shoulder_hip_balance",
        "bust_hip_balance",
        "waist_definition",
        "torso_leg_balance",
        "frame_scale_dev",
    )


def test_main_concern_is_none_for_a_genuinely_balanced_body():
    """All four zero-neutral axes sit inside the 0.05 deadzone, and
    waist_definition is exactly 0 too — nothing here reads as a real
    imbalance or asset."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.02,
        bust_hip_balance=-0.03,
        waist_definition=0.0,
        torso_leg_balance=0.01,
        frame_scale_dev=-0.02,
    )
    assert bp.main_concern() is None


def test_main_concern_ignores_small_deviations_on_the_four_zero_neutral_axes():
    """A deviation just under the deadzone doesn't count as the main
    concern, even if it's the largest magnitude present."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.04,
        bust_hip_balance=0.0,
        waist_definition=0.0,
        torso_leg_balance=0.0,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() is None


def test_main_concern_still_fires_once_a_deviation_clears_the_deadzone():
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.06,
        bust_hip_balance=0.0,
        waist_definition=0.0,
        torso_leg_balance=0.0,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() == "shoulder_hip_balance"


def test_main_concern_leaves_waist_definition_without_a_deadzone():
    """waist_definition has its own asymmetric threshold (scoring.py's
    AXIS_RULES reference=0.15), not this deadzone — even a small nonzero
    value here should still win over axes zeroed out by the deadzone."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.02,
        bust_hip_balance=0.0,
        waist_definition=0.01,
        torso_leg_balance=0.0,
        frame_scale_dev=0.0,
    )
    assert bp.main_concern() == "waist_definition"
