from typing import Literal

from pydantic import BaseModel


class Measurements(BaseModel):
    """Women's v0 measurements, in centimeters."""

    bust: float
    waist: float
    hip: float
    torso: float
    leg: float
    height: float


class MenswearMeasurements(BaseModel):
    """Menswear v0 measurements, in centimeters."""

    chest: float
    waist: float
    hip: float
    torso: float
    leg: float
    height: float


class GarmentAttributes(BaseModel):
    """A garment described by the techniques it uses (keys into effects.yaml)."""

    techniques: list[str]


class Reason(BaseModel):
    """One effect tag's contribution to a Verdict's score.

    direction is "+" when the effect helps (positive contribution) and "-"
    when it works against the wearer's balance points (negative contribution).
    """

    tag: str
    axis: str
    contribution: float
    direction: Literal["+", "-"]


class Verdict(BaseModel):
    recommendation: Literal["recommended", "neutral", "avoid", "strong_avoid"]
    score: float
    reasons: list[Reason]
