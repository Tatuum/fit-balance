from dataclasses import dataclass, replace

from .balance_points import WomensBalancePoints
from .garments import GarmentItem, get_item, resolve_outfit
from .schemas import Verdict
from .scoring import score
from .technique_advice import DimensionAdvice, recommend_techniques


@dataclass(frozen=True)
class GarmentBalanceAdvice:
    """One chosen catalog item's own verdict on this body, plus which
    OTHER-slot catalog items would counteract its negative reasons. Distinct
    from two things NOTES.md already documents: it's not the single-item
    *replacement* suggestion ("Garment catalog" section, still deferred) --
    nothing here proposes swapping the chosen item -- and it's not full
    *outfit* recommendation (recommend.py) -- it only ever reasons about the
    one item the user already committed to."""

    item: GarmentItem
    verdict: Verdict
    suggestions: list[DimensionAdvice]


def suggest_balance(balance_points: WomensBalancePoints, item_id: str) -> GarmentBalanceAdvice:
    """Score a single catalog item on this body, then for each axis where
    it scores a negative reason, pull the "seek" (opposite-direction) half
    of recommend_techniques()'s advice for that axis, filtered to items in
    a different slot than the chosen item -- real complementary pieces, not
    a replacement for the item itself.

    Reuses resolve_outfit/score/recommend_techniques unchanged; no new
    scoring or AXIS_RULES logic. An axis recommend_techniques() doesn't
    report (shoulder_hip_balance -- see its DIMENSIONS comment) is silently
    skipped here too, same documented gap, not a bug.
    """
    item = get_item(item_id)
    _, garment = resolve_outfit([item_id])
    verdict = score(balance_points, garment)
    negative_axes = {r.axis for r in verdict.reasons if r.direction == "-"}

    suggestions = []
    for dimension in recommend_techniques(balance_points):
        if dimension.axis not in negative_axes:
            continue
        seek = [
            replace(rec, items=[i for i in rec.items if i.slot != item.slot])
            for rec in dimension.recommendations
            if rec.direction == "+"
        ]
        seek = [rec for rec in seek if rec.items]
        if seek:
            suggestions.append(replace(dimension, recommendations=seek))

    return GarmentBalanceAdvice(item=item, verdict=verdict, suggestions=suggestions)
