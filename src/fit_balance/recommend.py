from dataclasses import dataclass

from .balance_points import WomensBalancePoints
from .garments import GarmentItem, list_items, resolve_outfit
from .schemas import Verdict
from .scoring import score


def enumerate_outfit_combinations() -> list[list[str]]:
    """All valid item-id combinations: dress XOR (top + bottom), with
    outerwear optional on either branch. Top-alone, bottom-alone, and
    top+dress/bottom+dress are not valid outfits and are never produced.

    Each returned list feeds straight into garments.resolve_outfit() — the
    same item_ids contract /score-outfit already uses.
    """
    dresses = [item.id for item in list_items() if item.slot == "dress"]
    tops = [item.id for item in list_items() if item.slot == "top"]
    bottoms = [item.id for item in list_items() if item.slot == "bottom"]
    outerwear_options: list[str | None] = [None] + [
        item.id for item in list_items() if item.slot == "outerwear"
    ]

    combos: list[list[str]] = []
    for dress_id in dresses:
        for outer_id in outerwear_options:
            combos.append([dress_id, outer_id] if outer_id else [dress_id])
    for top_id in tops:
        for bottom_id in bottoms:
            for outer_id in outerwear_options:
                ids = [top_id, bottom_id]
                if outer_id:
                    ids.append(outer_id)
                combos.append(ids)
    return combos


@dataclass(frozen=True)
class OutfitRecommendation:
    """One ranked candidate outfit: the resolved items plus its Verdict
    against a fixed set of balance points."""

    items: list[GarmentItem]
    verdict: Verdict


def recommend_outfits(
    balance_points: WomensBalancePoints, limit: int = 5
) -> list[OutfitRecommendation]:
    """Score every valid outfit combination against fixed balance points and
    return the top `limit`, sorted by verdict.score descending.

    Takes balance points rather than raw Measurements so a caller that
    already computed them (e.g. the /recommend-outfits endpoint, which also
    needs main_concern()) doesn't pay for it twice. Reuses resolve_outfit()
    and scoring.score() unchanged — no merge or scoring logic is duplicated
    here, only enumeration + sorting.
    """
    candidates = []
    for item_ids in enumerate_outfit_combinations():
        items, garment = resolve_outfit(item_ids)
        verdict = score(balance_points, garment)
        candidates.append(OutfitRecommendation(items=items, verdict=verdict))
    candidates.sort(key=lambda candidate: candidate.verdict.score, reverse=True)
    return candidates[:limit]
