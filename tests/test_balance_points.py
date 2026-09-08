"""The 5 worked examples from NOTES.md, encoded as regression tests.

The garment + verdict parts of each example are tested separately in
test_scoring.py; this file covers only the balance-point layer.
"""

import pytest

from fit_balance.balance_points import compute_womens_balance_points
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
