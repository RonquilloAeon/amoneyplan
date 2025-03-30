"""
Service classes for the Money Plan app.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple, TypeVar, Union
from uuid import UUID

from django.db import models, transaction

from amoneyplan.common.use_cases import UseCaseResult
from amoneyplan.domain.money import Money

if TYPE_CHECKING:
    from amoneyplan.domain.money_plan import MoneyPlan as DomainMoneyPlan

from .models import Bucket, MoneyPlan, PlanAccount
from .repositories import (
    AccountRepository,
    BucketRepository,
    MoneyPlanRepository,
    PlanAccountRepository,
    to_domain_money_plan,
)

logger = logging.getLogger("amoneyplan")

# Define a TypeVar for DomainMoneyPlan to use in return type annotations
DMP = TypeVar("DMP", bound="DomainMoneyPlan")


# Domain exceptions
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


# Value objects
class BucketConfig:
    """Configuration for a bucket."""

    def __init__(self, bucket_name: str, category: str, allocated_amount: Money = None):
        self.bucket_name = bucket_name
        self.category = category
        self.allocated_amount = allocated_amount or Money(0)


class AccountAllocationConfig:
    """Configuration for an account allocation in a Money Plan."""

    def __init__(self, account_id: str, name: str, buckets: List[BucketConfig] = None):
        self.account_id = account_id
        self.name = name
        self.buckets = buckets or []


class MoneyPlanUseCases:
    def __init__(self):
        self.money_plan_repo = MoneyPlanRepository()
        self.account_repo = AccountRepository()
        self.plan_account_repo = PlanAccountRepository()
        self.bucket_repo = BucketRepository()
        self.user_id = None  # Will be set by the GraphQL context

    def _get_current_plan_id(self) -> Optional[str]:
        """Get the current uncommitted plan ID by checking the most recent plans."""
        if not self.user_id:
            return None

        # Look for the most recent plan
        current_plan = self.money_plan_repo.get_current_plan(self.user_id)
        if current_plan:
            return str(current_plan.id)

        return None

    def _check_not_archived(self, plan: MoneyPlan):
        """Check if the plan is not archived."""
        if plan.is_archived:
            raise MoneyPlanError("Cannot modify an archived plan")

    def create_plan(
        self,
        initial_balance: Union[Money, float, str],
        default_allocations: Optional[List[AccountAllocationConfig]] = None,
        notes: str = "",
        plan_date: Optional[date] = None,
    ) -> UseCaseResult[UUID]:
        """
        Create a new Money Plan.

        Args:
            initial_balance: The initial balance for the plan
            default_allocations: Optional list of account allocation configurations
            notes: Optional notes for the plan
            plan_date: Optional date for the plan

        Returns:
            UseCaseResult containing the ID of the new plan or error information
        """
        try:
            # Check if there's a current uncommitted plan
            current_plan_id = self._get_current_plan_id()
            if current_plan_id is not None:
                plan_result = self.get_plan(current_plan_id)
                if plan_result.has_data() and not plan_result.data.committed:
                    return UseCaseResult.failure(
                        PlanAlreadyCommittedError(
                            "There is already an uncommitted plan. Commit it before creating a new one."
                        )
                    )

            # Convert to Money and get decimal value
            if isinstance(initial_balance, (float, str, int)):
                balance = Money(initial_balance)
            else:
                balance = initial_balance

            # Create new plan
            with transaction.atomic():
                plan = self.money_plan_repo.create(
                    initial_balance=balance.as_decimal,
                    owner_id=self.user_id,
                    notes=notes,
                    plan_date=plan_date or date.today(),
                )

                # Process default allocations if provided
                if default_allocations:
                    for config in default_allocations:
                        # Get or create the account
                        account, _ = self.account_repo.get_or_create(config.name, self.user_id)

                        # Create plan account
                        plan_account = self.plan_account_repo.create(plan_id=plan.id, account_id=account.id)

                        # Create buckets
                        if config.buckets:
                            for bucket_config in config.buckets:
                                bucket_amount = bucket_config.allocated_amount.as_decimal
                                self.bucket_repo.create(
                                    plan_account_id=plan_account.id,
                                    name=bucket_config.bucket_name,
                                    category=bucket_config.category,
                                    allocated_amount=bucket_amount,
                                )
                                # Reduce the remaining balance
                                plan.remaining_balance -= bucket_amount
                        else:
                            # Create default bucket if none provided
                            self.bucket_repo.create(
                                plan_account_id=plan_account.id,
                                name="Default",
                                category="default",
                                allocated_amount=0,
                            )

                        # Update plan
                        self.money_plan_repo.save(plan)

            return UseCaseResult.success(data=plan.id)
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error creating plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    def get_plan(self, plan_id: str) -> UseCaseResult[DMP]:
        """
        Get a Money Plan by ID.

        Args:
            plan_id: The ID of the plan to retrieve

        Returns:
            UseCaseResult containing the Money Plan as a domain object or error information
        """
        try:
            # Convert str to UUID if needed for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            plan = self.money_plan_repo.get_by_id(plan_uuid, self.user_id)
            return UseCaseResult.success(data=to_domain_money_plan(plan))
        except MoneyPlan.DoesNotExist:
            error = MoneyPlanError(f"Plan with ID {plan_id} does not exist")
            return UseCaseResult.failure(error=error)
        except Exception as e:
            logger.error(f"Error retrieving plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    def get_current_plan(self) -> UseCaseResult[DMP]:
        """
        Get the current Money Plan being worked on.

        Returns:
            UseCaseResult containing the current Money Plan as a domain object or None
        """
        try:
            current_plan_id = self._get_current_plan_id()
            if current_plan_id is None:
                return UseCaseResult.success(data=None, message="No current plan found")

            plan = self.money_plan_repo.get_by_id(current_plan_id, self.user_id)
            return UseCaseResult.success(data=to_domain_money_plan(plan))
        except MoneyPlan.DoesNotExist:
            return UseCaseResult.success(data=None)
        except Exception as e:
            logger.error(f"Error retrieving current plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def add_account(
        self, plan_id: str, name: str, buckets: Optional[List[BucketConfig]] = None
    ) -> UseCaseResult[str]:
        """
        Add a new account to a plan.

        Args:
            plan_id: The ID of the plan to add the account to
            name: The name of the account
            buckets: Optional list of bucket configurations

        Returns:
            UseCaseResult containing the ID of the new account or error information
        """
        logger.info("Adding account %s to plan %s", name, plan_id)

        try:
            # Convert str to UUID if needed for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            # Check if plan is not committed
            if plan.committed:
                return UseCaseResult.failure(PlanAlreadyCommittedError("Cannot modify a committed plan"))

            # Get or create the account
            account, _ = self.account_repo.get_or_create(name, self.user_id)

            # Create plan account
            plan_account = self.plan_account_repo.create(plan_id=plan_uuid, account_id=account.id)

            # Add buckets if provided
            if buckets:
                for bucket_config in buckets:
                    bucket_amount = bucket_config.allocated_amount.as_decimal
                    self.bucket_repo.create(
                        plan_account_id=plan_account.id,
                        name=bucket_config.bucket_name,
                        category=bucket_config.category,
                        allocated_amount=bucket_amount,
                    )

                    # Update remaining balance
                    plan.remaining_balance -= bucket_amount
            else:
                # Create default bucket if none provided
                self.bucket_repo.create(
                    plan_account_id=plan_account.id, name="Default", category="default", allocated_amount=0
                )

            # Save plan
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(data=str(account.id))
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error adding account: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def remove_account(self, plan_id: str, account_id: str) -> UseCaseResult[None]:
        """
        Remove an account from a plan.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account to remove

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            # Check if plan is not committed
            if plan.committed:
                return UseCaseResult.failure(
                    error=PlanAlreadyCommittedError("Cannot modify a committed plan")
                )

            # Convert to UUID for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            account_uuid = UUID(account_id) if isinstance(account_id, str) else account_id

            try:
                # Find the plan account
                plan_account = PlanAccount.objects.get(plan_id=plan_uuid, account_id=account_uuid)
            except PlanAccount.DoesNotExist:
                return UseCaseResult.failure(
                    error=AccountNotFoundError(f"Account with ID {account_id} not found in plan")
                )

            # Calculate total allocated in account's buckets to add back to remaining balance
            total_allocated = plan_account.get_total_allocated()

            # Add back funds to remaining balance
            plan.remaining_balance += total_allocated

            # Delete plan account (cascades to buckets)
            plan_account.delete()

            # Save plan
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error removing account: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def allocate_funds(
        self,
        plan_id: str,
        account_id: str,
        bucket_name: str,
        amount: Union[Money, float, str],
    ) -> UseCaseResult[None]:
        """
        Allocate funds to a bucket within an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            bucket_name: The name of the bucket
            amount: The amount to allocate

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            # Check if plan is not committed
            if plan.committed:
                return UseCaseResult.failure(
                    error=PlanAlreadyCommittedError("Cannot modify a committed plan")
                )

            # Convert amount to Money
            if isinstance(amount, (float, str, int)):
                amount = Money(amount)

            # Check if we have enough remaining funds
            if amount.as_decimal > plan.remaining_balance:
                return UseCaseResult.failure(
                    error=InsufficientFundsError(
                        f"Not enough funds to allocate {amount}. Remaining: {plan.remaining_balance}"
                    )
                )

            # Convert to UUID for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            account_uuid = UUID(account_id) if isinstance(account_id, str) else account_id

            try:
                # Find the plan account
                plan_account = PlanAccount.objects.get(plan_id=plan_uuid, account_id=account_uuid)
            except PlanAccount.DoesNotExist:
                return UseCaseResult.failure(
                    error=AccountNotFoundError(f"Account with ID {account_id} not found in plan")
                )

            # Find bucket
            bucket = self.bucket_repo.find_by_name_and_plan_account(
                name=bucket_name, plan_account_id=plan_account.id
            )

            if not bucket:
                return UseCaseResult.failure(
                    error=BucketNotFoundError(
                        f"Bucket '{bucket_name}' not found in account '{plan_account.account.name}'"
                    )
                )

            # Update the bucket's allocation
            bucket.allocated_amount += amount.as_decimal
            self.bucket_repo.save(bucket)

            # Reduce the remaining balance
            plan.remaining_balance -= amount.as_decimal
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error allocating funds: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def reverse_allocation(
        self,
        plan_id: str,
        account_id: str,
        bucket_name: str,
        original_amount: Union[Money, float, str],
        corrected_amount: Union[Money, float, str],
    ) -> UseCaseResult[None]:
        """
        Reverse an allocation and apply a corrected amount.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            bucket_name: The name of the bucket
            original_amount: The original amount that was allocated
            corrected_amount: The corrected amount to allocate

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            # Check if plan is not committed
            if plan.committed:
                return UseCaseResult.failure(
                    error=PlanAlreadyCommittedError("Cannot modify a committed plan")
                )

            # Convert to UUID for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            account_uuid = UUID(account_id) if isinstance(account_id, str) else account_id

            if isinstance(original_amount, (float, str)):
                original_amount = Money(original_amount)

            if isinstance(corrected_amount, (float, str)):
                corrected_amount = Money(corrected_amount)

            try:
                # Find the plan account
                plan_account = PlanAccount.objects.get(plan_id=plan_uuid, account_id=account_uuid)
            except PlanAccount.DoesNotExist:
                return UseCaseResult.failure(
                    error=AccountNotFoundError(f"Account with ID {account_id} not found in plan")
                )

            # Find bucket
            bucket = self.bucket_repo.find_by_name_and_plan_account(
                name=bucket_name, plan_account_id=plan_account.id
            )

            if not bucket:
                return UseCaseResult.failure(
                    error=BucketNotFoundError(f"Bucket '{bucket_name}' not found in account")
                )

            # Calculate the net adjustment
            net_adjustment = corrected_amount.as_decimal - original_amount.as_decimal

            # Check if we have enough funds for the adjustment
            if net_adjustment > plan.remaining_balance:
                return UseCaseResult.failure(
                    error=InsufficientFundsError(
                        f"Not enough funds for adjustment of {net_adjustment}. "
                        f"Remaining: {plan.remaining_balance}"
                    )
                )

            # Update the bucket's allocation
            bucket.allocated_amount += net_adjustment
            self.bucket_repo.save(bucket)

            # Update remaining balance
            plan.remaining_balance -= net_adjustment
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error reversing allocation: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def adjust_plan_balance(
        self, plan_id: str, adjustment: Union[Money, float, str], reason: str = ""
    ) -> UseCaseResult[None]:
        """
        Adjust the overall plan balance.

        Args:
            plan_id: The ID of the plan
            adjustment: The amount to adjust (positive or negative)
            reason: Optional reason for the adjustment

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            # Check if plan is not committed
            if plan.committed:
                return UseCaseResult.failure(
                    error=PlanAlreadyCommittedError("Cannot modify a committed plan")
                )

            # Convert to Money
            if isinstance(adjustment, (float, str)):
                adjustment = Money(adjustment)

            # Update the initial and remaining balances
            plan.initial_balance += adjustment.as_decimal
            plan.remaining_balance += adjustment.as_decimal
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error adjusting plan balance: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def change_account_configuration(
        self, plan_id: str, account_id: str, new_bucket_config: List[BucketConfig]
    ) -> UseCaseResult[None]:
        """
        Change the bucket configuration for an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            new_bucket_config: The new bucket configuration

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            # Check if plan is not committed
            if plan.committed:
                return UseCaseResult.failure(
                    error=PlanAlreadyCommittedError("Cannot modify a committed plan")
                )

            # Convert to UUID for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            account_uuid = UUID(account_id) if isinstance(account_id, str) else account_id

            try:
                # Find the plan account
                plan_account = PlanAccount.objects.get(plan_id=plan_uuid, account_id=account_uuid)
            except PlanAccount.DoesNotExist:
                return UseCaseResult.failure(
                    error=AccountNotFoundError(f"Account with ID {account_id} not found in plan")
                )

            # Calculate current total allocated to this account's buckets
            current_total = plan_account.get_total_allocated()

            # Calculate new total from new configuration
            new_total = Decimal("0.00")
            for config in new_bucket_config:
                new_total += config.allocated_amount.as_decimal

            # Calculate adjustment needed to remaining balance
            adjustment = current_total - new_total

            # Update the plan's remaining balance
            plan.remaining_balance += adjustment
            self.money_plan_repo.save(plan)

            # Delete existing buckets
            plan_account.buckets.all().delete()

            # Create new buckets
            for config in new_bucket_config:
                self.bucket_repo.create(
                    plan_account_id=plan_account.id,
                    name=config.bucket_name,
                    category=config.category,
                    allocated_amount=config.allocated_amount.as_decimal,
                )

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error changing account configuration: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def set_account_checked_state(
        self, plan_id: str, account_id: str, is_checked: bool
    ) -> UseCaseResult[None]:
        """
        Set the checked state of an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            is_checked: The desired checked state

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            # Convert to UUID for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            account_uuid = UUID(account_id) if isinstance(account_id, str) else account_id

            try:
                # Find the plan account
                plan_account = PlanAccount.objects.get(plan_id=plan_uuid, account_id=account_uuid)
            except PlanAccount.DoesNotExist:
                return UseCaseResult.failure(
                    error=AccountNotFoundError(f"Account with ID {account_id} not found")
                )

            # Check state
            if plan_account.is_checked == is_checked:
                return UseCaseResult.failure(
                    error=AccountStateMatchError(
                        "Account is already checked" if is_checked else "Account is already unchecked"
                    )
                )

            # Update checked state
            plan_account.is_checked = is_checked
            self.plan_account_repo.save(plan_account)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error setting account checked state: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def commit_plan(self, plan_id: str) -> UseCaseResult[None]:
        """
        Commit a Money Plan, finalizing its allocations.

        Args:
            plan_id: The ID of the plan to commit

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is already committed
            if plan.committed:
                return UseCaseResult.failure(error=PlanAlreadyCommittedError("Plan is already committed"))

            # Check invariants
            # 1. At least one account must exist
            if not plan.plan_accounts.exists():
                return UseCaseResult.failure(
                    error=InvalidPlanStateError("Plan must have at least one account to be committed")
                )

            # 2. Each account must have at least one bucket
            for account in plan.plan_accounts.all():
                if not account.buckets.exists():
                    return UseCaseResult.failure(
                        error=InvalidPlanStateError(
                            f"Account '{account.account.name}' must have at least one bucket"
                        )
                    )

            # 3. Sum of all bucket allocations must equal the initial balance
            total_allocated = Bucket.objects.filter(plan_account__plan=plan).aggregate(
                total=models.Sum("allocated_amount")
            )["total"] or Decimal("0.00")

            # Allow for small rounding errors (less than 1 cent)
            if abs(total_allocated - plan.initial_balance) >= Decimal("0.01"):
                difference = plan.initial_balance - total_allocated
                return UseCaseResult.failure(
                    error=InvalidPlanStateError(
                        f"Sum of bucket allocations ({total_allocated}) "
                        f"must equal initial balance ({plan.initial_balance}). "
                        f"Difference: {difference}"
                    )
                )

            # All invariants satisfied, commit the plan
            plan.committed = True
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(message="Plan committed successfully")
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error committing plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    def get_plans(
        self,
        *,
        gt: int | None = None,
        lte: int | None = None,
        desc: bool = True,  # Default to descending (most recent first)
        limit: int | None = None,
    ) -> Iterator[Tuple[int, DMP]]:
        """
        Get money plans with their notification positions for cursor-based pagination.

        Args:
            gt: Return plans after this notification position
            lte: Return plans up to and including this notification position
            desc: Order by notification position descending (defaults to True for most recent first)
            limit: Maximum number of plans to return

        Returns:
            Iterator of (position, plan) tuples where position can be used as a cursor
            and plan is a domain object
        """
        # For compatibility with the eventsourcing implementation,
        # we'll use a simplified approach converting gt/lte positions to UUIDs
        gt_id = UUID(int=gt) if gt is not None else None
        lte_id = UUID(int=lte) if lte is not None else None

        for position, plan in self.money_plan_repo.get_plans_paginated(
            user_id=self.user_id, gt_id=gt_id, lte_id=lte_id, desc=desc, limit=limit
        ):
            # Convert Django model to domain model
            yield position, to_domain_money_plan(plan)

    @transaction.atomic
    def archive_plan(self, plan_id: str) -> UseCaseResult[None]:
        """
        Archive a money plan to prevent further modifications.

        Args:
            plan_id: The ID of the plan to archive

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            if plan.is_archived:
                return UseCaseResult.failure(error=MoneyPlanError("Plan is already archived"))

            plan.is_archived = True
            plan.archived_at = datetime.now(timezone.utc)
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(message="Plan archived successfully")
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error archiving plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def edit_plan_notes(self, plan_id: str, notes: str) -> UseCaseResult[None]:
        """
        Edit the notes of a plan.

        Args:
            plan_id: The ID of the plan
            notes: The new notes for the plan

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Check if plan is not archived
            self._check_not_archived(plan)

            plan.notes = notes
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error editing plan notes: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def edit_account_notes(self, plan_id: str, account_id: str, notes: str) -> UseCaseResult[None]:
        """
        Edit the notes of an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            notes: The new notes for the account

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            # Check if plan is not archived
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data
            self._check_not_archived(plan)

            # Convert to UUID for repository layer
            plan_uuid = UUID(plan_id) if isinstance(plan_id, str) else plan_id
            account_uuid = UUID(account_id) if isinstance(account_id, str) else account_id

            try:
                # Find the plan account
                plan_account = PlanAccount.objects.get(plan_id=plan_uuid, account_id=account_uuid)
            except PlanAccount.DoesNotExist:
                return UseCaseResult.failure(
                    error=AccountNotFoundError(f"Account with ID {account_id} not found")
                )

            # Update notes
            plan_account.notes = notes
            self.plan_account_repo.save(plan_account)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error editing account notes: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def copy_plan_structure(
        self,
        source_plan_id: str,
        initial_balance: Union[Money, float, str],
        notes: str = "",
    ) -> UseCaseResult[str]:
        """
        Create a new plan with the account structure copied from an existing plan.
        All allocations in the new plan will be set to zero.

        Args:
            source_plan_id: The ID of the plan to copy structure from
            initial_balance: The initial balance for the new plan
            notes: Optional notes for the new plan

        Returns:
            UseCaseResult containing the ID of the new plan or error information
        """
        try:
            # Check if there's already an uncommitted plan
            current_plan_id = self._get_current_plan_id()
            if current_plan_id is not None:
                plan_result = self.get_plan(current_plan_id)
                if plan_result.has_data() and not plan_result.data.committed:
                    return UseCaseResult.failure(
                        error=PlanAlreadyCommittedError(
                            "There is already an uncommitted plan. Commit it before creating a new one."
                        )
                    )

            # Get the source plan
            source_plan_result = self.get_plan(source_plan_id)
            if not source_plan_result.success:
                return UseCaseResult.failure(error=source_plan_result.error)

            source_plan = source_plan_result.data

            # Convert to Money
            if isinstance(initial_balance, (float, str)):
                initial_balance = Money(initial_balance)

            # Convert str to UUID if needed for repository layer
            UUID(source_plan_id) if isinstance(source_plan_id, str) else source_plan_id

            # Create new plan
            new_plan = self.money_plan_repo.create(
                initial_balance=initial_balance.as_decimal, owner_id=self.user_id, notes=notes
            )

            # Copy account structure
            if source_plan.plan_accounts.exists():
                for source_plan_account in source_plan.plan_accounts.all():
                    # Create plan account
                    plan_account = self.plan_account_repo.create(
                        plan_id=new_plan.id, account_id=source_plan_account.account.id
                    )

                    # Create buckets with zero allocations
                    for source_bucket in source_plan_account.buckets.all():
                        self.bucket_repo.create(
                            plan_account_id=plan_account.id,
                            name=source_bucket.name,
                            category=source_bucket.category,
                            allocated_amount=0,  # Start with zero allocations
                        )

                logger.info(
                    f"Copied {source_plan.plan_accounts.count()} account structures "
                    f"from plan {source_plan_id}"
                )

            return UseCaseResult.success(data=str(new_plan.id))
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error copying plan structure: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)
