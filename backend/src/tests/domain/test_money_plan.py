from datetime import date
from uuid import uuid4

import pytest

from amoneyplan.domain.money_plan import MoneyPlan


@pytest.fixture
def the_date() -> date:
    return date(2022, 3, 29)


@pytest.fixture
def money_plan(the_date) -> MoneyPlan:
    """Create a new MoneyPlan with default settings."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=0, notes=f"Test plan created on {the_date}")
    return plan


def test_money_plan_create(money_plan, the_date):
    assert money_plan.id is not None
    assert money_plan.notes == f"Test plan created on {the_date}"
    assert not money_plan.committed


def test_money_plan_create_with_id():
    """Test creating a plan with a specific ID."""
    id = uuid4()
    plan = MoneyPlan()
    plan._id = id  # Set ID directly for testing
    plan.start_plan(initial_balance=0)
    assert plan.id == id
