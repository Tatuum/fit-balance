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
from fit_balance.scoring import EFFECTS_TABLE, score
from tests.fixtures import HOURGLASS_BALANCED, PEAR_FULLER


def test_catalog_covers_all_four_slots():
    slots = {item.slot for item in list_items()}
    assert slots == {"top", "bottom", "dress", "outerwear"}


def test_catalog_covers_all_seven_techniques():
    catalog_techniques = {t for item in list_items() for t in item.techniques}
    assert catalog_techniques == set(EFFECTS_TABLE)


def test_resolve_outfit_dedupes_identical_technique_across_items():
    # fitted_top and slim_trousers both use skinny_straight.
    _, garment = resolve_outfit(["fitted_top", "slim_trousers"])
    assert garment.techniques.count("skinny_straight") == 1


def test_resolve_outfit_raises_for_unknown_item_id():
    with pytest.raises(UnknownGarmentItemError):
        resolve_outfit(["not_a_real_item"])


def test_attribution_reuses_worked_example_5():
    """NOTES.md worked example 5: pear + fuller frame, oversized top +
    skinny/straight bottom -> recommended, with both a helping and a
    hurting reason. Same body, same techniques (via catalog items instead
    of raw technique strings), plus attribution pinned to the right item."""
    items, garment = resolve_outfit(["oversized_top", "slim_trousers"])
    assert garment.techniques == ["oversized_top", "skinny_straight"]

    bp = compute_womens_balance_points(PEAR_FULLER)
    verdict = score(bp, garment)
    assert verdict.recommendation == "recommended"

    attributed = attribute_reasons(verdict.reasons, items)
    by_tag = {r.tag: r.item_ids for r in attributed}
    assert by_tag["adds_bulk"] == ["oversized_top"]
    assert by_tag["reduces_bulk"] == ["slim_trousers"]


def test_attribution_lists_both_items_when_tags_overlap():
    """seamed_top (vertical_detail) and slim_trousers (skinny_straight) are
    different techniques that both produce reduces_bulk. score() doesn't
    dedupe reasons by tag, so this deliberately produces TWO reduces_bulk
    reasons, each attributing to both items — see NOTES.md."""
    items, garment = resolve_outfit(["seamed_top", "slim_trousers"])
    assert garment.techniques == ["vertical_detail", "skinny_straight"]

    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    verdict = score(bp, garment)
    reduces_bulk_reasons = [r for r in verdict.reasons if r.tag == "reduces_bulk"]
    assert len(reduces_bulk_reasons) == 2

    attributed = attribute_reasons(verdict.reasons, items)
    for reason in attributed:
        if reason.tag == "reduces_bulk":
            assert set(reason.item_ids) == {"seamed_top", "slim_trousers"}


def test_catalog_has_no_empty_technique_lists():
    assert all(item.techniques for item in CATALOG.values())
