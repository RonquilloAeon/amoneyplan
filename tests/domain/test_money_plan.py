from datetime import date

from amoneyplan.domain.money_plan import MoneyPlan


def test_money_plan_create():
    money_plan = MoneyPlan.create(
        date(2022, 3, 29),
    )

    assert money_plan.id is not None
    assert money_plan.date == date(2022, 3, 29)
