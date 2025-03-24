"""
Application service for managing Money Plans.
"""

import logging
from dataclasses import asdict
from typing import Iterator, List, Optional, Union
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from eventsourcing.application import AggregateNotFoundError, Application, EventSourcedLog
from eventsourcing.persistence import Transcoding
from eventsourcing.system import ProcessingEvent

from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig,
    BucketConfig,
    MoneyPlan,
    MoneyPlanLogged,
    PlanAlreadyCommittedError,
)

logger = logging.getLogger("amoneyplan")


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


class AccountAllocationConfigTranscoding(Transcoding):
    """Custom transcoding for AccountAllocationConfig class."""

    type = AccountAllocationConfig
    name = "account_allocation_config"

    def encode(self, obj: AccountAllocationConfig) -> dict:
        """Convert AccountAllocationConfig to a dictionary for serialization."""
        logger.info("Encoding AccountAllocationConfig %s", obj)

        # Convert buckets using BucketConfigTranscoding
        bucket_transcoding = BucketConfigTranscoding()
        return {
            "account_id": str(obj.account_id),
            "name": obj.name,
            "buckets": [bucket_transcoding.encode(b) for b in obj.buckets] if obj.buckets else [],
        }

    def decode(self, data: dict) -> AccountAllocationConfig:
        """Convert dictionary to AccountAllocationConfig for deserialization."""
        bucket_transcoding = BucketConfigTranscoding()
        return AccountAllocationConfig(
            account_id=UUID(data["account_id"]),
            name=data["name"],
            buckets=[bucket_transcoding.decode(b) for b in data["buckets"]] if data["buckets"] else None,
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
        self.plan_log: EventSourcedLog[MoneyPlanLogged] = EventSourcedLog(
            self.events, uuid5(NAMESPACE_URL, "/money_plan_log"), MoneyPlanLogged
        )

    def register_transcodings(self, transcoder):
        super().register_transcodings(transcoder)
        transcoder.register(BucketConfigTranscoding())
        transcoder.register(AccountAllocationConfigTranscoding())

    def _get_current_plan_id(self) -> Optional[UUID]:
        """Get the current uncommitted plan ID by checking the most recent plans."""
        if not self.user_id:
            return None

        # Look for the most recent plan (limit=1, desc=True)
        for _, plan in self.get_plans(limit=1, desc=True):
            # Only consider plan as current if it's both uncommitted and not archived
            if not plan.committed and not plan.is_archived:
                return plan.id
        return None

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
            except AggregateNotFoundError:
                # Plan doesn't exist anymore, we can proceed
                pass

        # Create new plan
        plan = MoneyPlan()
        plan.start_plan(initial_balance=initial_balance, default_allocations=default_allocations, notes=notes)
        plan_logged = self.plan_log.trigger_event(plan_id=plan.id)

        # Save the plan
        self.save(plan, plan_logged)

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
            return self.get_plan(current_plan_id)
        except KeyError:
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
        account_id = uuid4()
        plan.add_account(account_id, name=name, buckets=buckets)
        self.save(plan)
        return account_id

    def remove_account(self, plan_id: UUID, account_id: Union[UUID, str]) -> None:
        """
        Remove an account from a plan.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account to remove

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account doesn't exist
        """
        plan = self.get_plan(plan_id)
        plan.remove_account(account_id=account_id)
        self.save(plan)

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

    def set_account_checked_state(
        self, plan_id: UUID, account_id: Union[UUID, str], is_checked: bool
    ) -> None:
        """
        Set the checked state of an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            is_checked: The desired checked state

        Raises:
            PlanAlreadyCommittedError: If the plan is already committed
            AccountNotFoundError: If the account doesn't exist
        """
        plan = self.get_plan(plan_id)
        plan.set_account_checked_state(account_id=account_id, is_checked=is_checked)
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

    def get_plans(
        self,
        *,
        gt: int | None = None,
        lte: int | None = None,
        desc: bool = True,  # Default to descending (most recent first)
        limit: int | None = None,
    ) -> Iterator[tuple[int, MoneyPlan]]:
        """Get money plans with their notification positions for cursor-based pagination.

        Args:
            gt: Return plans after this notification position
            lte: Return plans up to and including this notification position
            desc: Order by notification position descending (defaults to True for most recent first)
            limit: Maximum number of plans to return

        Returns:
            Iterator of (position, plan) tuples where position can be used as a cursor
        """
        for notification in self.plan_log.get(gt=gt, lte=lte, desc=desc, limit=limit):
            # Return both the notification position (for cursors) and the plan
            yield notification.originator_version, self.get_plan(notification.plan_id)

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

    def edit_plan_notes(self, plan_id: UUID, notes: str) -> None:
        """
        Edit the notes of a plan.

        Args:
            plan_id: The ID of the plan
            notes: The new notes for the plan
        """
        plan = self.get_plan(plan_id)
        plan.edit_plan_notes(notes)
        self.save(plan)

    def edit_account_notes(self, plan_id: UUID, account_id: UUID, notes: str) -> None:
        """
        Edit the notes of an account.

        Args:
            plan_id: The ID of the plan
            account_id: The ID of the account
            notes: The new notes for the account
        """
        plan = self.get_plan(plan_id)
        plan.edit_account_notes(account_id, notes)
        self.save(plan)

    def copy_plan_structure(
        self,
        source_plan_id: UUID,
        initial_balance: Union[Money, float, str],
        notes: str = "",
    ) -> UUID:
        """
        Create a new plan with the account structure copied from an existing plan.
        All allocations in the new plan will be set to zero.

        Args:
            source_plan_id: The ID of the plan to copy structure from
            initial_balance: The initial balance for the new plan
            notes: Optional notes for the new plan

        Returns:
            The ID of the new plan

        Raises:
            KeyError: If the source plan doesn't exist
            PlanAlreadyCommittedError: If there's an uncommitted plan already
        """
        # Check if there's already an uncommitted plan (reuse existing check)
        current_plan_id = self._get_current_plan_id()
        if current_plan_id is not None:
            try:
                plan = self.get_plan(current_plan_id)
                if not plan.committed:
                    raise PlanAlreadyCommittedError(
                        "There is already an uncommitted plan. Commit it before creating a new one."
                    )
            except AggregateNotFoundError:
                # Plan doesn't exist anymore, we can proceed
                pass

        # Get the source plan to copy from
        source_plan = self.get_plan(source_plan_id)

        default_allocations = None
        if source_plan and source_plan.accounts:
            # Extract accounts and buckets from the source plan
            default_allocations = []

            for account_id, allocation in source_plan.accounts.items():
                account = allocation.account
                buckets = []

                # Create bucket configs with zero allocations
                for bucket_name, bucket in account.buckets.items():
                    buckets.append(
                        BucketConfig(
                            bucket_name=bucket.bucket_name,
                            category=bucket.category,
                            allocated_amount=Money(0),  # Start with zero allocations
                        )
                    )

                # Create account allocation config
                default_allocations.append(
                    AccountAllocationConfig(account_id=account.account_id, name=account.name, buckets=buckets)
                )

            logger.info(f"Copied {len(default_allocations)} account structures from plan {source_plan_id}")

        # Create new plan using the copied structure
        return self.create_plan(
            initial_balance=initial_balance, default_allocations=default_allocations, notes=notes
        )
