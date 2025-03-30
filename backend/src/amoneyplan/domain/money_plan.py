"""
Money Plan aggregate root for the personal money management app.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from amoneyplan.domain.account import Account, Bucket, PlanAccountAllocation
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
class BucketConfig:
    """Configuration for a bucket."""

    bucket_name: str
    category: str
    allocated_amount: Money = field(default_factory=lambda: Money(0))


@dataclass
class AccountAllocationConfig:
    """
    Configuration for an account allocation in a Money Plan.
    """

    account_id: UUID
    name: str
    buckets: List[BucketConfig]


@dataclass(frozen=True)
class MoneyPlan:
    def __init__(self):
        self.initial_balance = Money(0)
        self.remaining_balance = Money(0)
        self.accounts: Dict[UUID, PlanAccountAllocation] = {}
        self.notes = ""
        self.committed = False
        self.is_archived = False
        self.created_at = None
        self.plan_date = None
        self.archived_at = None

    def start_plan(
        self,
        initial_balance: Union[Money, float, str],
        created_at: Optional[datetime] = None,
        plan_date: Optional[date] = None,
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

        self.initial_balance = balance
        self.remaining_balance = Money(balance.as_float)  # Create a new Money instance
        self.notes = notes
        self.committed = False

        # Handle backward compatibility for existing events
        self.created_at = created_at
        self.plan_date = plan_date

        # Process default allocations if provided
        if default_allocations:
            for config in default_allocations:
                account = Account(account_id=config.account_id, name=config.name)

                # Add buckets to the account
                if config.buckets:
                    for bucket_config in config.buckets:
                        bucket = Bucket(
                            bucket_name=bucket_config.bucket_name,
                            category=bucket_config.category,
                            allocated_amount=bucket_config.allocated_amount,
                        )
                        account.buckets[bucket.bucket_name] = bucket
                        # Reduce the remaining balance by the allocated amount
                        self.remaining_balance -= bucket_config.allocated_amount

                # Add the account allocation to the plan
                self.accounts[account.account_id] = PlanAccountAllocation(account=account)

    def allocate_funds(
        self, account_id: Union[UUID, str], bucket_name: str, amount: Union[Money, float, str]
    ):
        """
        Allocate funds to a bucket within an account.

        Args:
            account_id: The ID of the account to allocate to
            bucket_name: The name of the bucket to allocate to
            amount: The amount to allocate

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account ID doesn't exist
            BucketNotFoundError: If the bucket doesn't exist in the account
            InsufficientFundsError: If there aren't enough funds to allocate
        """
        self._check_not_archived()

        if self.committed:
            raise PlanAlreadyCommittedError("Cannot allocate funds to a committed plan")

        if isinstance(account_id, str):
            account_id = UUID(account_id)

        if isinstance(amount, (float, str)):
            amount = Money(amount)

        # Check if we have enough remaining funds
        if amount > self.remaining_balance:
            raise InsufficientFundsError(
                f"Not enough funds to allocate {amount}. Remaining: {self.remaining_balance}"
            )

        # Find the account
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        account_allocation = self.accounts[account_id]
        account = account_allocation.account

        # Find the bucket
        bucket = account.get_bucket(bucket_name)
        if not bucket:
            raise BucketNotFoundError(f"Bucket '{bucket_name}' not found in account '{account.name}'")

        # Update the bucket's allocation
        bucket.allocated_amount += amount

        # Reduce the remaining balance
        self.remaining_balance -= amount

    def reverse_allocation(
        self,
        account_id: Union[UUID, str],
        bucket_name: str,
        original_amount: Union[Money, float, str],
        corrected_amount: Union[Money, float, str],
    ):
        """
        Reverse a previous allocation and apply a corrected amount.

        Args:
            account_id: The ID of the account containing the bucket
            bucket_name: The name of the bucket to adjust
            original_amount: The original amount that was allocated (to be reversed)
            corrected_amount: The new amount to allocate

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account ID doesn't exist
            BucketNotFoundError: If the bucket doesn't exist in the account
            InsufficientFundsError: If there aren't enough funds for the new allocation
        """
        self._check_not_archived()

        if self.committed:
            raise PlanAlreadyCommittedError("Cannot adjust allocations in a committed plan")

        if isinstance(account_id, str):
            account_id = UUID(account_id)

        if isinstance(original_amount, (float, str)):
            original_amount = Money(original_amount)

        if isinstance(corrected_amount, (float, str)):
            corrected_amount = Money(corrected_amount)

        # Find the account
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account with ID {account_id} not found")

        account_allocation = self.accounts[account_id]
        account = account_allocation.account

        # Find the bucket
        bucket = account.get_bucket(bucket_name)
        if not bucket:
            raise BucketNotFoundError(f"Bucket '{bucket_name}' not found in account '{account.name}'")

        # Calculate the net adjustment
        net_adjustment = corrected_amount - original_amount

        # Check if we have enough funds for the adjustment
        if net_adjustment > self.remaining_balance:
            raise InsufficientFundsError(
                f"Not enough funds for adjustment of {net_adjustment}. Remaining: {self.remaining_balance}"
            )

        # Update the bucket and remaining balance
        bucket.allocated_amount += net_adjustment
        self.remaining_balance -= net_adjustment

    def adjust_plan_balance(self, adjustment: Union[Money, float, str], reason: str = ""):
        """
        Adjust the overall plan balance.

        Args:
            adjustment: The amount to adjust by (positive or negative)
            reason: The reason for the adjustment

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

    def change_account_configuration(
        self, account_id: Union[UUID, str], new_bucket_config: List[BucketConfig]
    ):
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

        if isinstance(account_id, str):
            try:
                account_id = UUID(account_id)
            except ValueError as e:
                raise ValueError(f"Invalid UUID format for account ID: {e}")

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
                bucket_name=config.bucket_name,
                category=config.category,
                allocated_amount=config.allocated_amount,
            )
            new_buckets[bucket.bucket_name] = bucket
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
                raise InvalidPlanStateError(
                    f"Account '{allocation.account.name}' must have at least one bucket"
                )

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

    def archive(self):
        """
        Archive the money plan, preventing further modifications.
        Plans can be archived regardless of commitment status.

        Raises:
            MoneyPlanError: If the plan is already archived
        """
        if self.is_archived:
            raise MoneyPlanError("Plan is already archived")

        self.is_archived = True
        self.archived_at = datetime.utcnow()

    def add_account(
        self, account_id: UUID, name: str, buckets: Optional[List[Union[BucketConfig, dict]]] = None
    ):
        """
        Add a new account to the plan.

        Args:
            account_id: UUID for the account.
            name: The name of the account
            buckets: Optional list of bucket configurations, can be BucketConfig objects or dicts

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
                        bucket_name=config["bucket_name"],
                        category=config["category"],
                        allocated_amount=Money(config["allocated_amount"]),
                    )
                else:
                    bucket = Bucket(
                        bucket_name=config.bucket_name,
                        category=config.category,
                        allocated_amount=config.allocated_amount,
                    )
                account_buckets.append(bucket)

        # Create the account with buckets (will add default bucket if none provided)
        account = Account.create(account_id, name, buckets=account_buckets)

        # Update remaining balance
        if account_buckets:
            for bucket in account_buckets:
                self.remaining_balance -= bucket.allocated_amount

        # Add the account to the plan
        self.accounts[account_id] = PlanAccountAllocation(account=account)

    def set_account_checked_state(self, account_id: Union[UUID, str], is_checked: bool) -> None:
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

        account = self.accounts[account_id].account

        if account.is_checked != is_checked:
            account.set_checked_state(is_checked)
        else:
            raise AccountStateMatchError(
                "Account is already checked" if is_checked else "Account is already unchecked"
            )

    def remove_account(self, account_id: Union[UUID, str]):
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

        if isinstance(account_id, str):
            account_id = UUID(account_id)

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

    def edit_account_notes(self, account_id: Union[UUID, str], notes: str):
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

        if isinstance(account_id, str):
            account_id = UUID(account_id)

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
