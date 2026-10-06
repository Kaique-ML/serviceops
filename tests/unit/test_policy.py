from datetime import date, timedelta

from serviceops.domain.policy import evaluate_return


def test_delivery_day_and_day_30_are_inclusive():
    today = date(2026, 1, 31)
    assert evaluate_return(
        delivered_on=today, today=today, ordered_quantity=1, requested_quantity=1, reason="damaged"
    ).eligible
    assert evaluate_return(
        delivered_on=today - timedelta(days=30),
        today=today,
        ordered_quantity=1,
        requested_quantity=1,
        reason="damaged",
    ).eligible


def test_day_31_and_excess_quantity_are_rejected_with_codes():
    result = evaluate_return(
        delivered_on=date(2025, 12, 31),
        today=date(2026, 1, 31),
        ordered_quantity=1,
        requested_quantity=2,
        reason="damaged",
    )
    assert not result.eligible
    assert result.codes == ("outside_demo_window", "quantity_exceeds_eligible")
