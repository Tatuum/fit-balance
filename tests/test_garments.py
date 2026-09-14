"""Tests for the manual garment-item catalog (garments.yaml/garments.py).

This is a presentation layer sitting on top of the untouched scoring
engine — see NOTES.md's "Garment catalog" section. These tests pin the
catalog's shape and the two behaviors that matter for correctness: exact-
technique dedup across items, and the deliberate non-dedup of reasons that
share an effect tag via different techniques.
"""

import pytest

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.garments import (
    CATALOG,
    UnknownGarmentItemError,
    attribute_reasons,
    list_items,
    resolve_outfit,
)
from fit_balance.scoring import AXIS_RULES, EFFECTS_TABLE, score
from tests.fixtures import BROAD_SHOULDER_NARROW_HIP, BUST_DRIVEN_TOP_HEAVY, PEAR_FULLER


def test_catalog_covers_all_four_slots():
    slots = {item.slot for item in list_items()}
    assert slots == {"top", "bottom", "dress", "outerwear"}


def test_catalog_covers_all_known_techniques():
    catalog_techniques = {t for item in list_items() for t in item.techniques}
    assert catalog_techniques == set(EFFECTS_TABLE)


def test_every_axis_rules_tag_has_a_catalog_producer():
    """Every scored effect tag (AXIS_RULES) must have at least one
    technique that produces it (effects.yaml) AND that technique must be
    used by a real catalog item -- otherwise the rule is dead code,
    unreachable through any real garment. This is exactly the gap
    adds_volume_top sat in after decision 0011 removed its only producer,
    until decision 0012 gave it real ones -- this test exists so a future
    technique removal can't silently reopen a gap like that one without a
    test failing.

    Doesn't require both signs of an axis to have a producer (e.g.
    shoulder_hip_balance currently has only narrows_shoulder, no
    "+weight" counterpart, which is a legitimate, deliberate asymmetry,
    not a gap) -- just that every tag that IS in AXIS_RULES is reachable.
    """
    catalog_techniques = {t for item in list_items() for t in item.techniques}
    for tag, rule in AXIS_RULES.items():
        producers = [t for t, tags in EFFECTS_TABLE.items() if tag in tags]
        assert producers, f"{tag!r} (axis={rule.axis}) has no producing technique in effects.yaml"
        assert any(t in catalog_techniques for t in producers), (
            f"{tag!r} (axis={rule.axis}) has producing techniques {producers} but none "
            "are used by any catalog item in garments.yaml"
        )


def test_resolve_outfit_dedupes_identical_technique_across_items():
    # fitted_top and slim_trousers both use skinny_straight.
    _, garment = resolve_outfit(["fitted_top", "slim_trousers"])
    assert garment.techniques.count("skinny_straight") == 1


def test_resolve_outfit_raises_for_unknown_item_id():
    with pytest.raises(UnknownGarmentItemError):
        resolve_outfit(["not_a_real_item"])


def test_attribution_reuses_worked_example_5():
    """NOTES.md worked example 5: pear + fuller frame, oversized top +
    skinny/straight bottom -> avoid, with both a helping and a hurting
    reason (including oversized_top hiding this body's defined waist). Same
    body, same techniques (via catalog items instead of raw technique
    strings), plus attribution pinned to the right item."""
    items, garment = resolve_outfit(["oversized_top", "slim_trousers"])
    assert garment.techniques == ["oversized_top", "skinny_straight"]

    bp = compute_womens_balance_points(PEAR_FULLER)
    verdict = score(bp, garment)
    assert verdict.recommendation == "avoid"

    attributed = attribute_reasons(verdict.reasons, items)
    by_tag = {r.tag: r.item_ids for r in attributed}
    assert by_tag["adds_bulk"] == ["oversized_top"]
    assert by_tag["reduces_bulk"] == ["slim_trousers"]
    assert by_tag["hides_waist"] == ["oversized_top"]


def test_attribution_lists_both_items_when_tags_overlap():
    """seamed_top (vertical_detail) and slim_trousers (skinny_straight) are
    different techniques that both produce reduces_bulk. score() doesn't
    dedupe reasons by tag, so this deliberately produces TWO reduces_bulk
    reasons, each attributing to both items — see NOTES.md.

    Uses PEAR_FULLER rather than HOURGLASS_BALANCED: frame_scale_dev needs
    to actually clear the 0.05 imbalance deadzone for reduces_bulk to score
    at all (HOURGLASS_BALANCED's frame_scale_dev ≈ 0.013 sits inside it)."""
    items, garment = resolve_outfit(["seamed_top", "slim_trousers"])
    assert garment.techniques == ["vertical_detail", "skinny_straight"]

    bp = compute_womens_balance_points(PEAR_FULLER)
    verdict = score(bp, garment)
    reduces_bulk_reasons = [r for r in verdict.reasons if r.tag == "reduces_bulk"]
    assert len(reduces_bulk_reasons) == 2

    attributed = attribute_reasons(verdict.reasons, items)
    for reason in attributed:
        if reason.tag == "reduces_bulk":
            assert set(reason.item_ids) == {"seamed_top", "slim_trousers"}


def test_catalog_has_no_empty_technique_lists():
    assert all(item.techniques for item in CATALOG.values())


def test_wide_leg_and_rise_items_resolve_to_expected_techniques():
    assert CATALOG["wide_leg_high_rise_trousers"].techniques == ("wide_leg", "high_rise")
    assert CATALOG["wide_leg_low_rise_trousers"].techniques == ("wide_leg", "low_rise")
    assert CATALOG["ankle_length_trousers"].techniques == ("cropped_ankle_length",)
    assert CATALOG["bomber_jacket"].techniques == ("oversized_top",)


def test_structured_blazer_fires_adds_volume_top_for_broad_shoulders():
    """Decision 0012: structured_shoulder is the first real technique to
    produce adds_volume_top, wiring up an AXIS_RULES entry that's existed
    since decision 0009 but had no producer since decision 0011 removed
    oversized_top's. A broad-shouldered, narrow-hipped body (shoulder-driven
    top_hip_balance, not bust-driven) should avoid adding more top volume."""
    items, garment = resolve_outfit(["structured_blazer"])
    assert garment.techniques == ["structured_shoulder"]

    bp = compute_womens_balance_points(BROAD_SHOULDER_NARROW_HIP)
    verdict = score(bp, garment)
    assert verdict.recommendation == "avoid"

    attributed = attribute_reasons(verdict.reasons, items)
    by_tag = {r.tag: r.item_ids for r in attributed}
    assert by_tag["adds_volume_top"] == ["structured_blazer"]


def test_scoop_neck_fires_narrows_shoulder_for_broad_shoulders():
    """Decision 0013: scoop_neck is the first technique scored directly
    against shoulder_hip_balance. On the same broad-shouldered body decision
    0012 used for adds_volume_top, narrowing the shoulder line is itself a
    win."""
    _, garment = resolve_outfit(["scoop_neck_top"])
    assert garment.techniques == ["scoop_neck"]

    bp = compute_womens_balance_points(BROAD_SHOULDER_NARROW_HIP)
    verdict = score(bp, garment)
    assert verdict.recommendation == "recommended"


def test_narrows_shoulder_distinguishes_shoulder_from_bust_driven_top_heaviness():
    """The exact distinction top_hip_balance alone can't make: on a body
    that's top-heavy because of a fuller bust with perfectly balanced
    shoulders, scoop_neck (shoulder-specific) has nothing to offer, while
    structured_blazer (adds_volume_top, scored against the bust-inclusive
    top_hip_balance) still correctly reads avoid."""
    bp = compute_womens_balance_points(BUST_DRIVEN_TOP_HEAVY)

    _, scoop_neck_garment = resolve_outfit(["scoop_neck_top"])
    scoop_verdict = score(bp, scoop_neck_garment)
    assert scoop_verdict.reasons == []
    assert scoop_verdict.recommendation == "neutral"

    _, blazer_garment = resolve_outfit(["structured_blazer"])
    blazer_verdict = score(bp, blazer_garment)
    assert blazer_verdict.recommendation == "avoid"
