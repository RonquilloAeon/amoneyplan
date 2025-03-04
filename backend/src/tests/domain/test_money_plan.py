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


def test_account_default_bucket():
    """Test that an account gets a default bucket when created without buckets."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Add account without specifying buckets
    plan.add_account(name="Test Account")
    account_id = plan.get_last_added_account_id()

    # Get the account from the plan
    account = plan.accounts[account_id].account

    # Verify default bucket was created
    assert len(account.buckets) == 1
    default_bucket = account.buckets.get("Default")
    assert default_bucket is not None
    assert default_bucket.bucket_name == "Default"
    assert default_bucket.category == "default"
    assert default_bucket.allocated_amount.as_float == 0


def test_account_no_default_bucket_when_buckets_provided():
    """Test that an account doesn't get a default bucket when buckets are provided."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Add account with buckets
    plan.add_account(
        name="Test Account",
        buckets=[
            {"bucket_name": "Savings", "category": "savings", "allocated_amount": 500},
            {"bucket_name": "Bills", "category": "expenses", "allocated_amount": 500},
        ],
    )
    account_id = plan.get_last_added_account_id()

    # Get the account from the plan
    account = plan.accounts[account_id].account

    # Verify only provided buckets exist (no default bucket)
    assert len(account.buckets) == 2
    assert "Default" not in account.buckets
    assert "Savings" in account.buckets
    assert "Bills" in account.buckets
