import logging
from datetime import date
from typing import List, Optional

import strawberry
from django.apps import apps
from strawberry import relay
from strawberry.types import Info

from amoneyplan.accounts.schema import AuthMutations, AuthQueries
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig,
    BucketConfig,
    MoneyPlanError,
    PlanAlreadyCommittedError,
)

logger = logging.getLogger("amoneyplan")


# GraphQL output types
@strawberry.type
class Bucket(relay.Node):
    id: relay.NodeID[str]
    bucket_name: str
    category: str
    allocated_amount: float

    @classmethod
    def resolve_node(cls, node_id: str, info: Info) -> Optional["Bucket"]:
        # In a real implementation, you would parse the node_id and fetch the bucket
        # For now, we return None as buckets are always loaded through their parent Account
        return None

    @staticmethod
    def from_domain(domain_bucket) -> "Bucket":
        bucket = Bucket(
            id=domain_bucket.bucket_name,
            bucket_name=domain_bucket.bucket_name,
            category=domain_bucket.category,
            allocated_amount=domain_bucket.allocated_amount.as_float,
        )
        return bucket


@strawberry.type
class Account(relay.Node):
    id: relay.NodeID[str]
    name: str
    buckets: List[Bucket]
    is_checked: bool
    notes: str = ""

    @classmethod
    def resolve_node(cls, node_id: str, info: Info) -> Optional["Account"]:
        # In a real implementation, you would parse the node_id and fetch the account
        # For now, we return None as accounts are always loaded through their parent MoneyPlan
        return None

    @staticmethod
    def from_domain(domain_account) -> "Account":
        account = Account(
            id=domain_account.account_id,
            name=domain_account.name,
            buckets=[Bucket.from_domain(bucket) for bucket in domain_account.buckets.values()],
            is_checked=domain_account.is_checked,
            notes=domain_account.notes,
        )
        return account


@strawberry.type
class MoneyPlan(relay.Node):
    id: relay.NodeID[str]
    initial_balance: float
    remaining_balance: float
    accounts: List[Account]
    notes: str
    is_committed: bool
    is_archived: bool
    created_at: Optional[str] = None
    plan_date: Optional[str] = None
    archived_at: Optional[str] = None

    @classmethod
    def resolve_node(cls, node_id: str, info: Info) -> Optional["MoneyPlan"]:
        use_case = apps.get_app_config("money_plans").money_planner
        try:
            plan_result = use_case.get_plan(node_id)
            if plan_result.success and plan_result.has_data():
                return MoneyPlan.from_domain(plan_result.data)
            return None
        except (KeyError, ValueError):
            return None

    @staticmethod
    def from_domain(domain_plan) -> "MoneyPlan":
        plan = MoneyPlan(
            id=domain_plan.id,
            initial_balance=domain_plan.initial_balance.as_float,
            remaining_balance=domain_plan.remaining_balance.as_float,
            accounts=[
                Account.from_domain(allocation.account) for allocation in domain_plan.accounts.values()
            ],
            notes=domain_plan.notes,
            is_committed=domain_plan.committed,
            is_archived=domain_plan.is_archived,
            created_at=domain_plan.created_at.isoformat() if domain_plan.created_at else None,
            plan_date=domain_plan.plan_date.isoformat() if domain_plan.plan_date else None,
            archived_at=domain_plan.archived_at.isoformat() if domain_plan.archived_at else None,
        )
        return plan


@strawberry.type
class MoneyPlanConnection(relay.Connection[MoneyPlan]):
    class Meta:
        node = MoneyPlan


@strawberry.type
class Error:
    message: str


@strawberry.type
class PlanResult:
    money_plan: Optional[MoneyPlan] = None
    error: Optional[Error] = None
    success: bool


# GraphQL input types
@strawberry.input
class BucketConfigInput:
    bucket_name: str
    category: str
    allocated_amount: float = 0.0

    def to_domain(self) -> BucketConfig:
        return BucketConfig(
            bucket_name=self.bucket_name,
            category=self.category,
            allocated_amount=Money(self.allocated_amount),
        )


@strawberry.input
class AccountAllocationConfigInput:
    account_id: Optional[str] = None
    name: str
    buckets: List[BucketConfigInput]

    def to_domain(self) -> AccountAllocationConfig:
        return AccountAllocationConfig(
            account_id=self.account_id if self.account_id else None,
            account_name=self.name,
            buckets=[bucket.to_domain() for bucket in self.buckets],
        )


@strawberry.input
class PlanStartInput:
    initial_balance: float
    notes: str = ""
    plan_date: Optional[date] = None
    default_allocations: Optional[List[AccountAllocationConfigInput]] = None
    copy_from: Optional[relay.GlobalID] = None


@strawberry.input
class AllocateFundsInput:
    plan_id: relay.GlobalID
    account_id: str
    bucket_name: str
    amount: float


@strawberry.input
class ReverseAllocationInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID
    bucket_name: str
    original_amount: float
    corrected_amount: float


@strawberry.input
class PlanBalanceAdjustInput:
    plan_id: relay.GlobalID
    adjustment: float
    reason: str = ""


@strawberry.input
class AccountConfigurationChangeInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID
    new_bucket_config: List[BucketConfigInput]


@strawberry.input
class AddAccountInput:
    plan_id: relay.GlobalID
    name: str
    buckets: Optional[List[BucketConfigInput]] = None


@strawberry.input
class CommitPlanInput:
    plan_id: relay.GlobalID


@strawberry.input
class ArchivePlanInput:
    plan_id: relay.GlobalID


@strawberry.input
class RemoveAccountInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID


@strawberry.input
class SetAccountCheckedStateInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID
    is_checked: bool


@strawberry.input
class MoneyPlanFilter:
    """Input type for filtering money plans."""

    is_archived: bool = False
    status: Optional[str] = None  # 'all', 'draft', or 'committed'


@strawberry.input
class EditPlanNotesInput:
    plan_id: relay.GlobalID
    notes: str


@strawberry.input
class EditAccountNotesInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID
    notes: str


# GraphQL queries
@strawberry.type
class Query(AuthQueries):
    @strawberry.field
    def money_plan(self, info: Info, plan_id: Optional[relay.GlobalID] = None) -> Optional[MoneyPlan]:
        """
        Get a Money Plan by ID or the current plan if no ID is provided.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        if plan_id:
            plan_id = plan_id.node_id
            plan_result = use_case.get_plan(plan_id)

            if plan_result.success and plan_result.has_data():
                return MoneyPlan.from_domain(plan_result.data)
            else:
                logger.warning(f"Failed to get plan: {plan_result.message}")
                return None
        else:
            plan_result = use_case.get_current_plan()

            if plan_result.success and plan_result.has_data():
                return MoneyPlan.from_domain(plan_result.data)

            return None

    @strawberry.field
    def money_plans(
        self,
        info: Info,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        filter: Optional[MoneyPlanFilter] = None,
    ) -> MoneyPlanConnection:
        """Get a paginated list of money plans."""
        if not info.context.request.user.is_authenticated:
            return MoneyPlanConnection(
                edges=[],
                page_info=relay.PageInfo(
                    has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
                ),
            )
        try:
            use_case = apps.get_app_config("money_plans").money_planner

            # Convert cursor strings to notification positions
            after_pos = None if after is None else int(strawberry.relay.from_base64(after)[1])
            before_pos = None if before is None else int(strawberry.relay.from_base64(before)[1])

            # Use descending order by default, switch to ascending only if using 'last'
            desc = not bool(last)

            # When displaying in descending order (most recent first), we need to adjust our gt/lte logic
            if desc:
                # When desc=True, swap gt/lte logic
                gt_pos = None
                lte_pos = after_pos - 1 if after_pos is not None else before_pos
            else:
                # When desc=False (using last), use normal gt/lte logic
                gt_pos = after_pos
                lte_pos = before_pos

            plans_with_pos = list(use_case.get_plans(gt=gt_pos, lte=lte_pos, desc=desc, limit=first or last))

            # Apply filters if provided
            if filter:
                if filter.is_archived:
                    # When is_archived is true, show only archived plans
                    plans_with_pos = [(pos, plan) for pos, plan in plans_with_pos if plan.is_archived]
                else:
                    # When is_archived is false, show only non-archived plans
                    plans_with_pos = [(pos, plan) for pos, plan in plans_with_pos if not plan.is_archived]

                # Filter by status if specified
                if filter.status:
                    if filter.status == "draft":
                        plans_with_pos = [(pos, plan) for pos, plan in plans_with_pos if not plan.committed]
                    elif filter.status == "committed":
                        plans_with_pos = [(pos, plan) for pos, plan in plans_with_pos if plan.committed]
                    # 'all' requires no filtering
            else:
                # Default behavior when no filter is provided: show only non-archived plans
                plans_with_pos = [(pos, plan) for pos, plan in plans_with_pos if not plan.is_archived]

            # If using 'last', we need to reverse the results since we got them in ascending order
            if last:
                plans_with_pos.reverse()

            # No plans found
            if not plans_with_pos:
                return MoneyPlanConnection(
                    edges=[],
                    page_info=relay.PageInfo(
                        has_next_page=False,
                        has_previous_page=False,
                        start_cursor=None,
                        end_cursor=None,
                    ),
                )

            # Create edges with cursors based on notification positions
            edges = [
                strawberry.relay.Edge(
                    node=MoneyPlan.from_domain(plan), cursor=strawberry.relay.to_base64("MoneyPlan", str(pos))
                )
                for pos, plan in plans_with_pos
            ]

            # The key insight for pagination is that positions increase as plans are created.
            # But we want to show most recent first, so we display them in reverse order.
            #
            # Therefore:
            # - For 'first': next page means lower positions, previous page means higher positions
            # - For 'last': next page means higher positions, previous page means lower positions
            min_pos = min(pos for pos, _ in plans_with_pos)
            max_pos = max(pos for pos, _ in plans_with_pos)

            if first:
                # When paginating forward with 'first':
                has_next = bool(
                    list(
                        use_case.get_plans(
                            lte=min_pos - 1,  # Look for records with lower positions
                            limit=1,
                            desc=desc,
                        )
                    )
                )
                has_previous = after_pos is not None  # If we used 'after', there must be previous pages
            else:  # last
                # When paginating backward with 'last':
                has_next = bool(
                    list(
                        use_case.get_plans(
                            gt=max_pos,  # Look for records with higher positions
                            limit=1,
                            desc=desc,
                        )
                    )
                )
                has_previous = before_pos is not None  # If we used 'before', there must be previous pages

            page_info = relay.PageInfo(
                has_next_page=has_next,
                has_previous_page=has_previous,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            )

            return MoneyPlanConnection(edges=edges, page_info=page_info)
        except Exception as e:
            logger.error(f"Error fetching money plans: {e}", exc_info=True)
            return MoneyPlanConnection(
                edges=[],
                page_info=relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                ),
            )


# GraphQL mutations
@strawberry.type
class MoneyPlanMutations:
    @strawberry.mutation
    def start_plan(self, info: Info, input: PlanStartInput) -> PlanResult:
        """
        Start a new Money Plan.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            if input.copy_from:
                # Create plan by copying structure from existing plan
                plan_result = use_case.copy_plan_structure(
                    source_plan_id=input.copy_from.node_id,
                    initial_balance=input.initial_balance,
                    notes=input.notes,
                )
                if not plan_result.success:
                    return PlanResult(error=Error(message=plan_result.message), success=False)
                plan_id = plan_result.data
            else:
                # Create plan with provided allocations if any
                default_allocations = None
                if input.default_allocations:
                    default_allocations = [config.to_domain() for config in input.default_allocations]

                plan_result = use_case.create_plan(
                    initial_balance=input.initial_balance,
                    default_allocations=default_allocations,
                    notes=input.notes,
                    plan_date=input.plan_date,
                )

                if not plan_result.success:
                    return PlanResult(error=Error(message=plan_result.message), success=False)
                plan_id = plan_result.data

            get_plan_result = use_case.get_plan(plan_id)
            if not get_plan_result.success:
                return PlanResult(error=Error(message=get_plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(get_plan_result.data), success=True)
        except PlanAlreadyCommittedError as e:
            logger.warning("Cannot create new plan: %s", str(e))
            return PlanResult(error=Error(message=str(e)), success=False)
        except Exception as e:
            logger.error("Error creating plan: %s", str(e), exc_info=True)
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def allocate_funds(self, info: Info, input: AllocateFundsInput) -> PlanResult:
        """
        Allocate funds to a bucket within an account.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            result = use_case.allocate_funds(
                plan_id=input.plan_id,
                account_id=input.account_id,
                bucket_name=input.bucket_name,
                amount=input.amount,
            )

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(input.plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def reverse_allocation(self, info: Info, input: ReverseAllocationInput) -> PlanResult:
        """
        Reverse a previous allocation and apply a corrected amount.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            result = use_case.reverse_allocation(
                plan_id=input.plan_id.node_id,
                account_id=input.account_id.node_id,
                bucket_name=input.bucket_name,
                original_amount=input.original_amount,
                corrected_amount=input.corrected_amount,
            )

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(input.plan_id.node_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def adjust_plan_balance(self, info: Info, input: PlanBalanceAdjustInput) -> PlanResult:
        """
        Adjust the overall plan balance.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        plan_id = input.plan_id.node_id
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            result = use_case.adjust_plan_balance(
                plan_id=plan_id, adjustment=input.adjustment, reason=input.reason
            )

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def change_account_configuration(self, info: Info, input: AccountConfigurationChangeInput) -> PlanResult:
        """
        Change the bucket configuration for an account.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            bucket_configs = [config.to_domain() for config in input.new_bucket_config]
            plan_id = input.plan_id.node_id

            result = use_case.change_account_configuration(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
                new_bucket_config=bucket_configs,
            )

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def add_account(self, info: Info, input: AddAccountInput) -> PlanResult:
        """
        Add an account to a Money Plan.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        plan_id = input.plan_id.node_id
        logger.info(f"Adding account '{input.name}' to plan {plan_id}")
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        buckets = None
        if input.buckets:
            buckets = [bucket.to_domain() for bucket in input.buckets]
            logger.info(f"With buckets: {[b.bucket_name for b in buckets]}")
        else:
            logger.info("No buckets specified, will use default bucket")

        # Call add_account method which now returns UseCaseResult
        account_result = use_case.add_account(plan_id=plan_id, name=input.name, buckets=buckets)

        if not account_result.success:
            logger.error(f"Error adding account: {account_result.message}")
            return PlanResult(error=Error(message=account_result.message), success=False)

        # Get updated plan
        plan_result = use_case.get_plan(plan_id)
        if not plan_result.success:
            logger.error(f"Error retrieving plan: {plan_result.message}")
            return PlanResult(error=Error(message=plan_result.message), success=False)

        logger.info(f"Account created with ID: {account_result.data}")
        logger.info(f"Retrieved updated plan. Account count: {len(plan_result.data.accounts)}")

        return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)

    @strawberry.mutation
    def commit_plan(self, info: Info, input: CommitPlanInput) -> PlanResult:
        """
        Commit a Money Plan.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        plan_id = input.plan_id.node_id

        # Call commit_plan method which now returns UseCaseResult
        commit_result = use_case.commit_plan(plan_id=plan_id)

        if not commit_result.success:
            logger.error(f"Error committing plan: {commit_result.message}")
            return PlanResult(error=Error(message=commit_result.message), success=False)

        # Get updated plan
        plan_result = use_case.get_plan(plan_id)
        if not plan_result.success:
            logger.error(f"Error retrieving plan: {plan_result.message}")
            return PlanResult(error=Error(message=plan_result.message), success=False)

        return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)

    @strawberry.mutation
    def archive_plan(self, info: Info, input: ArchivePlanInput) -> PlanResult:
        """Archive a money plan to prevent further modifications."""
        try:
            use_case = apps.get_app_config("money_plans").money_planner
            use_case.user_id = str(info.context.request.user.id)
            plan_id = input.plan_id.node_id

            archive_result = use_case.archive_plan(plan_id)
            if not archive_result.success:
                return PlanResult(error=Error(message=archive_result.message), success=False)

            # Get updated plan state
            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            logger.error("Error archiving plan: %s", str(e), exc_info=True)
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def remove_account(self, info: Info, input: RemoveAccountInput) -> PlanResult:
        """Remove an account from a Money Plan."""
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            plan_id = input.plan_id.node_id
            remove_result = use_case.remove_account(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
            )

            if not remove_result.success:
                return PlanResult(error=Error(message=remove_result.message), success=False)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            logger.error(f"Error removing account: {e}", exc_info=True)
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def set_account_checked_state(self, info: Info, input: SetAccountCheckedStateInput) -> PlanResult:
        """Set the checked state of an account."""
        use_case = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        use_case.user_id = str(info.context.request.user.id)

        try:
            plan_id = input.plan_id.node_id
            result = use_case.set_account_checked_state(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
                is_checked=input.is_checked,
            )

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            logger.error(f"Error setting account checked state: {e}", exc_info=True)
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def edit_plan_notes(self, info: Info, input: EditPlanNotesInput) -> PlanResult:
        """
        Edit the notes of a plan.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        use_case.user_id = str(info.context.request.user.id)

        try:
            plan_id = input.plan_id.node_id
            result = use_case.edit_plan_notes(plan_id=plan_id, notes=input.notes)

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def edit_account_notes(self, info: Info, input: EditAccountNotesInput) -> PlanResult:
        """
        Edit the notes of an account.
        """
        use_case = apps.get_app_config("money_plans").money_planner
        use_case.user_id = str(info.context.request.user.id)

        try:
            plan_id = input.plan_id.node_id
            result = use_case.edit_account_notes(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
                notes=input.notes,
            )

            if not result.success:
                return PlanResult(error=Error(message=result.message), success=False)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return PlanResult(error=Error(message=plan_result.message), success=False)

            return PlanResult(money_plan=MoneyPlan.from_domain(plan_result.data), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)


@strawberry.type
class Mutation:
    @strawberry.field
    def money_plan(self, info: Info) -> MoneyPlanMutations:
        return MoneyPlanMutations()

    @strawberry.field
    def auth(self, info: Info) -> AuthMutations:
        return AuthMutations()


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
