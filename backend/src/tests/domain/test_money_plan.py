from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from amoneyplan.domain.money import Money
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
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(
        initial_balance=0, created_at=now, plan_date=today, notes=f"Test plan created on {the_date}"
    )
    return plan


def test_money_plan_create(money_plan, the_date):
    assert money_plan.id is not None
    assert money_plan.notes == f"Test plan created on {the_date}"
    assert not money_plan.committed


def test_money_plan_create_with_id():
    """Test creating a plan with a specific ID."""
    now = datetime.now(timezone.utc)
    today = date.today()
    id = uuid4()
    plan = MoneyPlan()
    plan._id = id  # Set ID directly for testing
    plan.start_plan(initial_balance=0, created_at=now, plan_date=today)
    assert plan.id == id


def test_account_default_bucket():
    """Test that an account gets a default bucket when created without buckets."""
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

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
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

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
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

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
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

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
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

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
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

    # Try to remove an account with a random UUID
    nonexistent_id = uuid4()
    with pytest.raises(AccountNotFoundError, match=f"Account with ID {nonexistent_id} not found"):
        plan.remove_account(nonexistent_id)


def test_set_account_checked_state():
    """Test setting the checked state of an account."""
    now = datetime.now(timezone.utc)
    today = date.today()
    plan = MoneyPlan()
    plan.start_plan(initial_balance=1000, created_at=now, plan_date=today)

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


def test_edit_plan_notes(money_plan):
    """Test editing the notes of a plan."""
    money_plan.edit_plan_notes("New plan notes")
    assert money_plan.notes == "New plan notes"


def test_edit_account_notes(money_plan):
    """Test editing the notes of an account."""
    account_id = uuid4()
    money_plan.add_account(account_id, name="Test Account")
    money_plan.edit_account_notes(account_id, "New account notes")
    account = money_plan.accounts[account_id].account
    assert account.notes == "New account notes"


class TestMoneyPlan:
    def test_start_plan_basic(self):
        """Test starting a basic plan with just a balance."""
        created_at = datetime.now(timezone.utc)
        plan_date = date.today()
        plan = MoneyPlan()

        plan.start_plan(initial_balance=1000, created_at=created_at, plan_date=plan_date)

        assert plan.initial_balance == Money(1000)
        assert plan.remaining_balance == Money(1000)
        assert not plan.committed
        assert plan.created_at == created_at
        assert plan.plan_date == plan_date

    def test_start_plan_future_date(self):
        """Test starting a plan with a future date."""
        plan = MoneyPlan()
        created_at = datetime.now(timezone.utc)
        plan_date = date.today() + timedelta(days=30)  # 30 days in future

        plan.start_plan(initial_balance=1000, created_at=created_at, plan_date=plan_date)

        assert plan.plan_date == plan_date
        assert plan.created_at == created_at

    def test_upcast_v1_to_v2(self):
        """Test upcasting a v1 plan state to v2 with missing created_at."""
        # Create a v1-style state dictionary without created_at
        event_timestamp = datetime(2025, 3, 1, tzinfo=timezone.utc)
        state = {
            "_created_on": datetime(2025, 3, 1, tzinfo=timezone.utc),
            "initial_balance": {"amount": "1000.00"},
            "remaining_balance": {"amount": "1000.00"},
            "accounts": {},
            "notes": "Test plan",
            "committed": False,
            "is_archived": False,
            "plan_date": date(2025, 3, 1),
            "archived_at": None,
            "__events__": [
                {
                    "timestamp": event_timestamp,
                    "initial_balance": {"amount": "1000.00"},
                    "created_at": event_timestamp,
                    "plan_date": date(2025, 3, 1),
                    "notes": "Test plan",
                }
            ],
        }

        # Apply the upcast
        upcast_state = MoneyPlan.upcast_v1_v2(state)

        assert upcast_state["created_at"] == state["_created_on"]

    def test_upcast_v1_to_v2_no_events(self):
        """Test upcasting a v1 plan state with no events."""
        # Create a v1-style state dictionary without events
        state = {
            "_created_on": datetime(2025, 3, 1, tzinfo=timezone.utc),
            "initial_balance": {"amount": "1000.00"},
            "remaining_balance": {"amount": "1000.00"},
            "accounts": {},
            "notes": "Test plan",
            "committed": False,
            "is_archived": False,
            "plan_date": date(2025, 3, 1),
            "archived_at": None,
        }

        # Apply the upcast
        upcast_state = MoneyPlan.upcast_v1_v2(state)

        # Verify created_at was set to current time
        assert upcast_state["created_at"] is not None
        assert upcast_state["created_at"] == state["_created_on"]

    def test_upcast_v1_to_v2_with_existing_created_at(self):
        """Test upcasting a v1 plan state that already has created_at."""
        existing_time = datetime(2025, 3, 1, tzinfo=timezone.utc)
        state = {
            "initial_balance": {"amount": "1000.00"},
            "remaining_balance": {"amount": "1000.00"},
            "accounts": {},
            "notes": "Test plan",
            "committed": False,
            "is_archived": False,
            "created_at": existing_time,
            "plan_date": date(2025, 3, 1),
            "archived_at": None,
        }

        # Apply the upcast
        upcast_state = MoneyPlan.upcast_v1_v2(state)

        # Verify created_at was not changed
        assert upcast_state["created_at"] == existing_time
