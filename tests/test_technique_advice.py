"""Tests for the per-dimension technique-recommendation layer
(technique_advice.py). Each dimension is reported independently — no
cross-axis combination, so no docs/decisions/ entry (same precedent as
recommend.py/garments.py's catalog); see NOTES.md's "Technique
recommendations" section.
"""

from fit_balance.balance_points import WomensBalancePoints, compute_womens_balance_points
from fit_balance.technique_advice import recommend_techniques
from tests.fixtures import PEAR_FULLER, RECTANGLE_LONG_TORSO_PETITE


def _advice_by_axis(balance_points):
    return {a.axis: a for a in recommend_techniques(balance_points)}


def test_pear_waist_definition_seeks_belted_and_fitted_avoids_oversized():
    bp = compute_womens_balance_points(PEAR_FULLER)
    advice = _advice_by_axis(bp)["waist_definition"]
    assert advice.notable is True
    assert advice.direction == "+"
    assert advice.pronounced is False

    by_tag = {r.tag: r for r in advice.recommendations}
    assert by_tag["defines_waist"].direction == "+"
    assert {i.id for i in by_tag["defines_waist"].items} == {
        "belted_sheath_dress",
        "belted_blouse",
        "belted_skirt",
        "belted_coat",
    }
    assert by_tag["clings_to_waist"].direction == "+"
    assert {i.id for i in by_tag["clings_to_waist"].items} == {
        "sheath_dress",
        "belted_sheath_dress",
    }
    assert by_tag["hides_waist"].direction == "-"
    assert {i.id for i in by_tag["hides_waist"].items} == {
        "oversized_top",
        "oversized_jacket",
        "bomber_jacket",
    }


def test_pear_horizontal_balance_avoids_added_bottom_volume():
    """adds_volume_top has no current producing technique (decision 0011),
    so only the "avoid" side fires here for this hip-heavy body."""
    bp = compute_womens_balance_points(PEAR_FULLER)
    advice = _advice_by_axis(bp)["top_hip_balance"]
    assert advice.notable is True
    assert advice.direction == "-"
    assert advice.pronounced is False

    by_tag = {r.tag: r for r in advice.recommendations}
    assert "adds_volume_top" not in by_tag
    assert by_tag["adds_volume_bottom"].direction == "-"
    assert {i.id for i in by_tag["adds_volume_bottom"].items} == {
        "wide_leg_high_rise_trousers",
        "wide_leg_low_rise_trousers",
    }


def test_pear_frame_scale_seeks_slimming_avoids_bulk():
    bp = compute_womens_balance_points(PEAR_FULLER)
    advice = _advice_by_axis(bp)["frame_scale_dev"]
    assert advice.pronounced is False

    by_tag = {r.tag: r for r in advice.recommendations}
    assert by_tag["reduces_bulk"].direction == "+"
    assert by_tag["adds_bulk"].direction == "-"
    assert {i.id for i in by_tag["adds_bulk"].items} == {
        "oversized_top",
        "oversized_jacket",
        "bomber_jacket",
    }


def test_pear_oversized_top_is_flagged_avoid_on_two_independent_dimensions():
    """The same item can be flagged consistently across more than one
    independently-computed dimension -- not a combined score, just the
    same real item showing up twice, on its own merits each time."""
    bp = compute_womens_balance_points(PEAR_FULLER)
    advice = _advice_by_axis(bp)

    waist_avoid_items = {
        i.id for r in advice["waist_definition"].recommendations if r.direction == "-" for i in r.items
    }
    frame_avoid_items = {
        i.id for r in advice["frame_scale_dev"].recommendations if r.direction == "-" for i in r.items
    }
    assert "oversized_top" in waist_avoid_items
    assert "oversized_top" in frame_avoid_items


def test_wide_leg_high_rise_trousers_is_a_genuine_seek_avoid_split():
    """A hip-heavy, long-torsoed body: wide_leg_high_rise_trousers' two
    techniques touch two different axes with opposite verdicts for this
    body -- adds_volume_bottom (top_hip_balance) works against an
    already-hip-heavy build, elongates_leg (torso_leg_balance) helps a
    long torso. The same item, genuinely "seek" on one dimension and
    "avoid" on another -- the actual trade-off this feature exists to
    surface, not just the same verdict repeated."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=-0.2,
        bust_hip_balance=-0.2,
        waist_definition=0,
        torso_leg_balance=0.2,
        frame_scale_dev=0,
    )
    advice = _advice_by_axis(bp)

    horizontal = advice["top_hip_balance"].recommendations
    vertical = advice["torso_leg_balance"].recommendations

    horizontal_avoid = {i.id for r in horizontal if r.direction == "-" for i in r.items}
    vertical_seek = {i.id for r in vertical if r.direction == "+" for i in r.items}

    assert "wide_leg_high_rise_trousers" in horizontal_avoid
    assert "wide_leg_high_rise_trousers" in vertical_seek


def test_pear_vertical_proportion_has_no_strong_trait():
    """PEAR_FULLER's torso_leg_balance is exactly 0.0 -- inside the
    deadzone, so every tag on that axis is empty on both sides."""
    bp = compute_womens_balance_points(PEAR_FULLER)
    advice = _advice_by_axis(bp)["torso_leg_balance"]
    assert advice.notable is False
    assert advice.direction is None
    assert advice.recommendations == []
    assert advice.pronounced is False


def test_notable_and_direction_are_driven_by_level_not_by_item_coverage():
    """A broad-shouldered (positive top_hip_balance) body: notable/direction
    must reflect the axis's own level, not merely "recommendations is
    non-empty" -- the "avoid" side here (adds_volume_top) has no current
    catalog item at all (decision 0011), so recommendations only has the
    "seek" side, but the axis itself is still notable and positive."""
    bp = WomensBalancePoints(
        shoulder_hip_balance=0.1,
        bust_hip_balance=0.1,
        waist_definition=0,
        torso_leg_balance=0,
        frame_scale_dev=0,
    )
    advice = _advice_by_axis(bp)["top_hip_balance"]
    assert advice.notable is True
    assert advice.direction == "+"
    assert all(r.direction == "+" for r in advice.recommendations)


def test_rectangle_vertical_proportion_is_pronounced_and_only_dimension():
    """RECTANGLE_LONG_TORSO_PETITE's torso_leg_balance (0.171) clears
    PRONOUNCED_THRESHOLD -- flagged, with no other dimension forced into
    the pick (independent per-dimension flags, not a single ranked winner)."""
    bp = compute_womens_balance_points(RECTANGLE_LONG_TORSO_PETITE)
    advice = _advice_by_axis(bp)
    assert advice["torso_leg_balance"].pronounced is True
    assert advice["waist_definition"].pronounced is False
    assert advice["top_hip_balance"].pronounced is False
    assert advice["frame_scale_dev"].pronounced is False


def test_recommend_techniques_covers_all_four_dimensions():
    bp = compute_womens_balance_points(PEAR_FULLER)
    axes = {a.axis for a in recommend_techniques(bp)}
    assert axes == {"waist_definition", "top_hip_balance", "torso_leg_balance", "frame_scale_dev"}
