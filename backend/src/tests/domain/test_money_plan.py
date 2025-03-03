from datetime import date

import pytest

from amoneyplan.domain.account import Account
from amoneyplan.domain.entry import Entry
from amoneyplan.domain.money import Currency, Money
from amoneyplan.domain.money_plan import MoneyPlan


@pytest.fixture
def the_date() -> date:
    return date(2022, 3, 29)


@pytest.fixture
def money_plan(the_date) -> MoneyPlan:
    return MoneyPlan.create(the_date)


def test_money_plan_create(money_plan, the_date):
    assert money_plan.id is not None
    assert money_plan.date == the_date


def test_money_plan_create_with_id(the_date):
    id = MoneyPlan.generate_id()
    money_plan = MoneyPlan.create(the_date, id=id)
    assert money_plan.id == id
    assert money_plan.date == the_date


def test_money_plan_create_with_funds(the_date):
    starting_funds = Money.parse(2500, Currency("USD"))
    entry = Entry.create(
        Account(name="Main Checking Account Balance"),
        Account(name="Main Checking Account A"),
        starting_funds,
    )
    money_plan = MoneyPlan.create_with_funds(the_date, entry)

    assert money_plan.funds_remaining == starting_funds
