# Decision log

One immutable file per engine-level design decision — never edit an
accepted decision to change its content; if it's later reversed or
refined, write a new decision that supersedes it (and add a one-line
`Status: Superseded by NNNN` note to the old one, nothing more).

`NOTES.md` stays the current-state spec — what the formulas and
architecture are *today*. This log is the history of *why* they got that
way. Start here if you want the current behavior; come here if you want
to know what was tried, rejected, or superseded.

| # | Title | Status |
|---|-------|--------|
| [0001](0001-torso-leg-balance-formula-fix.md) | torso_leg_balance formula fix (deviation-from-own-baseline) | Accepted |
| [0002](0002-shoulder-hip-balance-axis.md) | Add shoulder_hip_balance axis | Accepted |
| [0003](0003-effects-vocabulary-extension.md) | Extend effects vocabulary for new garment catalog items | Accepted |
| [0004](0004-avatar-to-scale-rendering.md) | Avatar renders to-scale from measurements | Superseded in part by 0005 |
| [0005](0005-avatar-curvy-head-width-fix.md) | Avatar curvy silhouette, head, and circumference-to-width fix | Accepted |
| [0006](0006-hides-waist-effect.md) | oversized_top gains hides_waist | Accepted |
| [0007](0007-imbalance-deadzone.md) | Imbalance deadzone for the four zero-neutral axes | Accepted |
| [0008](0008-frame-scale-dev-max-shoulder-bust.md) | frame_scale_dev uses max(shoulder, bust) | Accepted |
| [0009](0009-top-hip-balance-axis.md) | adds_volume_top/bottom scored against top_hip_balance | Accepted |
| [0010](0010-discrete-severity-level-scoring.md) | Discrete severity-level scoring | Accepted |
| [0011](0011-remove-adds-volume-top-from-oversized-top.md) | Remove adds_volume_top from oversized_top | Accepted |
