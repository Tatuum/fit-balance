from dataclasses import dataclass, fields

from .schemas import Measurements, MenswearMeasurements

# Guessed placeholders, not real anthropometric reference data (NOTES.md
# "known gaps") — chosen so avg(...)/height lands near these values for a
# roughly average build. This ratio is unit-invariant (numerator and
# denominator scale together), so it holds regardless of the unit used, as
# long as Measurements/MenswearMeasurements are consistently in centimeters.
# Revisit before trusting frame_scale_dev.
WOMEN_FRAME_SCALE_BASELINE = 0.50
MEN_FRAME_SCALE_BASELINE = 0.45


@dataclass(frozen=True)
class WomensBalancePoints:
    bust_hip_balance: float
    waist_definition: float
    torso_leg_balance: float
    frame_scale_dev: float

    def main_concern(self) -> str:
        """Name of the balance point with the largest absolute magnitude.

        A favorable-sign value (e.g. high waist_definition) is an asset, not
        a concern — callers should check the sign before treating this as a
        problem to fix.
        """
        return max((f.name for f in fields(self)), key=lambda name: abs(getattr(self, name)))


@dataclass(frozen=True)
class MenswearBalancePoints:
    chest_waist_balance: float
    chest_hip_balance: float
    torso_leg_balance: float
    frame_scale_dev: float

    def main_concern(self) -> str:
        return max((f.name for f in fields(self)), key=lambda name: abs(getattr(self, name)))


def compute_womens_balance_points(
    m: Measurements, *, frame_scale_baseline: float = WOMEN_FRAME_SCALE_BASELINE
) -> WomensBalancePoints:
    return WomensBalancePoints(
        bust_hip_balance=(m.bust - m.hip) / max(m.bust, m.hip),
        waist_definition=1 - m.waist / ((m.bust + m.hip) / 2),
        torso_leg_balance=(m.torso - m.leg) / max(m.torso, m.leg),
        frame_scale_dev=(m.bust + m.waist + m.hip) / 3 / m.height - frame_scale_baseline,
    )


def compute_menswear_balance_points(
    m: MenswearMeasurements, *, frame_scale_baseline: float = MEN_FRAME_SCALE_BASELINE
) -> MenswearBalancePoints:
    return MenswearBalancePoints(
        chest_waist_balance=(m.chest - m.waist) / m.chest,
        chest_hip_balance=(m.chest - m.hip) / max(m.chest, m.hip),
        torso_leg_balance=(m.torso - m.leg) / max(m.torso, m.leg),
        frame_scale_dev=(m.chest + m.waist + m.hip) / 3 / m.height - frame_scale_baseline,
    )
