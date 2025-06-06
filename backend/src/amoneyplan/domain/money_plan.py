# ruff: noqa: E501
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Union

from amoneyplan.domain.money import Money


class MoneyPlanError(Exception):
    """Base exception class for money plan errors."""

    pass


class InsufficientFundsError(MoneyPlanError):
    """Raised when trying to allocate more funds than are available."""

    pass


class PlanAlreadyCommittedError(MoneyPlanError):
    """Raised when trying to modify an already committed plan."""

    pass


class BucketNotFoundError(MoneyPlanError):
    """Raised when referencing a bucket that doesn't exist."""

    pass


class AccountNotFoundError(MoneyPlanError):
    """Raised when referencing an account that doesn't exist."""

    pass


class AccountStateMatchError(MoneyPlanError):
    """Raised when the account state already matches the desired state."""

    pass


class InvalidPlanStateError(MoneyPlanError):
    """Raised when the plan is in an invalid state for commitment."""

    pass


@dataclass
class Bucket:
    """
    Represents a bucket (or sub-account) within an account.
    Each bucket has a name, category, and allocated amount.
    """

    name: str
    category: str
    allocated_amount: Money = field(default_factory=lambda: Money(0))

    def __str__(self) -> str:
        return f"{self.name} ({self.category}): {self.allocated_amount}"


@dataclass
class PlanAccount:
    """
    Represents a financial account (e.g., "Wealthfront", "Apple Card").
    An account has a unique ID, a name, and contains one or more buckets.
    """

    account_id: str
    buckets: Dict[str, Bucket] = field(default_factory=dict)
    is_checked: bool = field(default=False)
    notes: str = ""

    @classmethod
    def create(
        cls, account_id: str, buckets: Optional[List[Union[Bucket, dict]]] = None, notes: str = ""
    ) -> "PlanAccount":
        """
        Factory method to create a new account with a generated ID.
        If no buckets are provided or added during creation, creates a default bucket.

        Args:
            account_id: id for the account.
            buckets: Optional list of buckets to add to the account. Can be Bucket objects or dicts.
            notes: Optional notes for the account.
        """
        account = cls(account_id=account_id, buckets={}, notes=notes)

        if buckets:
            # If buckets are provided, use those
            for bucket_data in buckets:
                if isinstance(bucket_data, dict):
                    bucket = Bucket(
                        name=bucket_data["name"],
                        category=bucket_data["category"],
                        allocated_amount=Money(bucket_data["allocated_amount"]),
                    )
                else:
                    bucket = bucket_data
                account.buckets[bucket.name] = bucket
        else:
            # Only create default bucket if no buckets were provided
            default_bucket = Bucket(name="Default", category="default")
            account.buckets[default_bucket.name] = default_bucket

        return account

    def add_bucket(self, bucket_name: str, category: str, initial_amount: Money | None = None) -> Bucket:
        """
        Add a new bucket to this account.
        """
        if not initial_amount:
            initial_amount = Money(0)

        bucket = Bucket(name=bucket_name, category=category, allocated_amount=initial_amount)

        self.buckets[bucket_name] = bucket
        return bucket

    def get_bucket(self, bucket_name: str) -> Optional[Bucket]:
        """
        Get a bucket by name.
        """
        return self.buckets.get(bucket_name)

    def get_total_allocated(self) -> Money:
        """
        Calculate the total amount allocated across all buckets.
        """
        total = Money(0)
        for bucket in self.buckets.values():
            total += bucket.allocated_amount
        return total

    def set_checked_state(self, is_checked: bool) -> None:
        """Change the checked state of the account."""
        self.is_checked = is_checked

    def edit_notes(self, notes: str):
        """
        Edit the notes of the account.

        Args:
            notes: The new notes for the account
        """
        self.notes = notes

    def __str__(self) -> str:
        return f"PlanAccount {self.account_id} ({len(self.buckets)} buckets)"


@dataclass
class PlanAccountAllocation:
    """
    Represents an allocation of funds to an account within a Money Plan.
    """

    account: PlanAccount
    name: str

    def get_total_allocated(self) -> Money:
        """
        Get the total amount allocated to this account across all buckets.
        """
        return self.account.get_total_allocated()


@dataclass
class BucketConfig:
    """Configuration for a bucket."""

    name: str
    category: str
    allocated_amount: Money = field(default_factory=lambda: Money(0))


@dataclass
class AccountAllocationConfig:
    """
    Configuration for an account allocation in a Money Plan.
    """

    account_id: str
    account_name: str
    buckets: List[BucketConfig]


@dataclass
class MoneyPlan:
    id: str
    initial_balance: Money
    remaining_balance: Money
    created_at: datetime
    plan_date: date

    accounts: Dict[str, PlanAccountAllocation] = field(default_factory=dict)
    archived_at: Optional[datetime] = None
    committed: bool = False
    is_archived: bool = False
    notes: str = ""

    @classmethod
    def start_plan(
        cls,
        id: str,
        initial_balance: Union[Money, float, str],
        created_at: datetime = None,
        plan_date: date = None,
        default_allocations: Optional[List[AccountAllocationConfig]] = None,
        notes: str = "",
    ):
        """
        Start a new Money Plan with an initial balance and optional default allocations.

        For backward compatibility, created_at and plan_date are optional.
        If not provided, created_at defaults to current time and plan_date to current date.
        """
        balance = (
            Money(initial_balance) if isinstance(initial_balance, (float, str, int)) else initial_balance
        )

        remaining_balance = Money(balance.as_float)

        # Process default allocations if provided
        accounts = {}
        if default_allocations:
            for config in default_allocations:
                account = PlanAccount(account_id=config.account_id)

                # Add buckets to the account
                if config.buckets:
                    for bucket_config in config.buckets:
                        bucket = Bucket(
                            name=bucket_config.name,
                            category=bucket_config.category,
                            allocated_amount=bucket_config.allocated_amount,
                        )
                        account.buckets[bucket.name] = bucket
                        # Reduce the remaining balance by the allocated amount
                        remaining_balance -= bucket.allocated_amount

                # Add the account allocation to the plan
                accounts[account.account_id] = PlanAccountAllocation(
                    account=account, name=config.account_name
                )

        return cls(
            id=id,
            initial_balance=balance,
            remaining_balance=remaining_balance,
            created_at=created_at,
            plan_date=plan_date,
            accounts=accounts,
            notes=notes,
        )

    @classmethod
    def copy_structure(
        cls,
        id: str,
        source_plan,
        initial_balance: Union[Money, float, str],
        created_at: datetime = None,
        plan_date: date = None,
        notes: str = "",
    ):
        """
        Create a new plan with the account structure copied from an existing plan.
        All allocations in the new plan will be set to zero.

        Args:
            id: The ID for the new plan
            source_plan: The plan to copy structure from
            initial_balance: The initial balance for the new plan
            created_at: Optional creation timestamp
            plan_date: Optional plan date
            notes: Optional notes for the new plan

        Returns:
            A new MoneyPlan instance with the same account and bucket structure
        """
        if isinstance(initial_balance, (float, str)):
            initial_balance = Money(initial_balance)

        accounts = {}
        # Copy each account from the source plan
        for account_id, allocation in source_plan.accounts.items():
            source_account = allocation.account
            # Create a new plan account with empty allocations
            new_account = PlanAccount(account_id=account_id)

            # Copy bucket structure with zero allocations
            for bucket_name, bucket in source_account.buckets.items():
                new_bucket = Bucket(name=bucket.name, category=bucket.category, allocated_amount=Money(0))
                new_account.buckets[bucket_name] = new_bucket

            # Add account to the new plan
            accounts[account_id] = PlanAccountAllocation(account=new_account, name=allocation.name)

        return cls(
            id=id,
            initial_balance=initial_balance,
            remaining_balance=initial_balance,  # All allocations start at 0
            created_at=created_at,
            plan_date=plan_date,
            accounts=accounts,
            notes=notes,
        )

    def allocate_funds(self, account_id: str, bucket_name: str, amount: Union[Money, float, str]):
        """
        Allocate or deallocate funds to/from a bucket within an account.

        Args:
            account_id: The ID of the account to allocate to
            bucket_name: The name of the bucket to allocate to
            amount: The amount to allocate (positive) or deallocate (negative)

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account ID doesn't exist
            BucketNotFoundError: If the bucket doesn't exist in the account
            InsufficientFundsError: If there aren't enough funds to allocate (for positive amounts)
            InsufficientFundsError: If the bucket doesn't have enough funds to deallocate (for negative amounts)
        """
        self._check_not_archived()
        if self.committed:
            raise PlanAlreadyCommittedError("Cannot allocate funds to a committed plan")

        if isinstance(amount, (float, str)):
            amount = Money(amount)

        # Find the account
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        account_allocation = self.accounts[account_id]
        account = account_allocation.account

        # Find the bucket
        bucket = account.get_bucket(bucket_name)
        if not bucket:
            raise BucketNotFoundError(f"Bucket {bucket_name!r} not found in the account")

        # For positive amounts (allocating funds), check if we have enough funds
        if amount > Money(0) and amount > self.remaining_balance:
            raise InsufficientFundsError(
                f"Not enough funds to allocate {amount}. Remaining: {self.remaining_balance}"
            )

        # For negative amounts (deallocating funds), check if the bucket has enough funds
        if amount < Money(0) and abs(amount) > bucket.allocated_amount:
            raise InsufficientFundsError(
                f"Not enough funds in bucket to deallocate {abs(amount)}. "
                f"Current allocation: {bucket.allocated_amount}"
            )

        # Update the bucket's allocation
        bucket.allocated_amount += amount

        # Update the remaining balance
        self.remaining_balance -= amount

    def adjust_plan_balance(self, adjustment: Union[Money, float, str]):
        """
        Adjust the overall plan balance.

        Args:
            adjustment: The amount to adjust by (positive or negative)

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
        """
        self._check_not_archived()

        if self.committed:
            raise PlanAlreadyCommittedError("Cannot adjust the balance of a committed plan")

        if isinstance(adjustment, (float, str)):
            adjustment = Money(adjustment)

        # Update the initial and remaining balances
        self.initial_balance += adjustment
        self.remaining_balance += adjustment

    def change_account_configuration(self, account_id: str, new_bucket_config: List[BucketConfig]):
        """
        Change the bucket configuration for an account.

        Args:
            account_id: The ID of the account to modify
            new_bucket_config: The new bucket configuration

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account ID doesn't exist
        """
        self._check_not_archived()

        if self.committed:
            raise PlanAlreadyCommittedError("Cannot change account configuration in a committed plan")

        # Find the account
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        account_allocation = self.accounts[account_id]
        account = account_allocation.account

        # Calculate the current total allocated to this account's buckets
        current_total = account.get_total_allocated()

        # Create new buckets dictionary
        new_buckets = {}
        new_total = Money(0)

        # Process each bucket configuration
        for config in new_bucket_config:
            bucket = Bucket(
                name=config.name,
                category=config.category,
                allocated_amount=config.allocated_amount,
            )
            new_buckets[bucket.name] = bucket
            new_total += bucket.allocated_amount

        # Calculate adjustment needed to remaining balance
        adjustment = current_total - new_total

        # Update the account's buckets and adjust the remaining balance
        account.buckets = new_buckets
        self.remaining_balance += adjustment

    def commit(self):
        """
        Commit the money plan, finalizing the allocations.

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            InvalidPlanStateError: If the plan doesn't satisfy the invariants for commitment
        """
        if self.committed:
            raise PlanAlreadyCommittedError("Plan is already committed")

        # Check invariants
        # 1. At least one account must exist
        if not self.accounts:
            raise InvalidPlanStateError("Plan must have at least one account to be committed")

        # 2. Each account must have at least one bucket
        for account_id, allocation in self.accounts.items():
            if not allocation.account.buckets:
                raise InvalidPlanStateError(f"Account '{allocation.name}' must have at least one bucket")

        # 3. Sum of all bucket allocations must equal the initial balance
        total_allocated = sum(
            (account.get_total_allocated().as_decimal for account in self.accounts.values()),
            start=Money(0).as_decimal,
        )

        # Allow for small rounding errors (less than 1 cent)
        if abs(total_allocated - self.initial_balance.as_decimal) >= 0.01:
            difference = Money(self.initial_balance.as_decimal - total_allocated)
            raise InvalidPlanStateError(
                f"Sum of bucket allocations ({total_allocated}) "
                f"must equal initial balance ({self.initial_balance}). "
                f"Difference: {difference}"
            )

        # All invariants satisfied, commit the plan
        self.committed = True

    def archive_plan(self, now: datetime):
        """Archive the money plan, preventing further modifications."""
        if self.is_archived:
            raise MoneyPlanError("Plan is already archived")

        self.is_archived = True
        self.archived_at = now

    def edit_plan_notes(self, notes: str):
        """Edit the notes of the money plan."""
        self.notes = notes

    def _check_not_archived(self):
        """Ensure the plan is not archived before making modifications."""
        if self.is_archived:
            raise MoneyPlanError("Cannot modify an archived plan")

    def add_account(
        self,
        account_id: str,
        account_name: str,
        buckets: Optional[List[Union[BucketConfig, dict]]] = None,
        notes: str = "",
    ):
        """
        Add a new account to the plan.

        Args:
            account_id: id for the account
            buckets: Optional list of bucket configurations, can be BucketConfig objects or dicts
            notes: Optional notes for the account

        Returns:
            The ID of the new account

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
        """
        self._check_not_archived()

        if self.committed:
            raise PlanAlreadyCommittedError("Cannot add an account to a committed plan")

        # Convert BucketConfigs or dicts to Buckets
        account_buckets = None
        if buckets:
            account_buckets = []
            for config in buckets:
                if isinstance(config, dict):
                    bucket = Bucket(
                        name=config["name"],
                        category=config["category"],
                        allocated_amount=Money(config["allocated_amount"]),
                    )
                else:
                    bucket = Bucket(
                        name=config.name,
                        category=config.category,
                        allocated_amount=config.allocated_amount,
                    )
                account_buckets.append(bucket)

        # Create the account with buckets (will add default bucket if none provided)
        account = PlanAccount.create(account_id, buckets=account_buckets, notes=notes)

        # Update remaining balance
        if account_buckets:
            for bucket in account_buckets:
                self.remaining_balance -= bucket.allocated_amount

        # Add the account to the plan
        self.accounts[account_id] = PlanAccountAllocation(account=account, name=account_name)

    def set_account_checked_state(self, account_id: str, is_checked: bool) -> None:
        """
        Set the checked state of an account.

        Args:
            account_id: The ID of the account
            is_checked: The desired checked state

        Raises:
            AccountNotFoundError: If the account doesn't exist
        """
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        plan_account = self.accounts[account_id].account

        if plan_account.is_checked != is_checked:
            plan_account.set_checked_state(is_checked)
        else:
            raise AccountStateMatchError(
                "Account is already checked" if is_checked else "Account is already unchecked"
            )

    def remove_account(self, account_id: str):
        """
        Remove an account from the plan.

        Args:
            account_id: The ID of the account to remove

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account ID doesn't exist
        """
        self._check_not_archived()

        if self.committed:
            raise PlanAlreadyCommittedError("Cannot remove an account from a committed plan")

        # Find the account
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        # Return allocated funds to remaining balance
        account_allocation = self.accounts[account_id]
        self.remaining_balance += account_allocation.get_total_allocated()

        # Remove the account
        del self.accounts[account_id]

    def edit_notes(self, notes: str):
        """
        Edit the notes of the plan.

        Args:
            notes: The new notes for the plan

        Raises:
            MoneyPlanError: If the plan is archived
        """
        self._check_not_archived()
        self.notes = notes

    def edit_account_notes(self, account_id: str, notes: str):
        """
        Edit the notes of an account.

        Args:
            account_id: The ID of the account
            notes: The new notes for the account

        Raises:
            AccountNotFoundError: If the account ID doesn't exist
            MoneyPlanError: If the plan is archived
        """
        self._check_not_archived()

        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        account = self.accounts[account_id].account
        account.notes = notes

    def get_total_allocated(self) -> Money:
        """
        Get the total amount allocated across all accounts and buckets.
        """
        total = Money(0)
        for account_allocation in self.accounts.values():
            total += account_allocation.get_total_allocated()
        return total
