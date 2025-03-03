"""
Application service for managing Money Plans.
"""

from typing import List, Optional, Union
from uuid import UUID

from eventsourcing.application import Application
from eventsourcing.system import ProcessingEvent

from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig,
    BucketConfig,
    MoneyPlan,
    PlanAlreadyCommittedError,
)


class MoneyPlanner(Application):
    """
    Service for creating and managing Money Plans.
    Uses the eventsourcing library to persist and retrieve Money Plans.
    """

    # The current active money plan being worked on
    current_plan_id: Optional[UUID] = None

    def create_plan(
        self,
        initial_balance: Union[Money, float, str],
        default_allocations: Optional[List[AccountAllocationConfig]] = None,
        notes: str = "",
    ) -> UUID:
        """
        Create a new Money Plan.

        Args:
            initial_balance: The initial balance for the plan
            default_allocations: Optional list of account allocation configurations
            notes: Optional notes for the plan

        Returns:
            The ID of the new plan

        Raises:
            PlanAlreadyCommittedError: If there's an uncommitted plan already
        """
        # Check if there's a current uncommitted plan
        if self.current_plan_id is not None:
            plan = self.get_plan(self.current_plan_id)
            if not plan.committed:
                raise PlanAlreadyCommittedError(
                    "There is already an uncommitted plan. Commit it before creating a new one."
                )

        # Create new plan
        plan = MoneyPlan()
        plan.start_plan(initial_balance=initial_balance, default_allocations=default_allocations, notes=notes)

        # Save the plan
        self.save(plan)
        self.current_plan_id = plan.id

        return plan.id

    def get_plan(self, plan_id: UUID) -> MoneyPlan:
        """
        Get a Money Plan by ID.

        Args:
            plan_id: The ID of the plan to retrieve

        Returns:
            The Money Plan

        Raises:
            KeyError: If the plan doesn't exist
        """
        return self.repository.get(plan_id)

    def get_current_plan(self) -> Optional[MoneyPlan]:
        """
        Get the current Money Plan being worked on.

        Returns:
            The current Money Plan, or None if there isn't one
        """
        if self.current_plan_id is None:
            return None

        return self.get_plan(self.current_plan_id)

    def add_account(
        self, plan_id: UUID, account_name: str, buckets: Optional[List[BucketConfig]] = None
    ) -> UUID:
        """
        Add an account to a Money Plan.

        Args:
            plan_id: The ID of the plan
            account_name: The name of the account
            buckets: Optional list of bucket configurations

        Returns:
            The ID of the new account

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
        """
        plan = self.get_plan(plan_id)
        account_id = plan.add_account(account_name=account_name, buckets=buckets)
        self.save(plan)
        return account_id

    def allocate_funds(
        self,
        plan_id: UUID,
        account_id: Union[UUID, str],
        bucket_name: str,
        amount: Union[Money, float, str],
    ) -> None:
        """
        Allocate funds to a bucket within an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            bucket_name: The name of the bucket
            amount: The amount to allocate

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account doesn't exist
            BucketNotFoundError: If the bucket doesn't exist
            InsufficientFundsError: If there aren't enough funds to allocate
        """
        plan = self.get_plan(plan_id)
        plan.allocate_funds(account_id=account_id, bucket_name=bucket_name, amount=amount)
        self.save(plan)

    def reverse_allocation(
        self,
        plan_id: UUID,
        account_id: Union[UUID, str],
        bucket_name: str,
        original_amount: Union[Money, float, str],
        corrected_amount: Union[Money, float, str],
    ) -> None:
        """
        Reverse an allocation and apply a corrected amount.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            bucket_name: The name of the bucket
            original_amount: The original amount that was allocated
            corrected_amount: The corrected amount to allocate

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account doesn't exist
            BucketNotFoundError: If the bucket doesn't exist
            InsufficientFundsError: If there aren't enough funds for the new allocation
        """
        plan = self.get_plan(plan_id)
        plan.reverse_allocation(
            account_id=account_id,
            bucket_name=bucket_name,
            original_amount=original_amount,
            corrected_amount=corrected_amount,
        )
        self.save(plan)

    def adjust_plan_balance(
        self, plan_id: UUID, adjustment: Union[Money, float, str], reason: str = ""
    ) -> None:
        """
        Adjust the overall plan balance.

        Args:
            plan_id: The ID of the plan
            adjustment: The amount to adjust (positive or negative)
            reason: Optional reason for the adjustment

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
        """
        plan = self.get_plan(plan_id)
        plan.adjust_plan_balance(adjustment=adjustment, reason=reason)
        self.save(plan)

    def change_account_configuration(
        self, plan_id: UUID, account_id: Union[UUID, str], new_bucket_config: List[BucketConfig]
    ) -> None:
        """
        Change the bucket configuration for an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            new_bucket_config: The new bucket configuration

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account doesn't exist
        """
        plan = self.get_plan(plan_id)
        plan.change_account_configuration(account_id=account_id, new_bucket_config=new_bucket_config)
        self.save(plan)

    def commit_plan(self, plan_id: UUID) -> None:
        """
        Commit a Money Plan, finalizing its allocations.

        Args:
            plan_id: The ID of the plan to commit

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            InvalidPlanStateError: If the plan doesn't satisfy commitment invariants
        """
        plan = self.get_plan(plan_id)
        plan.commit_plan()
        self.save(plan)

    def list_plans(self) -> List[UUID]:
        """
        List all Money Plan IDs.

        Returns:
            A list of Money Plan IDs
        """
        return self.repository.get_entity_ids()

    # Notification handlers for processing events
    def policy(self, domain_event: ProcessingEvent, process_event) -> None:
        """
        Policy for handling domain events.

        Args:
            domain_event: The domain event to process
            process_event: Function to process the event
        """
        # This method can be implemented to handle any side effects or notifications
        # that need to happen when domain events occur
        pass
