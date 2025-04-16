from datetime import date, datetime, timedelta, timezone

import pytest

from amoneyplan.common.models import generate_safe_cuid16
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig,
    AccountNotFoundError,
    AccountStateMatchError,
    BucketConfig,
    MoneyPlan,
    MoneyPlanError,
    PlanAccount,
    PlanAlreadyCommittedError,
)


@pytest.fixture
def the_date() -> date:
    return date(2022, 3, 29)


@pytest.fixture
def money_plan(the_date) -> MoneyPlan:
    """Create a new MoneyPlan with default settings."""
    now = datetime.now(timezone.utc)
    today = date.today()
    return MoneyPlan.start_plan(
        id=generate_safe_cuid16(),
        initial_balance=1000,
        created_at=now,
        plan_date=today,
        notes=f"Test plan created on {the_date}",
    )


def test_money_plan_create(money_plan, the_date):
    assert money_plan.id is not None
    assert money_plan.notes == f"Test plan created on {the_date}"
    assert not money_plan.committed


def test_plan_account_default_bucket():
    """Test that an account gets a default bucket if none are provided."""
    plan_account = PlanAccount.create("1")
    assert len(plan_account.buckets) == 1
    default_bucket = next(iter(plan_account.buckets.values()))
    assert default_bucket.name == "Default"
    assert default_bucket.category == "default"
    assert default_bucket.allocated_amount == Money(0)


def test_plan_account_no_default_bucket_when_buckets_provided():
    """Test that an account doesn't get a default bucket if buckets are provided."""
    buckets = [
        {"name": "Savings", "category": "savings", "allocated_amount": 500},
        {"name": "Bills", "category": "expenses", "allocated_amount": 500},
    ]
    plan_account = PlanAccount.create("1", buckets=buckets)
    assert len(plan_account.buckets) == 2
    assert "Savings" in plan_account.buckets
    assert "Bills" in plan_account.buckets


def test_archive_uncommitted_plan(money_plan):
    """Test archiving an uncommitted money plan."""
    assert not money_plan.is_archived
    assert money_plan.archived_at is None

    # Archive the plan
    now = datetime.now(timezone.utc)
    money_plan.archive_plan(now)

    # Verify the plan is now archived
    assert money_plan.is_archived
    assert money_plan.archived_at is not None


def test_archive_committed_plan():
    """Test that a committed plan can be archived."""
    # Create a plan with one account and bucket
    plan = MoneyPlan.start_plan(
        id="1",
        initial_balance=1000,
        created_at=datetime.now(timezone.utc),
        plan_date=date.today(),
        default_allocations=[
            AccountAllocationConfig(
                "1",
                "Test Account",
                buckets=[
                    BucketConfig(
                        name="Savings",
                        category="savings",
                        allocated_amount=Money(1000),
                    )
                ],
            )
        ],
    )

    # Commit the plan
    plan.commit()

    # Archive the plan
    now = datetime.now(timezone.utc)
    plan.archive_plan(now)

    # Verify the plan is archived
    assert plan.is_archived
    assert plan.archived_at == now


def test_archive_already_archived_plan(money_plan):
    """Test that archiving an already archived plan raises an error."""
    # Archive the plan once
    now = datetime.now(timezone.utc)
    money_plan.archive_plan(now)
    assert money_plan.is_archived

    # Try to archive again - should raise an error
    with pytest.raises(MoneyPlanError, match="Plan is already archived"):
        money_plan.archive_plan(now)


def test_cannot_modify_archived_plan(money_plan):
    """Test that an archived plan cannot be modified."""
    # Archive the plan
    now = datetime.now(timezone.utc)
    money_plan.archive_plan(now)

    # Attempts to modify should raise errors
    with pytest.raises(MoneyPlanError, match="Cannot modify an archived plan"):
        money_plan.add_account(generate_safe_cuid16(), "New Account")

    with pytest.raises(MoneyPlanError, match="Cannot modify an archived plan"):
        money_plan.adjust_plan_balance(adjustment=100)


def test_remove_account():
    """Test removing an account from a plan."""
    # Create a plan with two accounts
    plan = MoneyPlan.start_plan(
        id="1",
        initial_balance=1000,
        created_at=datetime.now(timezone.utc),
        plan_date=date.today(),
        default_allocations=[
            AccountAllocationConfig(
                "1",
                "Account 1",
                buckets=[
                    BucketConfig(
                        name="Savings",
                        category="savings",
                        allocated_amount=Money(500),
                    ),
                    BucketConfig(
                        name="Bills",
                        category="expenses",
                        allocated_amount=Money(300),
                    ),
                ],
            ),
            AccountAllocationConfig(
                "2",
                "Account 2",
                buckets=[
                    BucketConfig(
                        name="Default",
                        category="default",
                        allocated_amount=Money(200),
                    ),
                ],
            ),
        ],
    )

    # Remove the first account
    plan.remove_account("1")

    # Check that the account was removed
    assert "1" not in plan.accounts
    assert len(plan.accounts) == 1
    assert plan.remaining_balance == Money(800)  # Initial - Account 2's allocation


def test_cannot_remove_account_from_committed_plan():
    """Test that an account cannot be removed from a committed plan."""
    # Create a plan with one account
    plan = MoneyPlan.start_plan(
        id="1",
        initial_balance=1000,
        created_at=datetime.now(timezone.utc),
        plan_date=date.today(),
        default_allocations=[
            AccountAllocationConfig(
                "1",
                "Test Account",
                buckets=[
                    BucketConfig(
                        name="Savings",
                        category="savings",
                        allocated_amount=Money(1000),
                    ),
                ],
            )
        ],
    )

    # Commit the plan
    plan.commit()

    # Try to remove the account
    with pytest.raises(PlanAlreadyCommittedError):
        plan.remove_account("1")


def test_cannot_remove_nonexistent_account():
    """Test that removing a non-existent account raises an error."""
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan.start_plan(
        id=generate_safe_cuid16(), initial_balance=1000, created_at=now, plan_date=today
    )

    # Try to remove an account with a random id
    nonexistent_id = generate_safe_cuid16()
    with pytest.raises(AccountNotFoundError, match=f"Account with ID {nonexistent_id} not found"):
        plan.remove_account(nonexistent_id)


def test_set_account_checked_state():
    """Test setting the checked state of an account."""
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan.start_plan(
        id=generate_safe_cuid16(), initial_balance=1000, created_at=now, plan_date=today
    )

    # Add account
    account_id = generate_safe_cuid16()
    plan.add_account(account_id, "Test Account")

    # Verify initial state
    assert not plan.accounts[account_id].account.is_checked

    # Set checked state
    plan.set_account_checked_state(account_id, is_checked=True)
    assert plan.accounts[account_id].account.is_checked

    # Repeat previous state setting to ensure we do not generate a duplicate event
    with pytest.raises(AccountStateMatchError, match="Account is already checked"):
        plan.set_account_checked_state(account_id, is_checked=True)
        assert plan.accounts[account_id].account.is_checked

    # Unset checked state again
    plan.set_account_checked_state(account_id, is_checked=False)
    assert not plan.accounts[account_id].account.is_checked

    # Repeat previous state setting to ensure we do not generate a duplicate event
    with pytest.raises(AccountStateMatchError, match="Account is already unchecked"):
        plan.set_account_checked_state(account_id, is_checked=False)
        assert not plan.accounts[account_id].account.is_checked


def test_edit_plan_notes(money_plan):
    """Test editing the notes of a plan."""
    money_plan.edit_plan_notes("New plan notes")
    assert money_plan.notes == "New plan notes"


def test_edit_account_notes(money_plan):
    """Test editing the notes of an account."""
    account_id = generate_safe_cuid16()
    money_plan.add_account(account_id, "Test Account")
    money_plan.edit_account_notes(account_id, "New account notes")
    account = money_plan.accounts[account_id].account
    assert account.notes == "New account notes"


class TestMoneyPlan:
    def test_start_plan_basic(self):
        """Test starting a basic plan with just a balance."""
        created_at = datetime.now(timezone.utc)
        plan_date = date.today()
        plan = MoneyPlan.start_plan(generate_safe_cuid16(), 1000, created_at, plan_date)

        assert plan.initial_balance == Money(1000)
        assert plan.remaining_balance == Money(1000)
        assert not plan.committed
        assert plan.created_at == created_at
        assert plan.plan_date == plan_date

    def test_start_plan_future_date(self):
        """Test starting a plan with a future date."""
        created_at = datetime.now(timezone.utc)
        plan_date = date.today() + timedelta(days=30)  # 30 days in future
        plan = MoneyPlan.start_plan(generate_safe_cuid16(), 1000, created_at, plan_date)

        assert plan.plan_date == plan_date
        assert plan.created_at == created_at
