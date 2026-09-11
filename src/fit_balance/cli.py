import typer
from rich.console import Console
from rich.table import Table

from .balance_points import compute_womens_balance_points
from .schemas import GarmentAttributes, Measurements
from .scoring import AXIS_RULES
from .scoring import score as score_garment

# Same "is this waist_definition value actually favorable" threshold
# AXIS_RULES's defines_waist/clings_to_waist rules and BalancePointsChart.tsx's
# AXIS_META.waist_definition.isBalanced use — reused here rather than
# duplicated, since cli.py and scoring.py are both Python.
_WAIST_DEFINITION_ASSET_THRESHOLD = AXIS_RULES["defines_waist"].reference

app = typer.Typer(add_completion=False, help="Validate fit-balance scoring rules on real inputs.")
console = Console()

_RECOMMENDATION_STYLE = {
    "recommended": "green",
    "neutral": "yellow",
    "avoid": "red",
    "strong_avoid": "bold red",
}

_AXES = (
    "shoulder_hip_balance",
    "bust_hip_balance",
    "waist_definition",
    "torso_leg_balance",
    "frame_scale_dev",
)


@app.command()
def score(
    shoulder: float = typer.Option(
        ..., help="Shoulder circumference (around fullest point of shoulders/upper arms), cm"
    ),
    bust: float = typer.Option(..., help="Bust circumference, cm"),
    waist: float = typer.Option(..., help="Waist circumference, cm"),
    hip: float = typer.Option(..., help="Hip circumference, cm"),
    torso: float = typer.Option(..., help="Torso length, cm"),
    leg: float = typer.Option(..., help="Leg length, cm"),
    height: float = typer.Option(..., help="Height, cm"),
    technique: list[str] = typer.Option(
        ...,
        "--technique",
        "-t",
        help="Garment technique, e.g. sheath_bodycon (repeat for multiple)",
    ),
) -> None:
    """Score a garment's techniques against a set of body measurements."""
    measurements = Measurements(
        shoulder=shoulder, bust=bust, waist=waist, hip=hip, torso=torso, leg=leg, height=height
    )
    garment = GarmentAttributes(techniques=technique)

    balance_points = compute_womens_balance_points(measurements)
    verdict = score_garment(balance_points, garment)

    style = _RECOMMENDATION_STYLE.get(verdict.recommendation, "white")
    console.print(
        f"[{style}]{verdict.recommendation.upper().replace('_', ' ')}[/{style}] "
        f"(score: {verdict.score:+.3f})"
    )

    if verdict.reasons:
        reasons_table = Table(show_header=True, header_style="bold")
        reasons_table.add_column("Effect")
        reasons_table.add_column("Balance point")
        reasons_table.add_column("Contribution", justify="right")
        for reason in verdict.reasons:
            sign_style = "green" if reason.direction == "+" else "red"
            reasons_table.add_row(
                reason.tag,
                reason.axis,
                f"[{sign_style}]{reason.direction}{abs(reason.contribution):.3f}[/{sign_style}]",
            )
        console.print(reasons_table)
    else:
        console.print("[dim]No scored effects fired for this garment.[/dim]")

    balance_table = Table(show_header=True, header_style="bold", title="Balance points")
    balance_table.add_column("Axis")
    balance_table.add_column("Value", justify="right")
    main_concern = balance_points.main_concern()
    for axis_name in _AXES:
        value = getattr(balance_points, axis_name)
        if axis_name != main_concern:
            label = axis_name
        elif axis_name == "waist_definition" and value >= _WAIST_DEFINITION_ASSET_THRESHOLD:
            # A favorable waist_definition is an asset, not a concern — see
            # WomensBalancePoints.main_concern()'s docstring.
            label = f"{axis_name} (key asset)"
        else:
            label = f"{axis_name} (main concern)"
        balance_table.add_row(label, f"{value:+.3f}")
    console.print(balance_table)


if __name__ == "__main__":
    app()
