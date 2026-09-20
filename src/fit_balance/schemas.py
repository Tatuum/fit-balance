from typing import Literal

from pydantic import BaseModel


class Measurements(BaseModel):
    """Women's v0 measurements, in centimeters.

    shoulder: circumference around the fullest part of the shoulders/upper
    arms (the stylist body-shape-calculator convention) — NOT the tailoring
    point-to-point shoulder width (~38-40cm), which is a different scale and
    isn't comparable to bust/hip circumferences.
    """

    shoulder: float
    bust: float
    waist: float
    hip: float
    torso: float
    leg: float
    height: float


class MenswearMeasurements(BaseModel):
    """Menswear v0 measurements, in centimeters.

    shoulder: same circumference convention as Measurements.shoulder.
    """

    shoulder: float
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

    contribution is a small discrete severity level (weight * one of
    {-2,-1,0,1,2}), not a raw balance-point value — see
    docs/adr/0010. direction is "+" when the effect helps (positive
    contribution) and "-" when it works against the wearer's balance points
    (negative contribution).
    """

    tag: str
    axis: str
    contribution: int
    direction: Literal["+", "-"]


class Verdict(BaseModel):
    recommendation: Literal["recommended", "neutral", "avoid", "strong_avoid"]
    score: int
    reasons: list[Reason]
