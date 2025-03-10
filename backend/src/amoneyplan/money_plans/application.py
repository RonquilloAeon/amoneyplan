"""
Application service for managing Money Plans.
"""

import logging
from dataclasses import asdict
from typing import List, Optional, Union
from uuid import UUID

from django.core.cache import cache
from eventsourcing.application import AggregateNotFoundError, Application
from eventsourcing.persistence import Transcoding
from eventsourcing.system import ProcessingEvent

from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig,
    BucketConfig,
    MoneyPlan,
    PlanAlreadyCommittedError,
)

logger = logging.getLogger("amoneyplan")


def get_current_plan_cache_key(user_id: str) -> str:
    """Get the cache key for storing the current plan ID for a user."""
    return f"money_planner_current_plan_id:{user_id}"


class BucketConfigTranscoding(Transcoding):
    """Custom transcoding for BucketConfig class."""

    type = BucketConfig
    name = "bucket_config"

    def encode(self, obj: BucketConfig) -> dict:
        """Convert BucketConfig to a dictionary for serialization."""
        logger.info("Encoding BucketConfig %s", obj)

        data = asdict(obj)
        data["allocated_amount"] = float(data["allocated_amount"]["amount"])
        return data

    def decode(self, data: dict) -> BucketConfig:
        """Convert dictionary to BucketConfig for deserialization."""
        return BucketConfig(
            bucket_name=data["bucket_name"],
            category=data["category"],
            allocated_amount=Money(data["allocated_amount"]),
        )


class MoneyPlanner(Application):
    """
    Service for creating and managing Money Plans.
    Uses the eventsourcing library to persist and retrieve Money Plans.
    """

    name = "money_planner"

    def __init__(self, env):
        super().__init__(env)
        self.user_id = None  # Will be set by the GraphQL context

    def register_transcodings(self, transcoder):
        super().register_transcodings(transcoder)
        transcoder.register(BucketConfigTranscoding())

    def _get_current_plan_id(self) -> Optional[UUID]:
        """Get the current plan ID from cache."""
        if not self.user_id:
            return None
        plan_id = cache.get(get_current_plan_cache_key(self.user_id))
        return UUID(plan_id) if plan_id else None

    def _set_current_plan_id(self, plan_id: Optional[UUID]) -> None:
        """Set the current plan ID in cache."""
        if not self.user_id:
            return
        cache_key = get_current_plan_cache_key(self.user_id)
        if plan_id:
            cache.set(cache_key, str(plan_id))
        else:
            cache.delete(cache_key)

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
        current_plan_id = self._get_current_plan_id()
        if current_plan_id is not None:
            try:
                plan = self.get_plan(current_plan_id)
                if not plan.committed:
                    raise PlanAlreadyCommittedError(
                        "There is already an uncommitted plan. Commit it before creating a new one."
                    )
            except (KeyError, AggregateNotFoundError):
                # Plan doesn't exist anymore or isn't found, clear the reference
                self._set_current_plan_id(None)

        # Create new plan
        plan = MoneyPlan()
        plan.start_plan(initial_balance=initial_balance, default_allocations=default_allocations, notes=notes)

        # Save the plan and update current plan ID
        self.save(plan)
        self._set_current_plan_id(plan.id)

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
        current_plan_id = self._get_current_plan_id()
        if current_plan_id is None:
            return None

        try:
            plan = self.get_plan(current_plan_id)
            # Clear current plan reference if it's committed
            if plan.committed:
                self._set_current_plan_id(None)
            return plan
        except KeyError:
            # Plan doesn't exist anymore
            self._set_current_plan_id(None)
            return None

    def add_account(self, plan_id: UUID, name: str, buckets: Optional[List[BucketConfig]] = None) -> UUID:
        """
        Add a new account to a plan.

        Args:
            plan_id: The ID of the plan to add the account to
            name: The name of the account
            buckets: Optional list of bucket configurations

        Returns:
            The ID of the new account

        Raises:
            KeyError: If the plan ID doesn't exist
            MoneyPlanError: If there's an error adding the account
        """
        logger.info("Adding account %s to plan %s", name, plan_id)
        plan = self.get_plan(plan_id)
        account_id = plan.add_account(name=name, buckets=buckets)
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

        # Clear current plan reference if this was the current plan
        current_plan_id = self._get_current_plan_id()
        if current_plan_id == plan_id:
            self._set_current_plan_id(None)

    def list_plans(self) -> List[UUID]:
        """
        List all Money Plan IDs.

        Returns:
            A list of Money Plan IDs ordered by creation time (most recent first)
        """
        # Use the events store to find all initial events (version 1) for plans
        seen_plans = set()  # Track plans we've seen to avoid duplicates
        plan_ids = []  # Preserve order while avoiding duplicates
        # Get notifications in batches of 10 (default section size)
        start = 1
        while True:
            try:
                notifications = list(self.notification_log.select(start=start, limit=10))
                if not notifications:
                    break

                # Process notifications in reverse order to get most recent first
                for notification in reversed(notifications):
                    if notification.originator_version == 1:  # Initial plan creation event
                        if notification.originator_id not in seen_plans:
                            plan_ids.append(notification.originator_id)
                            seen_plans.add(notification.originator_id)

                start += len(notifications)
            except ValueError:
                # We've reached the end of the log
                break

        return plan_ids

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

    def archive_plan(self, plan_id: UUID) -> None:
        """
        Archive a money plan to prevent further modifications.

        Args:
            plan_id: The ID of the plan to archive

        Raises:
            MoneyPlanError: If the plan doesn't exist or is already archived
        """
        plan = self.get_plan(plan_id)
        plan.archive_plan()
        self.save(plan)
