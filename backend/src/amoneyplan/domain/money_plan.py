"""
Money Plan aggregate root for the personal money management app.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from eventsourcing.domain import Aggregate, event

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
    """Configuration for an account allocation."""

    account_id: UUID
    account_name: str
    buckets: List[BucketConfig] = field(default_factory=list)


class MoneyPlan(Aggregate):
    """
    Money Plan aggregate root that manages the allocation of funds across accounts.
    Implements the event sourcing pattern to track all changes as events.
    """

    def __init__(self):
        self.initial_balance = Money(0)
        self.remaining_balance = Money(0)
        self.accounts: Dict[UUID, PlanAccountAllocation] = {}
        self.notes = ""
        self.committed = False
        self.timestamp = None

    @event("PlanStarted")
    def start_plan(
        self,
        initial_balance: Union[Money, float, str],
        default_allocations: Optional[List[AccountAllocationConfig]] = None,
        notes: str = "",
    ):
        """
        Start a new Money Plan with an initial balance and optional default allocations.

        Args:
            initial_balance: The starting balance for this plan
            default_allocations: Optional list of account allocation configurations
            notes: Free-text notes about this plan
        """
        if isinstance(initial_balance, (float, str)):
            initial_balance = Money(initial_balance)

        self.initial_balance = initial_balance
        self.remaining_balance = initial_balance
        self.notes = notes
        self.committed = False
        self.timestamp = datetime.utcnow()

        # Process default allocations if provided
        if default_allocations:
            for config in default_allocations:
                account = Account(account_id=config.account_id, account_name=config.account_name)

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
                else:
                    # Add a default bucket if none provided
                    account.add_bucket("Default", "Default")

                # Add the account allocation to the plan
                self.accounts[account.account_id] = PlanAccountAllocation(account=account)

    @event("FundsAllocated")
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
            raise BucketNotFoundError(f"Bucket '{bucket_name}' not found in account '{account.account_name}'")

        # Update the bucket's allocation
        bucket.allocated_amount += amount

        # Reduce the remaining balance
        self.remaining_balance -= amount

    @event("AllocationReversed")
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
            raise BucketNotFoundError(f"Bucket '{bucket_name}' not found in account '{account.account_name}'")

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

    @event("PlanBalanceAdjusted")
    def adjust_plan_balance(self, adjustment: Union[Money, float, str], reason: str = ""):
        """
        Adjust the overall plan balance.

        Args:
            adjustment: The amount to adjust by (positive or negative)
            reason: The reason for the adjustment

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
        """
        if self.committed:
            raise PlanAlreadyCommittedError("Cannot adjust the balance of a committed plan")

        if isinstance(adjustment, (float, str)):
            adjustment = Money(adjustment)

        # Update the initial and remaining balances
        self.initial_balance += adjustment
        self.remaining_balance += adjustment

    @event("AccountConfigurationChanged")
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
        if self.committed:
            raise PlanAlreadyCommittedError("Cannot change account configuration in a committed plan")

        if isinstance(account_id, str):
            account_id = UUID(account_id)

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

        for config in new_bucket_config:
            bucket = Bucket(
                bucket_name=config.bucket_name,
                category=config.category,
                allocated_amount=config.allocated_amount,
            )
            new_buckets[bucket.bucket_name] = bucket
            new_total += config.allocated_amount

        # Calculate adjustment needed to remaining balance
        adjustment = current_total - new_total

        # Update the account's buckets and adjust the remaining balance
        account.buckets = new_buckets
        self.remaining_balance += adjustment

    @event("PlanCommitted")
    def commit_plan(self):
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
                    f"Account '{allocation.account.account_name}' must have at least one bucket"
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
                "must equal initial balance ({self.initial_balance}). "
                f"Difference: {difference}"
            )

        # All invariants satisfied, commit the plan
        self.committed = True

    @event("AccountAdded")
    def add_account(self, account_name: str, buckets: Optional[List[BucketConfig]] = None) -> UUID:
        """
        Add a new account to the plan.

        Args:
            account_name: The name of the account
            buckets: Optional list of bucket configurations

        Returns:
            The ID of the new account

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
        """
        if self.committed:
            raise PlanAlreadyCommittedError("Cannot add an account to a committed plan")

        # Create the account
        account = Account.create(account_name=account_name)

        # Add buckets if provided
        if buckets:
            for bucket_config in buckets:
                account.add_bucket(
                    bucket_name=bucket_config.bucket_name,
                    category=bucket_config.category,
                    initial_amount=bucket_config.allocated_amount,
                )
                # Reduce remaining balance
                self.remaining_balance -= bucket_config.allocated_amount

        # Add the account to the plan
        self.accounts[account.account_id] = PlanAccountAllocation(account=account)

        return account.account_id

    def get_total_allocated(self) -> Money:
        """
        Get the total amount allocated across all accounts and buckets.
        """
        total = Money(0)
        for account_allocation in self.accounts.values():
            total += account_allocation.get_total_allocated()
        return total
