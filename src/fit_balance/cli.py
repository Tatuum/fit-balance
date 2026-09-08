import typer
from rich.console import Console
from rich.table import Table

from .balance_points import compute_womens_balance_points
from .schemas import GarmentAttributes, Measurements
from .scoring import score as score_garment

app = typer.Typer(add_completion=False, help="Validate fit-balance scoring rules on real inputs.")
console = Console()

_RECOMMENDATION_STYLE = {
    "recommended": "green",
    "neutral": "yellow",
    "avoid": "red",
    "strong_avoid": "bold red",
}

_AXES = ("bust_hip_balance", "waist_definition", "torso_leg_balance", "frame_scale_dev")


@app.command()
def score(
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
        bust=bust, waist=waist, hip=hip, torso=torso, leg=leg, height=height
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
        label = f"{axis_name} (main concern)" if axis_name == main_concern else axis_name
        balance_table.add_row(label, f"{value:+.3f}")
    console.print(balance_table)


if __name__ == "__main__":
    app()
