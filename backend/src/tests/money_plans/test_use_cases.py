import pytest

from amoneyplan.accounts.tenancy import set_current_account
from amoneyplan.accounts.use_cases import AccountUseCases, RegisterAccountData
from amoneyplan.common.time import get_utc_now
from amoneyplan.common.use_cases import UseCaseResult
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountStateMatchError,
    BucketNotFoundError,
    InsufficientFundsError,
    InvalidPlanStateError,
    PlanAlreadyCommittedError,
)
from amoneyplan.money_plans.use_cases import (
    AccountNotFoundError,
    BucketConfig,
    MoneyPlanError,
    MoneyPlanUseCases,
)
from amoneyplan.money_plans.use_cases import (
    AccountUseCases as MoneyPlanAccountUseCases,
)


@pytest.mark.django_db(transaction=True)
class TestMoneyPlanUseCases:
    def setup_method(self):
        """Set up test cases."""
        self.use_case: MoneyPlanUseCases = MoneyPlanUseCases()
        # Create and set a test account for tenancy
        account_use_case = AccountUseCases()

        result = account_use_case.register_account(
            RegisterAccountData(username="testuser", email="testuser@example.com", password="testpass")
        )
        assert result.success
        user, account = result.data if result.data else (None, None)

        self.test_user = user
        self.test_account = account
        set_current_account(account)

    def test_get_plan_not_found(self):
        """Test getting a non-existent plan."""
        result: UseCaseResult = self.use_case.get_plan("non_existent_id")

        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_get_current_plan_none(self):
        """Test getting current plan when none exists."""
        result: UseCaseResult = self.use_case.get_current_plan()

        assert result.success
        assert result.data is None
        assert result.message == "No current plan found"

    def test_add_account_plan_not_found(self):
        """Test adding account to non-existent plan."""
        result: UseCaseResult = self.use_case.add_account("non_existent_id", "test_account", [], "")
        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_add_account_account_not_found(self):
        """Test adding non-existent account to plan."""
        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Try to add non-existent account
        result: UseCaseResult = self.use_case.add_account(plan_id, "non_existent_account", [], "")
        assert not result.success
        assert isinstance(result.error, AccountNotFoundError)
        assert "does not exist" in str(result.error)

    def test_remove_account_plan_not_found(self):
        """Test removing account from non-existent plan."""
        result: UseCaseResult[None] = self.use_case.remove_account("non_existent_id", "test_account")
        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_allocate_funds_plan_not_found(self):
        """Test allocating funds to non-existent plan."""
        result: UseCaseResult[None] = self.use_case.allocate_funds(
            "non_existent_id", "test_account", "test_bucket", 100
        )

        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_allocate_funds_insufficient_funds(self):
        """Test allocating more funds than available."""

        # Create a test account
        account_use_case = MoneyPlanAccountUseCases()
        account_result = account_use_case.create_account("Test account", notes="Test account notes")
        account_id = account_result.data.id

        # Create a real plan first
        plan_result: UseCaseResult = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Add the account to the plan
        add_account_result = self.use_case.add_account(
            plan_id,
            account_id,
            [BucketConfig(name="Test bucket", category="Test category", allocated_amount=Money(1000))],
            "",
        )
        assert add_account_result.success

        # Try to allocate more than available
        result: UseCaseResult[None] = self.use_case.allocate_funds(plan_id, account_id, "Test bucket", 100)

        assert not result.success
        assert isinstance(result.error, InsufficientFundsError)

    def test_allocate_funds_bucket_not_found(self):
        """Test allocating funds to non-existent bucket."""
        # Create a test account
        account_use_case = MoneyPlanAccountUseCases()
        account_result = account_use_case.create_account("Test account", notes="Test account notes")
        account_id = account_result.data.id

        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Add the account to the plan
        add_account_result = self.use_case.add_account(
            plan_id,
            account_id,
            [BucketConfig(name="Test bucket", category="Test category", allocated_amount=Money(1000))],
            "",
        )

        assert add_account_result.success

        # Try to allocate to non-existent bucket
        result: UseCaseResult[None] = self.use_case.allocate_funds(
            plan_id, account_id, "non_existent_bucket", 100
        )

        assert not result.success
        assert isinstance(result.error, BucketNotFoundError)
        assert "not found in the account" in str(result.error)

    def test_adjust_plan_balance_plan_not_found(self):
        """Test adjusting balance of non-existent plan."""
        result: UseCaseResult[None] = self.use_case.adjust_plan_balance("non_existent_id", 100)

        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_commit_plan_already_committed(self):
        """Test committing an already committed plan."""
        # Create a test account
        account_use_case = MoneyPlanAccountUseCases()
        account_result = account_use_case.create_account("Test account", notes="Test account notes")
        assert account_result.success
        account_id = account_result.data.id

        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Add the account to the plan
        add_account_result = self.use_case.add_account(
            plan_id,
            account_id,
            [BucketConfig(name="Test bucket", category="Test category", allocated_amount=Money(1000))],
            "",
        )

        assert add_account_result.success

        # Commit the plan
        commit_result: UseCaseResult[None] = self.use_case.commit_plan(plan_id)
        assert commit_result.success

        # Try to commit again
        result: UseCaseResult[None] = self.use_case.commit_plan(plan_id)

        assert not result.success
        assert isinstance(result.error, PlanAlreadyCommittedError)

    def test_commit_plan_invalid_state(self):
        """Test committing a plan in invalid state."""
        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Try to commit without allocating all funds
        result: UseCaseResult[None] = self.use_case.commit_plan(plan_id)

        assert not result.success
        assert isinstance(result.error, InvalidPlanStateError)
        assert "Plan must have at least one account" in str(result.error)

    def test_set_account_checked_state_already_matches(self):
        """Test setting account checked state when it already matches."""
        # Create a test account
        account_use_case = MoneyPlanAccountUseCases()
        account_result = account_use_case.create_account("Test account", notes="Test account notes")
        assert account_result.success
        account_id = account_result.data.id

        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Add a test account to the plan
        plan = self.use_case.get_plan(plan_id)

        assert plan.success
        assert plan.data is not None
        assert plan.data.id == plan_id

        add_account_result = self.use_case.add_account(plan_id, account_id, [], "")

        assert add_account_result.success

        # Set checked state to True
        result: UseCaseResult[None] = self.use_case.set_account_checked_state(plan_id, account_id, True)
        assert result.success

        # Try to set the same state again
        result: UseCaseResult[None] = self.use_case.set_account_checked_state(plan_id, account_id, True)

        assert not result.success
        assert isinstance(result.error, AccountStateMatchError)
        assert str(result.error) == "Account is already checked"

    def test_archive_plan_already_archived(self):
        """Test archiving an already archived plan."""
        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Archive the plan
        archive_result: UseCaseResult[None] = self.use_case.archive_plan(plan_id)
        assert archive_result.success

        # Try to archive again
        result: UseCaseResult[None] = self.use_case.archive_plan(plan_id)

        assert not result.success
        assert "Plan is already archived" in str(result.error)

    def test_edit_plan_notes_plan_not_found(self):
        """Test editing notes of non-existent plan."""
        result: UseCaseResult[None] = self.use_case.edit_plan_notes("non_existent_id", "New notes")

        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_edit_account_notes_plan_not_found(self):
        """Test editing account notes in non-existent plan."""
        result: UseCaseResult[None] = self.use_case.edit_account_notes(
            "non_existent_id", "test_account", "New notes"
        )

        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "does not exist" in str(result.error)

    def test_copy_plan_structure_source_not_found(self):
        """Test copying structure from non-existent plan."""
        result = self.use_case.copy_plan_structure("non_existent_id", 1000, "New plan", get_utc_now().date())

        assert not result.success
        assert isinstance(result.error, MoneyPlanError)
        assert "source plan was not found" in str(result.error)

    def test_create_share_link_plan_not_found(self):
        """Test creating share link for non-existent plan."""
        result = self.use_case.create_share_link("non_existent_id", 14, None)

        assert not result.success
        assert "Unable to create share link" in str(result.error)

    def test_get_shared_plan_invalid_token(self):
        """Test getting shared plan with invalid token."""
        result = self.use_case.get_shared_plan(token="invalid_token")

        assert not result.success
        assert "The share link is invalid or has expired" in str(result.error)

    def test_get_shared_plan_expired(self):
        """Test getting shared plan with expired token."""
        # Create a real plan first
        plan_result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert plan_result.success
        plan_id = plan_result.data

        # Create a share link with expired date
        result = self.use_case.create_share_link(plan_id, 0, self.test_user)
        assert result.success

        # Try to get the shared plan
        result = self.use_case.get_shared_plan(result.data.token if result.data else "")

        assert not result.success
        assert "The share link is invalid or has expired" in str(result.error)

    def test_error_if_user_not_set(self):
        """Test that an error is returned if the user is not set in tenancy scope."""
        # Unset the user
        set_current_account(None)
        result = self.use_case.start_plan(initial_balance=1000, notes="Test plan")
        assert not result.success
        assert "no user" in str(result.error).lower() or "user" in str(result.error).lower()
        # Reset user for other tests
        set_current_account(self.test_user)
