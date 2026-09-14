"""Tests for the outfit-recommendation ranking layer (recommend.py).

Presentation-layer work sitting on top of the untouched scoring engine —
see NOTES.md's "Outfit recommendations" section. These tests pin the
enumeration math (which combinations are valid, how many there are for the
current catalog) and the ranking behavior (sorted, respects limit).
"""

from fit_balance.balance_points import compute_womens_balance_points
from fit_balance.garments import CATALOG
from fit_balance.recommend import enumerate_outfit_combinations, recommend_outfits
from fit_balance.schemas import GarmentAttributes
from fit_balance.scoring import score
from tests.fixtures import HOURGLASS_BALANCED

DRESS_COUNT = sum(1 for item in CATALOG.values() if item.slot == "dress")
TOP_COUNT = sum(1 for item in CATALOG.values() if item.slot == "top")
BOTTOM_COUNT = sum(1 for item in CATALOG.values() if item.slot == "bottom")
OUTERWEAR_COUNT = sum(1 for item in CATALOG.values() if item.slot == "outerwear")
OUTERWEAR_OPTIONS = OUTERWEAR_COUNT + 1  # + "none"


def test_enumerate_outfit_combinations_counts_current_catalog():
    expected = DRESS_COUNT * OUTERWEAR_OPTIONS + TOP_COUNT * BOTTOM_COUNT * OUTERWEAR_OPTIONS
    assert len(enumerate_outfit_combinations()) == expected == 474


def test_enumerate_outfit_combinations_excludes_invalid_shapes():
    for combo in enumerate_outfit_combinations():
        slots = [CATALOG[item_id].slot for item_id in combo]
        has_dress = "dress" in slots
        has_top = "top" in slots
        has_bottom = "bottom" in slots
        outerwear_count = slots.count("outerwear")

        assert outerwear_count <= 1
        if has_dress:
            assert not has_top and not has_bottom
            assert slots.count("dress") == 1
        else:
            assert has_top and has_bottom
            assert slots.count("top") == 1
            assert slots.count("bottom") == 1


def test_recommend_outfits_ranks_descending_by_score():
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    ranked = recommend_outfits(bp, limit=len(enumerate_outfit_combinations()))
    scores = [rec.verdict.score for rec in ranked]
    assert scores == sorted(scores, reverse=True)


def test_recommend_outfits_respects_limit():
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    assert len(recommend_outfits(bp, limit=3)) == 3
    assert len(recommend_outfits(bp, limit=1000)) == 474


def test_recommend_outfits_top_pick_matches_engine_score_for_worked_example_1():
    """Worked example 1 (HOURGLASS_BALANCED): sheath_bodycon +
    belted_natural_waist -> recommended. The top-ranked recommendation's
    score must match scoring.score() computed directly on the best-scoring
    combination's own resolved techniques -- not a hardcoded number, so this
    tracks the engine rather than asserting a specific catalog item."""
    bp = compute_womens_balance_points(HOURGLASS_BALANCED)
    top_pick = recommend_outfits(bp, limit=1)[0]

    techniques: list[str] = []
    for item in top_pick.items:
        for technique in item.techniques:
            if technique not in techniques:
                techniques.append(technique)
    expected_verdict = score(bp, GarmentAttributes(techniques=techniques))

    assert top_pick.verdict.score == expected_verdict.score
    assert top_pick.verdict.recommendation == "recommended"
