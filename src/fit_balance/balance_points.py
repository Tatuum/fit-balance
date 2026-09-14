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

# Below this magnitude, a deviation from 0 is measurement noise, not a real
# proportion difference worth treating as an imbalance — matches the
# "near-balanced" threshold test_balance_points.py's worked-example
# assertions already use (e.g. "abs(...) < 0.05"). Applies only to the four
# axes below where 0 is neutral in both directions; waist_definition has its
# own asymmetric threshold instead (scoring.py's AXIS_RULES reference=0.15)
# and is deliberately left out here — the two aren't the same kind of thing
# (see NOTES.md).
IMBALANCE_DEADZONE = 0.05
DEADZONE_AXES = frozenset(
    {"shoulder_hip_balance", "bust_hip_balance", "torso_leg_balance", "frame_scale_dev"}
)

# Second magnitude-band boundary, used by scoring.py to quantize a raw axis
# deviation into a small severity level (0 = within the deadzone / no
# deadzone, 1 = "notable", 2 = "pronounced") instead of summing raw,
# differently-scaled axis values directly — see docs/decisions/0010. A
# starting proposal verified against all 5 NOTES.md worked examples, not
# derived from external data — same judgment-call category as
# IMBALANCE_DEADZONE and waist_definition's 0.15 reference already are.
PRONOUNCED_THRESHOLD = 0.15


@dataclass(frozen=True)
class WomensBalancePoints:
    # + = shoulder wider than hip (broad-shoulder build), − = hip wider than
    # shoulder. Distinguishes a broad-shoulder/narrow-hip build from a
    # top-heavy-by-bust build that would otherwise look identical on
    # bust_hip_balance alone (NOTES.md "known gaps"). Feeds top_hip_balance
    # (max of this and bust_hip_balance, decision 0009) — structured_shoulder
    # and puff_sleeve (decision 0012) react to it that way — and also has
    # its own dedicated AXIS_RULES entry, narrows_shoulder (decision 0013),
    # for techniques (scoop necklines) that specifically address shoulder
    # width rather than top volume generally.
    shoulder_hip_balance: float
    bust_hip_balance: float
    waist_definition: float
    torso_leg_balance: float
    frame_scale_dev: float

    def _magnitude(self, name: str) -> float:
        value = abs(getattr(self, name))
        if name in DEADZONE_AXES and value < IMBALANCE_DEADZONE:
            return 0.0
        return value

    def main_concern(self) -> str | None:
        """Name of the balance point with the largest absolute magnitude, or
        None if nothing clears the deadzone — a body with no axis reading as
        a real imbalance and no natural waist definition either.

        A favorable-sign value (e.g. high waist_definition) is an asset, not
        a concern — callers should check the sign before treating this as a
        problem to fix.
        """
        name = max((f.name for f in fields(self)), key=self._magnitude)
        return name if self._magnitude(name) > 0 else None


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
        # max(shoulder, bust), not bust alone: bust size is confounded by
        # breast tissue independent of actual frame/width, so it can
        # undercount a broad-shouldered, less-busty build. Whichever of the
        # two is actually wider drives the "how fuller does the top read"
        # signal; falls back to bust only when bust genuinely exceeds
        # shoulder (see NOTES.md).
        frame_scale_dev=(max(m.shoulder, m.bust) + m.waist + m.hip) / 3 / m.height
        - frame_scale_baseline,
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
