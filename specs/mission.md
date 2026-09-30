# fit-balance: Mission

## What it is

fit-balance is an explainable styling-recommendation system. Every
verdict comes with editable, inspectable reasons tied to the user's
own balance points — never a black-box shape label.

## Who it's for

Anyone deciding whether a specific garment works for their own body —
a real styling tool meant for everyday use, not a demo. Single user
for now, no accounts; multi-user later.

## The gap (validated via web search)

- Body-shape apps (Style DNA, BodyMuse, MioLook...) are crowded. User
  reviews consistently complain about vague/inconsistent classification
  and no way to see or override the reasoning.
- Photorealistic virtual try-on (Doppl, TryDrobe, FitRoom, Krea...) is
  also crowded — well-funded, generative, good at "does it look real,"
  bad at "why does/doesn't this suit me."
- Explainable AI (XAI) for fashion is mostly unsolved, per industry
  writing. An arXiv paper (StePO-Rec, 2025) is actively researching
  "knowledge-guided reasoning" for outfit styling — still a research
  problem, not a shipped product feature.
- **The gap: transparent, overridable reasoning.** Not another
  body-shape classifier. Not another photorealistic renderer.

## The one rule that doesn't bend

Continuous, signed balance points (`bust_hip_balance`,
`waist_definition`, etc.) drive scoring — never a shape category
(pear/hourglass/apple/rectangle). A shape label may be shown to the
user as a display string, but it must never enter the scoring logic
itself. Every feature on this roadmap has to respect that.

## Vision

Every "does this suit me" verdict traces back to a specific,
explainable reason — and that reasoning stays inspectable and
correctable by the user, not hidden inside a trained model's opinion.
