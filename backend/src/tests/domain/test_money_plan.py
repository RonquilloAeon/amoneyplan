from datetime import date
from uuid import uuid4

import pytest

from amoneyplan.domain.money_plan import (
    AccountNotFoundError,
    AccountStateMatchError,
    MoneyPlan,
    MoneyPlanError,
    PlanAlreadyCommittedError,
)


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
    new_account_id = uuid4()
    plan.add_account(new_account_id, name="Test Account")

    # Get the account from the plan
    account_id = plan.get_last_added_account_id()
    assert account_id == new_account_id

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
        uuid4(),
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


def test_archive_uncommitted_plan(money_plan):
    """Test archiving an uncommitted money plan."""
    assert not money_plan.is_archived
    assert money_plan.archived_at is None

    # Archive the plan
    money_plan.archive_plan()

    # Verify the plan is now archived
    assert money_plan.is_archived
    assert money_plan.archived_at is not None


def test_archive_committed_plan():
    """Test archiving a committed money plan."""
    # Create a plan with some funds and accounts
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Add an account with a bucket to make the plan committable
    plan.add_account(
        uuid4(),
        name="Test Account",
        buckets=[{"bucket_name": "Savings", "category": "savings", "allocated_amount": 1000}],
    )

    # Commit the plan
    plan.commit_plan()
    assert plan.committed

    # Archive the plan
    plan.archive_plan()

    # Verify the plan is archived
    assert plan.is_archived
    assert plan.archived_at is not None


def test_archive_already_archived_plan(money_plan):
    """Test that archiving an already archived plan raises an error."""
    # Archive the plan once
    money_plan.archive_plan()
    assert money_plan.is_archived

    # Try to archive again - should raise an error
    with pytest.raises(MoneyPlanError, match="Plan is already archived"):
        money_plan.archive_plan()


def test_cannot_modify_archived_plan(money_plan):
    """Test that an archived plan cannot be modified."""
    # Archive the plan
    money_plan.archive_plan()

    # Attempts to modify should raise errors
    with pytest.raises(MoneyPlanError, match="Cannot modify an archived plan"):
        money_plan.add_account(uuid4(), name="New Account")

    with pytest.raises(MoneyPlanError, match="Cannot modify an archived plan"):
        money_plan.adjust_plan_balance(adjustment=100)


def test_remove_account():
    """Test removing an account from a draft plan."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Add account with some funds allocated
    plan.add_account(
        uuid4(),
        name="Test Account",
        buckets=[
            {"bucket_name": "Savings", "category": "savings", "allocated_amount": 500},
            {"bucket_name": "Bills", "category": "expenses", "allocated_amount": 300},
        ],
    )
    account_id = plan.get_last_added_account_id()

    # Verify initial state
    assert len(plan.accounts) == 1
    assert plan.remaining_balance.as_float == 200  # 1000 - 500 - 300
    assert account_id in plan.accounts

    # Remove the account
    plan.remove_account(account_id)

    # Verify account was removed and funds were returned
    assert len(plan.accounts) == 0
    assert account_id not in plan.accounts
    assert plan.remaining_balance.as_float == 1000  # All funds returned


def test_cannot_remove_account_from_committed_plan():
    """Test that we cannot remove accounts from committed plans."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Add account with all funds allocated
    plan.add_account(
        uuid4(),
        name="Test Account",
        buckets=[{"bucket_name": "Savings", "category": "savings", "allocated_amount": 1000}],
    )
    account_id = plan.get_last_added_account_id()

    # Commit the plan
    plan.commit_plan()

    # Try to remove the account - should raise error
    with pytest.raises(PlanAlreadyCommittedError, match="Cannot remove an account from a committed plan"):
        plan.remove_account(account_id)


def test_cannot_remove_nonexistent_account():
    """Test that removing a non-existent account raises an error."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Try to remove an account with a random UUID
    nonexistent_id = uuid4()
    with pytest.raises(AccountNotFoundError, match=f"Account with ID {nonexistent_id} not found"):
        plan.remove_account(nonexistent_id)


def test_set_account_checked_state():
    """Test setting the checked state of an account."""
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000)

    # Add account
    plan.add_account(uuid4(), name="Test Account")
    account_id = plan.get_last_added_account_id()

    # Verify initial state
    assert not plan.accounts[account_id].account.is_checked

    # Set checked state
    plan.set_account_checked_state(account_id, is_checked=True)
    assert plan.accounts[account_id].account.is_checked

    # Repeat previous state setting to ensure we do not generated a duplicate event
    with pytest.raises(AccountStateMatchError, match="Account is already checked"):
        plan.set_account_checked_state(account_id, is_checked=True)
        assert plan.accounts[account_id].account.is_checked

    # Unset checked state again
    plan.set_account_checked_state(account_id, is_checked=False)
    assert not plan.accounts[account_id].account.is_checked

    # Repeat previous state setting to ensure we do not generated a duplicate event
    with pytest.raises(AccountStateMatchError, match="Account is already unchecked"):
        plan.set_account_checked_state(account_id, is_checked=False)
        assert not plan.accounts[account_id].account.is_checked

    # Filter events of type AccountCheckedStateSet and verify count
    checked_state_events = [
        e for e in plan.pending_events if e.__class__.__name__ == "AccountCheckedStateSet"
    ]
    assert len(checked_state_events) == 2
