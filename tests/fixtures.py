"""Shared Measurements fixtures for the 5 worked examples in NOTES.md.

NOTES.md expresses each example as a shape/frame label (e.g. "shape≈apple,
torso_leg=long_torso") rather than raw measurements. Each constant below is a
concrete Measurements set (in centimeters) chosen to produce the balance-point
signs implied by that label.
"""

from fit_balance.schemas import Measurements

# Example 1: shape≈hourglass, frame_scale=balanced
HOURGLASS_BALANCED = Measurements(
    bust=91.4, waist=68.6, hip=94.0, torso=68.6, leg=68.6, height=165.1
)

# Example 2: shape≈apple, torso_leg=long_torso
APPLE_LONG_TORSO = Measurements(
    bust=96.5, waist=86.4, hip=94.0, torso=76.2, leg=63.5, height=162.6
)

# Examples 3 & 4: shape≈rectangle, torso_leg=long_torso, height=petite
# (NOTES.md pairs the same body with two different garments — same fixture,
# different GarmentAttributes in each test.)
RECTANGLE_LONG_TORSO_PETITE = Measurements(
    bust=86.4, waist=81.3, hip=86.4, torso=66.0, leg=50.8, height=152.4
)

# Example 5: shape≈pear, frame_scale=fuller
PEAR_FULLER = Measurements(bust=91.4, waist=76.2, hip=106.7, torso=63.5, leg=63.5, height=160.0)
