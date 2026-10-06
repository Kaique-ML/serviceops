from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    codes: tuple[str, ...]
    policy_version: str = "demo-return-v1"


def evaluate_return(
    *,
    delivered_on: date | None,
    today: date,
    ordered_quantity: int,
    requested_quantity: int,
    reason: str,
    window_days: int = 30,
) -> EligibilityResult:
    """Synthetic demo rule: delivery day through day 30 are inclusive."""
    codes: list[str] = []
    if delivered_on is None:
        codes.append("missing_delivery_date")
    elif (today - delivered_on).days < 0 or (today - delivered_on).days > window_days:
        codes.append("outside_demo_window")
    if requested_quantity <= 0:
        codes.append("quantity_not_positive")
    elif requested_quantity > ordered_quantity:
        codes.append("quantity_exceeds_eligible")
    if reason not in {"wrong_product", "damaged", "quality_issue"}:
        codes.append("reason_not_supported")
    return EligibilityResult(not codes, tuple(codes))
