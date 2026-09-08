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

# torso_leg_balance baselines, in ratio-to-height. Public reference points,
# not a rigorous study (same caveat class as the frame-scale baselines
# above): back waist length ~15.5-16.25in / 39-41cm per ASTM misses sizing
# (~0.245 x a ~163cm average height); inseam ~0.45-0.46 x height per common
# sizing guidance. NOTES.md "known gaps": torso (back waist length) and leg
# (inseam) are anchored at very different landmarks and are NEVER close in
# raw magnitude on a real body (back waist length is structurally about
# half of inseam) — a raw (torso-leg)/max(...) ratio is dominated by that
# structural gap and reads as "long legs" for essentially everyone,
# regardless of actual proportion. Comparing each measurement's deviation
# from its own baseline ratio (mirroring frame_scale_dev's approach) fixes
# that: it reads ~0 for baseline proportions and only diverges when a body
# is actually long/short-torsoed or long/short-legged relative to average.
TORSO_HEIGHT_RATIO_BASELINE = 0.245
LEG_HEIGHT_RATIO_BASELINE = 0.455


@dataclass(frozen=True)
class WomensBalancePoints:
    # + = shoulder wider than hip (broad-shoulder build), − = hip wider than
    # shoulder. Distinguishes a broad-shoulder/narrow-hip build from a
    # top-heavy-by-bust build that would otherwise look identical on
    # bust_hip_balance alone (NOTES.md "known gaps"). Not yet wired into any
    # effects.yaml AXIS_RULES — no v0 garment technique reacts to it, same
    # "known fact, not yet scored" treatment as clings_to_hip in scoring.py.
    shoulder_hip_balance: float
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
    shoulder_hip_balance: float
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
        shoulder_hip_balance=(m.shoulder - m.hip) / max(m.shoulder, m.hip),
        bust_hip_balance=(m.bust - m.hip) / max(m.bust, m.hip),
        waist_definition=1 - m.waist / ((m.bust + m.hip) / 2),
        torso_leg_balance=(
            (m.torso / m.height - TORSO_HEIGHT_RATIO_BASELINE)
            - (m.leg / m.height - LEG_HEIGHT_RATIO_BASELINE)
        ),
        frame_scale_dev=(m.bust + m.waist + m.hip) / 3 / m.height - frame_scale_baseline,
    )


def compute_menswear_balance_points(
    m: MenswearMeasurements, *, frame_scale_baseline: float = MEN_FRAME_SCALE_BASELINE
) -> MenswearBalancePoints:
    return MenswearBalancePoints(
        shoulder_hip_balance=(m.shoulder - m.hip) / max(m.shoulder, m.hip),
        chest_waist_balance=(m.chest - m.waist) / m.chest,
        chest_hip_balance=(m.chest - m.hip) / max(m.chest, m.hip),
        torso_leg_balance=(
            (m.torso / m.height - TORSO_HEIGHT_RATIO_BASELINE)
            - (m.leg / m.height - LEG_HEIGHT_RATIO_BASELINE)
        ),
        frame_scale_dev=(m.chest + m.waist + m.hip) / 3 / m.height - frame_scale_baseline,
    )
