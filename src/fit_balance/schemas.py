from typing import Literal

from pydantic import BaseModel, Field


class Measurements(BaseModel):
    """Women's v0 measurements, in centimeters.

    shoulder: circumference around the fullest part of the shoulders/upper
    arms (the stylist body-shape-calculator convention) — NOT the tailoring
    point-to-point shoulder width (~38-40cm), which is a different scale and
    isn't comparable to bust/hip circumferences.

    Every field is range-checked (inclusive), so a typo or impossible value
    is a 422 at the API instead of a nonsense verdict (or, for height 0, a
    ZeroDivisionError). The bounds are deliberately wide sanity limits chosen
    by the project owner, not survey data: they reject impossible input, not
    unusual bodies. web/src/lib/measurements.ts mirrors them — keep the two
    in sync; this one is the authority.
    """

    shoulder: float = Field(ge=60, le=160)
    bust: float = Field(ge=60, le=180)
    waist: float = Field(ge=40, le=180)
    hip: float = Field(ge=60, le=200)
    torso: float = Field(ge=25, le=60)
    leg: float = Field(ge=50, le=110)
    height: float = Field(ge=120, le=230)


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
