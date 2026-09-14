"""Shared Measurements fixtures for the 5 worked examples in NOTES.md, plus
fixtures for garments-layer decisions (e.g. decision 0012) below them.

NOTES.md expresses each example as a shape/frame label (e.g. "shape≈apple,
torso_leg=long_torso") rather than raw measurements. Each constant below is a
concrete Measurements set (in centimeters) chosen to produce the balance-point
signs implied by that label.

bust/waist/hip/height are round-inch values (the classic "36-27-37" hourglass
stat, etc.) — illustrative, not sourced from an anthropometric survey.
shoulder/torso/leg are picked against researched reference ratios (see
balance_points.py's TORSO_HEIGHT_RATIO_BASELINE/LEG_HEIGHT_RATIO_BASELINE
comment): baseline (~0 torso_leg_balance) for examples with no torso/leg
trait in their label, deliberately pronounced above/below baseline for the
two examples explicitly labeled long_torso — same idealized-archetype
treatment as the bust/waist/hip numbers, not average-person values.
"""

from fit_balance.schemas import Measurements

# Example 1: shape≈hourglass, frame_scale=balanced
# shoulder≈92: near-balanced against bust/hip, consistent with hourglass
# having no shoulder-hip skew. torso/leg at baseline ratio for this height
# (40.5cm / 75.0cm) — hourglass has no torso/leg trait in its label.
HOURGLASS_BALANCED = Measurements(
    shoulder=92.0, bust=91.4, waist=68.6, hip=94.0, torso=40.5, leg=75.0, height=165.1
)

# Example 2: shape≈apple, torso_leg=long_torso
# shoulder≈97: apple carries weight up top (bust/shoulders), so shoulder
# tracks bust rather than hip. torso=47/leg=61: notably above/below this
# height's baseline (39.8/74.0), producing a clear long-torso reading.
APPLE_LONG_TORSO = Measurements(
    shoulder=97.0, bust=96.5, waist=86.4, hip=94.0, torso=47.0, leg=61.0, height=162.6
)

# Examples 3 & 4: shape≈rectangle, torso_leg=long_torso, height=petite
# (NOTES.md pairs the same body with two different garments — same fixture,
# different GarmentAttributes in each test.)
# shoulder≈87: balanced with bust/hip, consistent with rectangle's
# "same all over" proportions. torso=48/leg=54: notably above/below this
# height's baseline (37.3/69.4) — a pronounced long-torso, short-leg build,
# needed for drop_waist to clear the strong_avoid threshold.
RECTANGLE_LONG_TORSO_PETITE = Measurements(
    shoulder=87.0, bust=86.4, waist=81.3, hip=86.4, torso=48.0, leg=54.0, height=152.4
)

# Example 5: shape≈pear, frame_scale=fuller
# shoulder≈89: classic pear — narrower shoulder than hip. torso/leg at
# baseline ratio for this height (39.2cm / 72.8cm) — pear has no torso/leg
# trait in its label.
PEAR_FULLER = Measurements(
    shoulder=89.0, bust=91.4, waist=76.2, hip=106.7, torso=39.2, leg=72.8, height=160.0
)

# Not one of the 5 NOTES.md worked examples above — added for decision
# 0012's test_garments.py case, the first real (non-synthetic) verdict to
# exercise adds_volume_top. shoulder=100/hip=88 gives shoulder_hip_balance
# ≈0.12 (clears the 0.05 deadzone, level 1), while bust=84/hip=88 keeps
# bust_hip_balance ≈ -0.045 (inside the deadzone) — isolates top_hip_balance
# to the shoulder-driven case decision 0002 exists to catch. torso/leg at
# this height's baseline ratio (40.5cm / 75.0cm, same as HOURGLASS_BALANCED)
# and waist=66 keeps frame_scale_dev inside its own deadzone — no other
# axis contributes.
BROAD_SHOULDER_NARROW_HIP = Measurements(
    shoulder=100.0, bust=84.0, waist=66.0, hip=88.0, torso=40.5, leg=75.0, height=165.1
)

# Added for decision 0013's test_garments.py case — the counterpart to
# BROAD_SHOULDER_NARROW_HIP above, deliberately top-heavy for the opposite
# reason. shoulder=88/hip=88 keeps shoulder_hip_balance at exactly 0 (inside
# the deadzone), while bust=105/hip=88 gives bust_hip_balance ≈0.162
# (clears PRONOUNCED_THRESHOLD on its own) — top_hip_balance still reads
# top-heavy via the bust, but shoulder_hip_balance alone reads perfectly
# balanced. Proves narrows_shoulder (shoulder_hip_balance-scored) and
# adds_volume_top (top_hip_balance-scored) diverge on this body exactly as
# decision 0013 intends. torso/leg/waist as in BROAD_SHOULDER_NARROW_HIP,
# keeping torso_leg_balance and frame_scale_dev both inside their deadzones.
BUST_DRIVEN_TOP_HEAVY = Measurements(
    shoulder=88.0, bust=105.0, waist=70.0, hip=88.0, torso=40.5, leg=75.0, height=165.1
)
