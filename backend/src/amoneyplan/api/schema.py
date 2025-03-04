"""
GraphQL schema for the Money Plan API.
"""

import logging
from typing import List, Optional
from uuid import UUID

import strawberry
from django.apps import apps
from strawberry import relay
from strawberry.types import Info

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
    id: relay.NodeID[UUID]
    name: str
    buckets: List[Bucket]

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
        )
        return account


@strawberry.type
class MoneyPlan(relay.Node):
    id: relay.NodeID[UUID]
    initial_balance: float
    remaining_balance: float
    accounts: List[Account]
    notes: str
    is_committed: bool
    timestamp: Optional[str] = None

    @classmethod
    def resolve_node(cls, node_id: str, info: Info) -> Optional["MoneyPlan"]:
        service = apps.get_app_config("money_plans").money_planner
        try:
            plan = service.get_plan(UUID(node_id))
            return MoneyPlan.from_domain(plan)
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
            timestamp=domain_plan.timestamp.isoformat() if domain_plan.timestamp else None,
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
            account_id=UUID(self.account_id) if self.account_id else UUID(),
            account_name=self.name,
            buckets=[bucket.to_domain() for bucket in self.buckets],
        )


@strawberry.input
class PlanStartInput:
    initial_balance: float
    notes: str = ""
    default_allocations: Optional[List[AccountAllocationConfigInput]] = None


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


# GraphQL queries
@strawberry.type
class Query:
    @strawberry.field
    def money_plan(self, info: Info, plan_id: Optional[relay.GlobalID] = None) -> Optional[MoneyPlan]:
        """
        Get a Money Plan by ID or the current plan if no ID is provided.
        """
        service = apps.get_app_config("money_plans").money_planner

        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        if plan_id:
            plan_id = UUID(plan_id.node_id)

            try:
                plan = service.get_plan(plan_id)
                return MoneyPlan.from_domain(plan)
            except (KeyError, ValueError):
                return None
        else:
            plan = service.get_current_plan()
            if plan:
                return MoneyPlan.from_domain(plan)
            return None

    @strawberry.field
    def money_plans(
        self,
        info: Info,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
    ) -> MoneyPlanConnection:
        """
        List all Money Plans with pagination support.
        """
        try:
            service = apps.get_app_config("money_plans").money_planner
            # Set user ID from request context
            service.user_id = str(info.context.request.user.id)

            plan_ids = service.list_plans()
            plans = []

            for plan_id in plan_ids:
                try:
                    plan = service.get_plan(plan_id)
                    plans.append(MoneyPlan.from_domain(plan))
                except KeyError:
                    logger.warning(f"Plan {plan_id} not found")
                    continue

            # Handle pagination
            if after:
                after_index = next(
                    (
                        i
                        for i, plan in enumerate(plans)
                        if str(plan.id) == strawberry.relay.from_base64(after)[1]
                    ),
                    0,
                )
                plans = plans[after_index + 1 :]

            if before:
                before_index = next(
                    (
                        i
                        for i, plan in enumerate(plans)
                        if str(plan.id) == strawberry.relay.from_base64(before)[1]
                    ),
                    len(plans),
                )
                plans = plans[:before_index]

            if first:
                plans = plans[:first]
            elif last:
                plans = plans[-last:]

            has_next_page = False
            has_previous_page = False

            if first and len(plans) == first:
                has_next_page = True
            if last and len(plans) == last:
                has_previous_page = True

            edges = [
                strawberry.relay.Edge(node=plan, cursor=strawberry.relay.to_base64("MoneyPlan", str(plan.id)))
                for plan in plans
            ]

            page_info = relay.PageInfo(
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            )

            return MoneyPlanConnection(edges=edges, page_info=page_info)
        except Exception as e:
            logger.error(f"Error fetching money plans: {e}", exc_info=True)
            # Return an empty connection instead of raising the error
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
        service = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            default_allocations = None
            if input.default_allocations:
                default_allocations = [config.to_domain() for config in input.default_allocations]

            plan_id = service.create_plan(
                initial_balance=input.initial_balance,
                default_allocations=default_allocations,
                notes=input.notes,
            )

            plan = service.get_plan(plan_id)
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
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
        service = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            service.allocate_funds(
                plan_id=UUID(input.plan_id),
                account_id=input.account_id,
                bucket_name=input.bucket_name,
                amount=input.amount,
            )

            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def reverse_allocation(self, info: Info, input: ReverseAllocationInput) -> PlanResult:
        """
        Reverse a previous allocation and apply a corrected amount.
        """
        service = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            service.reverse_allocation(
                plan_id=UUID(input.plan_id),
                account_id=input.account_id,
                bucket_name=input.bucket_name,
                original_amount=input.original_amount,
                corrected_amount=input.corrected_amount,
            )

            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def adjust_plan_balance(self, info: Info, input: PlanBalanceAdjustInput) -> PlanResult:
        """
        Adjust the overall plan balance.
        """
        service = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            service.adjust_plan_balance(
                plan_id=UUID(input.plan_id), adjustment=input.adjustment, reason=input.reason
            )

            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def change_account_configuration(self, info: Info, input: AccountConfigurationChangeInput) -> PlanResult:
        """
        Change the bucket configuration for an account.
        """
        service = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            bucket_configs = [config.to_domain() for config in input.new_bucket_config]

            service.change_account_configuration(
                plan_id=UUID(input.plan_id),
                account_id=input.account_id,
                new_bucket_config=bucket_configs,
            )

            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def add_account(self, info: Info, input: AddAccountInput) -> PlanResult:
        """
        Add an account to a Money Plan.
        """
        service = apps.get_app_config("money_plans").money_planner
        plan_id = UUID(input.plan_id.node_id)
        logger.info(f"Adding account '{input.name}' to plan {plan_id}")
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            buckets = None
            if input.buckets:
                buckets = [bucket.to_domain() for bucket in input.buckets]
                logger.info(f"With buckets: {[b.bucket_name for b in buckets]}")
            else:
                logger.info("No buckets specified, will use default bucket")

            account_id = service.add_account(plan_id=plan_id, name=input.name, buckets=buckets)
            logger.info(f"Account created with ID: {account_id}")

            plan = service.get_plan(plan_id)
            logger.info(f"Retrieved updated plan. Account count: {len(plan.accounts)}")
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
        except (MoneyPlanError, ValueError) as e:
            logger.error(f"Error adding account: {e}", exc_info=True)
            return PlanResult(error=Error(message=str(e)), success=False)

    @strawberry.mutation
    def commit_plan(self, info: Info, input: CommitPlanInput) -> PlanResult:
        """
        Commit a Money Plan.
        """
        service = apps.get_app_config("money_plans").money_planner
        # Set user ID from request context
        service.user_id = str(info.context.request.user.id)

        try:
            plan_id = UUID(input.plan_id.node_id)
            service.commit_plan(plan_id=plan_id)

            plan = service.get_plan(plan_id)
            return PlanResult(money_plan=MoneyPlan.from_domain(plan), success=True)
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(error=Error(message=str(e)), success=False)


@strawberry.type
class Mutation:
    @strawberry.field
    def money_plan(self, info: Info) -> MoneyPlanMutations:
        return MoneyPlanMutations()


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
