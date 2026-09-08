from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from .schemas import GarmentAttributes, Reason
from .scoring import EFFECTS_TABLE

Slot = Literal["top", "bottom", "dress", "outerwear"]

_GARMENTS_PATH = Path(__file__).parent / "garments.yaml"


def load_garments_table() -> dict[str, dict]:
    with _GARMENTS_PATH.open() as f:
        return yaml.safe_load(f)


GARMENTS_TABLE = load_garments_table()


@dataclass(frozen=True)
class GarmentItem:
    """A user-facing catalog entry — id/label/slot are safe to expose over
    the API; techniques is the internal detail that resolve_outfit() and
    attribute_reasons() need but that must never reach an API response
    (see api/main.py's GarmentSummary, which omits it)."""

    id: str
    label: str
    slot: Slot
    techniques: tuple[str, ...]


def _build_catalog(table: dict[str, dict]) -> dict[str, GarmentItem]:
    return {
        item_id: GarmentItem(
            id=item_id,
            label=data["label"],
            slot=data["slot"],
            techniques=tuple(data["techniques"]),
        )
        for item_id, data in table.items()
    }


CATALOG: dict[str, GarmentItem] = _build_catalog(GARMENTS_TABLE)


class UnknownGarmentItemError(ValueError):
    """Raised when a requested item id isn't in the catalog."""


def list_items() -> list[GarmentItem]:
    return list(CATALOG.values())


def get_item(item_id: str) -> GarmentItem:
    try:
        return CATALOG[item_id]
    except KeyError:
        raise UnknownGarmentItemError(item_id) from None


def resolve_outfit(item_ids: list[str]) -> tuple[list[GarmentItem], GarmentAttributes]:
    """Resolve catalog item ids into the selected items and their merged
    GarmentAttributes for scoring.

    Techniques are de-duplicated by exact technique key across items (the
    same literal technique shouldn't count twice just because two garments
    happen to share it) — but two *different* technique keys that happen to
    produce the same effect tag (e.g. vertical_detail and skinny_straight
    both -> reduces_bulk) are NOT deduplicated here; scoring.score() treats
    them as independent contributions. See NOTES.md's "Garment catalog"
    section for why this is a deliberate, tested v1 choice, not an
    oversight.
    """
    items = [get_item(item_id) for item_id in item_ids]
    techniques: list[str] = []
    seen: set[str] = set()
    for item in items:
        for technique in item.techniques:
            if technique not in seen:
                seen.add(technique)
                techniques.append(technique)
    return items, GarmentAttributes(techniques=techniques)


class AttributedReason(BaseModel):
    """A Reason plus which selected item(s) produced it. Attribution
    only — "here's what's working against you" — not a replacement
    suggestion; see NOTES.md."""

    tag: str
    axis: str
    contribution: float
    direction: Literal["+", "-"]
    item_ids: list[str]


def attribute_reasons(reasons: list[Reason], items: list[GarmentItem]) -> list[AttributedReason]:
    """For each Reason, name every selected item with a technique that
    produces that reason's tag. Lists ALL responsible items, not just one —
    honest when two items share a technique, or two different techniques
    happen to produce the same tag, rather than picking one arbitrarily.
    """
    attributed = []
    for reason in reasons:
        item_ids = [
            item.id
            for item in items
            if any(reason.tag in EFFECTS_TABLE.get(t, []) for t in item.techniques)
        ]
        attributed.append(AttributedReason(**reason.model_dump(), item_ids=item_ids))
    return attributed
