import logging
import secrets
from datetime import date, timedelta
from typing import List, Optional, TypeVar, Union

from django.contrib.auth.models import AnonymousUser, User
from django.db import transaction

from amoneyplan.accounts.tenancy import get_current_account
from amoneyplan.common.models import generate_safe_cuid16
from amoneyplan.common.time import get_utc_now
from amoneyplan.common.use_cases import UseCaseException, UseCaseResult
from amoneyplan.domain.account import Account as DomainAccount
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig as DomainAccountAllocationConfig,
)
from amoneyplan.domain.money_plan import (
    MoneyPlan as DomainMoneyPlan,
)

from .models import MoneyPlan, PlanShareLink
from .repositories import (
    AccountRepository,
    MoneyPlanRepository,
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


class AccountUseCases:
    """Use cases for Account entity."""

    def __init__(self):
        self.account_repo = AccountRepository()

    def get_account(self, account_id: str) -> UseCaseResult[DomainAccount]:
        """
        Get an account by ID.

        Args:
            account_id: The ID of the account to retrieve

        Returns:
            UseCaseResult containing the account or error information
        """
        try:
            account = self.account_repo.get_by_id(account_id)
            if not account:
                return UseCaseResult.failure(error=f"Account with ID {account_id} not found")
            return UseCaseResult.success(data=account)
        except Exception as e:
            logger.error(f"Error getting account: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    def get_all_accounts(self) -> UseCaseResult[List[DomainAccount]]:
        """
        Get all accounts for the current user.

        Returns:
            UseCaseResult containing the list of accounts or error information
        """
        try:
            accounts = self.account_repo.get_all()
            return UseCaseResult.success(data=accounts)
        except Exception as e:
            logger.error(f"Error getting accounts: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def create_account(self, name: str, notes: str = "") -> UseCaseResult[DomainAccount]:
        """
        Create a new account.

        Args:
            name: The name of the account
            notes: Optional notes for the account

        Returns:
            UseCaseResult containing the created account or error information
        """
        try:
            # Generate a new account ID
            account_id = generate_safe_cuid16()

            # Create the domain model
            account = DomainAccount.create(
                account_id,
                name=name,
                notes=notes,
            )

            # Save the account
            self.account_repo.save(account)

            return UseCaseResult.success(data=account)
        except Exception as e:
            logger.error(f"Error creating account: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def update_account(self, account_id: str, name: str, notes: str = "") -> UseCaseResult[DomainAccount]:
        """
        Update an existing account.

        Args:
            account_id: The ID of the account to update
            name: The new name for the account
            notes: Optional new notes for the account

        Returns:
            UseCaseResult containing the updated account or error information
        """
        try:
            # Get the existing account
            account_result = self.get_account(account_id)
            if not account_result.success:
                return account_result

            account = account_result.data

            # Update the account
            # TODO move to domain
            account.name = name
            account.notes = notes

            # Save the account
            self.account_repo.save(account)

            return UseCaseResult.success(data=account)
        except Exception as e:
            logger.error(f"Error updating account: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)


# Value objects
class BucketConfig:
    """Configuration for a bucket."""

    def __init__(self, name: str, category: str, allocated_amount: Money = None):
        self.name = name
        self.category = category
        self.allocated_amount = allocated_amount or Money(0)


class AccountAllocationConfig:
    """Configuration for an account allocation in a Money Plan."""

    def __init__(self, account_id: str, buckets: List[BucketConfig] = None):
        self.account_id = account_id
        self.buckets = buckets or []


class MoneyPlanUseCases:
    def __init__(self):
        self.account_repo = AccountRepository()
        self.money_plan_repo = MoneyPlanRepository()

    def _get_current_plan_id(self) -> Optional[str]:
        """Get the current uncommitted plan ID by checking the most recent plans."""
        # Look for the most recent plan
        current_plan = self.money_plan_repo.get_current_plan()
        if current_plan:
            return str(current_plan.id)

        return None

    def _check_not_archived(self, plan: MoneyPlan):
        """Check if the plan is not archived."""
        if plan.is_archived:
            raise MoneyPlanError("Cannot modify an archived plan")

    def start_plan(
        self,
        initial_balance: Union[Money, float, str],
        default_allocations: Optional[List[AccountAllocationConfig]] = None,
        notes: str = "",
        plan_date: Optional[date] = None,
    ) -> UseCaseResult[str]:
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

            # Verify all accounts in default_allocations exist
            allocations = []

            if default_allocations:
                for config in default_allocations:
                    account = self.account_repo.get_by_id(config.account_id)
                    if not account:
                        return UseCaseResult.failure(
                            AccountNotFoundError(f"Account with ID {config.account_id} does not exist")
                        )

                    allocations.append(DomainAccountAllocationConfig(**config, account_name=account.name))

            with transaction.atomic():
                # Generate a new ID for the plan
                plan_id = generate_safe_cuid16()

                # Create a new domain model MoneyPlan using the class method
                plan = DomainMoneyPlan.start_plan(
                    id=plan_id,
                    initial_balance=initial_balance,
                    created_at=get_utc_now(),
                    plan_date=plan_date or date.today(),
                    default_allocations=default_allocations,
                    notes=notes,
                )

                # Save the domain model through the repository
                self.money_plan_repo.save(plan)

            return UseCaseResult.success(data=plan_id)
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
            plan = self.money_plan_repo.get_by_id(plan_id)
            return UseCaseResult.success(data=plan)
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
            # Get the domain model directly from the repository
            plan = self.money_plan_repo.get_current_plan()

            if plan is None:
                return UseCaseResult.success(data=None, message="No current plan found")

            return UseCaseResult.success(data=plan)
        except Exception as e:
            logger.error(f"Error retrieving current plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def add_account(
        self, plan_id: str, account_id: str, buckets: Optional[List[BucketConfig]] = None, notes: str = ""
    ) -> UseCaseResult:
        """
        Add a new account to a plan.

        Args:
            plan_id: The ID of the plan to add the account to
            name: The ID of the account being added
            buckets: Optional list of bucket configurations
            notes: Optional notes for the account

        Returns:
            UseCaseResult containing the ID of the new account or error information
        """
        logger.info("Adding account %s to plan %s", account_id, plan_id)

        try:
            # Get the domain model from repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Get the account as well
            account = self.account_repo.get_by_id(account_id)
            if not account:
                return UseCaseResult.failure(
                    AccountNotFoundError(f"Account with ID {account_id} does not exist")
                )

            # Use the domain model's add_account method
            plan.add_account(account_id=account_id, account_name=account.name, buckets=buckets, notes=notes)

            # Save the updated domain model through the repository
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
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
            # Get the domain model from repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Use the domain model's remove_account method
            plan.remove_account(account_id)

            # Save the updated domain model through the repository
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
        The amount can be positive (to add funds) or negative (to remove funds).

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            bucket_name: The name of the bucket
            amount: The amount to allocate (positive) or deallocate (negative)

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            # Get the domain model from repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Use the domain model's allocate_funds method
            plan.allocate_funds(account_id=account_id, bucket_name=bucket_name, amount=amount)

            # Save the updated domain model through the repository
            self.money_plan_repo.save(plan)

            return UseCaseResult.success()
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error allocating funds: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def adjust_plan_balance(
        self,
        plan_id: str,
        adjustment: Union[Money, float, str],
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
            # Get the domain model from repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Use the domain model's adjust_balance method
            plan.adjust_plan_balance(adjustment)

            # Save the updated domain model through the repository
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
            # Get the domain model from the repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            # Get the domain model
            plan = plan_result.data

            # Use the domain model's change_account_configuration method
            plan.change_account_configuration(account_id, new_bucket_config)

            # Save the updated domain model through the repository
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(message="Account configuration updated successfully")
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
        Set the checked state of an account in a Money Plan.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            is_checked: Whether the account should be checked

        Returns:
            UseCaseResult indicating success or failure
        """
        try:
            # Get the domain model from the repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            # Get the domain model
            plan = plan_result.data

            try:
                # Use the domain model's set_account_checked_state method
                plan.set_account_checked_state(account_id, is_checked)

                # Save the updated domain model through the repository
                self.money_plan_repo.save(plan)

                return UseCaseResult.success()
            except AccountStateMatchError as e:
                return UseCaseResult.failure(error=e)

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
            # Get the domain model from the repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            # Get the domain model
            plan = plan_result.data

            # Use the domain model's commit method which has all the validation logic
            plan.commit()

            # Save the updated domain model through the repository
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(message="Plan committed successfully")
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error committing plan: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

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
            # Get the domain model from the repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            plan = plan_result.data

            # Use the domain model's archive_plan method
            plan.archive_plan(get_utc_now())

            # Save the updated domain model through the repository
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
            # Get the domain model from the repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            # Get the domain model
            plan = plan_result.data

            # Use the domain model's edit_notes method
            plan.edit_notes(notes)

            # Save the updated domain model through the repository
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(message="Plan notes updated successfully")
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
            # Get the domain model from the repository
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(error=plan_result.error)

            # Get the domain model
            plan = plan_result.data

            # Use the domain model's edit_account_notes method
            plan.edit_account_notes(account_id, notes)

            # Save the updated domain model through the repository
            self.money_plan_repo.save(plan)

            return UseCaseResult.success(message="Account notes updated successfully")
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
        plan_date: Optional[date] = None,
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
                logger.warning(f"Error getting source plan: {source_plan_result.error}")
                return UseCaseResult.failure(
                    error=MoneyPlanError(
                        "Unable to copy plan structure because the source plan was not found."
                    )
                )

            source_plan = source_plan_result.data

            # Generate a new ID for the plan
            plan_id = generate_safe_cuid16()

            # Use the domain model's copy_structure method
            new_plan = DomainMoneyPlan.copy_structure(
                id=plan_id,
                source_plan=source_plan,
                initial_balance=initial_balance,
                created_at=get_utc_now(),
                plan_date=plan_date or date.today(),
                notes=notes,
            )

            # Save the new plan through the repository
            self.money_plan_repo.save(new_plan)

            logger.info(f"Copied plan structure from plan {source_plan_id} to new plan {plan_id}")

            return UseCaseResult.success(data=plan_id)
        except MoneyPlanError as e:
            return UseCaseResult.failure(error=e)
        except Exception as e:
            logger.error(f"Error copying plan structure: {e}", exc_info=True)
            return UseCaseResult.failure(error=e)

    @transaction.atomic
    def create_share_link(self, plan_id: str, expiry_days: int, user: User) -> UseCaseResult:
        """
        Create a temporary share link for a plan.

        Args:
            plan_id: The ID of the plan to share
            expiry_days: Number of days before the link expires (default: 14)
            request: Optional request object containing the user

        Returns:
            UseCaseResult containing the share link details or error
        """
        try:
            # Get the plan
            plan_result = self.get_plan(plan_id)
            if not plan_result.success:
                return UseCaseResult.failure(
                    UseCaseException("Unable to create share link because the plan does not exist.")
                )

            # Generate a random token
            token = secrets.token_urlsafe(32)
            expires_at = get_utc_now() + timedelta(days=expiry_days)

            # Create share link
            if isinstance(user, AnonymousUser):
                return UseCaseResult.failure(UseCaseException("Could not determine the current user."))

            current_account = get_current_account()

            if not current_account:
                return UseCaseResult.failure(UseCaseException("Could not determine the current account."))

            share_link = PlanShareLink.objects.create(
                plan_id=plan_id,
                token=token,
                expires_at=expires_at,
                created_by=user,
                user_account=current_account,
            )

            return UseCaseResult.success(data=share_link)
        except Exception as e:
            logger.error(f"Error creating share link: {e}", exc_info=True)
            return UseCaseResult.failure(
                UseCaseException("Unable to create share link."), message="Please try again later."
            )

    def get_shared_plan(self, token: str) -> UseCaseResult[DMP]:
        """
        Get a plan by share token without requiring authentication.

        Args:
            token: The share token

        Returns:
            UseCaseResult containing the plan or error
        """
        try:
            # Find valid share link

            share_link = (
                PlanShareLink.unscoped.filter(
                    token=token,
                )
                .order_by("-expires_at")
                .first()
            )

            logger.info(f"Found share link: {share_link}")

            if not share_link or share_link.expires_at < get_utc_now():
                return UseCaseResult.failure(UseCaseException("The share link is invalid or has expired."))

            # Return the associated plan
            plan = self.money_plan_repo.get_by_id(share_link.plan_id, scoped=False)
            logger.info(f"Found plan: {plan}")

            return UseCaseResult.success(data=plan)
        except Exception as e:
            logger.error(f"Error retrieving shared plan: {e}", exc_info=True)
            return UseCaseResult.failure(
                UseCaseException("Unable to retrieve shared plan."), message="Please try again later."
            )
