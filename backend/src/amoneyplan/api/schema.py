import logging
from datetime import date, datetime
from typing import List, Optional, Union

import strawberry
from django.conf import settings
from strawberry import relay
from strawberry.types import Info
from strawberry_django.optimizer import DjangoOptimizerExtension

from amoneyplan.accounts.schema import AuthMutations, AuthQueries
from amoneyplan.common import graphql as graphql_common
from amoneyplan.common.permissions import IsAuthenticated
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    AccountAllocationConfig,
    BucketConfig,
    MoneyPlanError,
    PlanAlreadyCommittedError,
)
from amoneyplan.money_plans.models import Account as OrmAccount
from amoneyplan.money_plans.models import MoneyPlan as OrmMoneyPlan
from amoneyplan.money_plans.models import PlanAccount as OrmPlanAccount
from amoneyplan.money_plans.use_cases import AccountUseCases, MoneyPlanUseCases

logger = logging.getLogger("amoneyplan")


# GraphQL output types
@strawberry.type
class Bucket(relay.Node):
    id: relay.NodeID[str]
    name: str
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
            id=domain_bucket.name,
            name=domain_bucket.name,
            category=domain_bucket.category,
            allocated_amount=domain_bucket.allocated_amount.as_float,
        )
        return bucket


@strawberry.type
class Account(relay.Node):
    """
    Represents a standalone account entity, not connected to a specific plan.
    This is used for the accounts query to list available accounts.
    """

    id: relay.NodeID[str]
    name: str
    notes: str

    @staticmethod
    def from_domain(domain_account) -> "Account":
        """
        Create an Account instance from a domain Account model.
        """
        return Account(
            id=domain_account.id,
            name=domain_account.name,
            notes=domain_account.notes,
        )

    @staticmethod
    def from_orm(orm_account) -> "Account":
        """
        Create an Account instance from an ORM Account model.
        """
        return Account(
            id=str(orm_account.id),
            name=orm_account.name,
            notes=orm_account.notes,
        )


@strawberry.type
class PlanAccount(relay.Node):
    """
    Represents an account within a money plan which has buckets, checked state, and notes.
    """

    id: relay.NodeID[str]
    account: Account
    buckets: List[Bucket]
    is_checked: bool
    notes: str = ""

    @classmethod
    def resolve_node(cls, node_id: str, info: Info) -> Optional["PlanAccount"]:
        # In a real implementation, you would parse the node_id and fetch the account
        # For now, we return None as accounts are always loaded through their parent MoneyPlan
        return None

    @staticmethod
    def from_domain(domain_account, plan_id: str) -> "PlanAccount":
        account = PlanAccount(
            # Explicitly encode the composite string as the node ID
            id=relay.to_base64("PlanAccount", f"{plan_id}:{domain_account.account_id}"),
            account=Account(
                id=domain_account.account_id,
                name=domain_account.name,
                notes=domain_account.notes,
            ),
            buckets=[Bucket.from_domain(bucket) for bucket in domain_account.buckets.values()],
            is_checked=domain_account.is_checked,
            notes=domain_account.notes,
        )
        return account

    @staticmethod
    def from_orm(orm_plan_account: OrmPlanAccount, plan_id: str) -> "PlanAccount":
        """
        Create a PlanAccount instance from an ORM PlanAccount object.
        This method is useful for converting ORM objects to GraphQL types.
        """
        buckets = [
            Bucket(
                id=str(bucket.id),
                name=bucket.name,
                category=bucket.category,
                allocated_amount=float(bucket.allocated_amount),
            )
            for bucket in orm_plan_account.buckets.all()
        ]

        orm_account = orm_plan_account.account
        account = PlanAccount(
            id=relay.to_base64("PlanAccount", f"{plan_id}:{orm_account.id}"),
            account=Account.from_domain(orm_account),
            buckets=buckets,
            is_checked=orm_plan_account.is_checked,
            notes=orm_plan_account.notes,
        )
        return account


@strawberry.type
class MoneyPlan(relay.Node):
    id: relay.NodeID[str]
    initial_balance: float
    remaining_balance: float
    accounts: List[PlanAccount]
    notes: str
    is_committed: bool
    is_archived: bool
    created_at: Optional[str] = None
    plan_date: Optional[str] = None
    archived_at: Optional[str] = None

    @classmethod
    def resolve_node(cls, node_id: str, info: Info) -> Optional["MoneyPlan"]:
        use_case = MoneyPlanUseCases()

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
                PlanAccount(
                    id=relay.to_base64("PlanAccount", f"{domain_plan.id}:{allocation.account.account_id}"),
                    account=Account(
                        id=allocation.account.account_id,
                        name=allocation.name,
                        notes=allocation.account.notes,
                    ),
                    buckets=[Bucket.from_domain(bucket) for bucket in allocation.account.buckets.values()],
                    is_checked=allocation.account.is_checked,
                    notes=allocation.account.notes,
                )
                for allocation in domain_plan.accounts.values()
            ],
            notes=domain_plan.notes,
            is_committed=domain_plan.committed,
            is_archived=domain_plan.is_archived,
            created_at=domain_plan.created_at.isoformat() if domain_plan.created_at else None,
            plan_date=domain_plan.plan_date.isoformat() if domain_plan.plan_date else None,
            archived_at=domain_plan.archived_at.isoformat() if domain_plan.archived_at else None,
        )
        return plan

    @staticmethod
    def from_orm(orm_plan) -> "MoneyPlan":
        """
        Create a MoneyPlan instance from an ORM MoneyPlan object.
        This method is useful for converting ORM objects to GraphQL types.
        """
        # Get accounts for the plan
        accounts = [
            PlanAccount.from_orm(plan_account, orm_plan.id) for plan_account in orm_plan.plan_accounts.all()
        ]

        # Create the MoneyPlan GraphQL type
        plan = MoneyPlan(
            id=orm_plan.id,
            initial_balance=float(orm_plan.initial_balance),
            remaining_balance=float(orm_plan.remaining_balance),
            accounts=accounts,
            notes=orm_plan.notes,
            is_committed=orm_plan.committed,
            is_archived=orm_plan.is_archived,
            created_at=orm_plan.created_at.isoformat() if orm_plan.created_at else None,
            plan_date=orm_plan.plan_date.isoformat() if orm_plan.plan_date else None,
            archived_at=orm_plan.archived_at.isoformat() if orm_plan.archived_at else None,
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
    name: str
    category: str
    allocated_amount: float = 0.0

    def to_domain(self) -> BucketConfig:
        return BucketConfig(
            name=self.name,
            category=self.category,
            allocated_amount=Money(self.allocated_amount),
        )


@strawberry.input
class AccountAllocationConfigInput:
    account_id: Optional[str] = None
    buckets: List[BucketConfigInput]

    def to_domain(self) -> AccountAllocationConfig:
        return AccountAllocationConfig(
            account_id=self.account_id if self.account_id else None,
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
    name: str
    amount: float


@strawberry.input
class PlanBalanceAdjustInput:
    plan_id: relay.GlobalID
    adjustment: float


@strawberry.input
class AccountConfigurationChangeInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID
    new_bucket_config: List[BucketConfigInput]


@strawberry.input
class AddAccountInput:
    plan_id: relay.GlobalID
    account_id: relay.GlobalID
    buckets: List[BucketConfigInput]
    notes: str = ""


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


@strawberry.input
class CreateAccountInput:
    name: str
    notes: str = ""


@strawberry.input
class UpdateAccountInput:
    account_id: relay.GlobalID
    name: str
    notes: str = ""


@strawberry.input
class CreateShareLinkInput:
    plan_id: relay.GlobalID
    expiry_days: int = 14  # Default to 14 days


@strawberry.type
class ShareLinkResponse:
    token: str
    expires_at: datetime
    url: str


@strawberry.type
class AccountQueries:
    @strawberry.field
    def list(self, info: Info) -> List[Account]:
        """
        Get all accounts for the current user.
        """
        if not info.context.request.user.is_authenticated:
            return []

        use_case = AccountUseCases()
        result = use_case.get_all_accounts()

        if result.success:
            return [Account.from_domain(account) for account in result.data]
        return []

    @strawberry.field
    def get(self, info: Info, id: relay.GlobalID) -> Optional[Account]:
        """
        Get an account by ID.
        """
        if not info.context.request.user.is_authenticated:
            return None

        use_case = AccountUseCases()
        result = use_case.get_account(id.node_id)

        if result.success:
            return Account.from_domain(result.data)
        return None


# GraphQL queries
@strawberry.type
class Query(AuthQueries):
    @strawberry.field
    def accounts(self, info: Info) -> List[Account]:
        """
        Get all accounts for the current user. This is useful when adding accounts to a draft plan.
        """
        if not info.context.request.user.is_authenticated:
            return []

        try:
            accounts = []
            for orm_account in OrmAccount.objects.all():
                account = Account(
                    id=str(orm_account.id),
                    name=orm_account.name,
                    notes=orm_account.notes,
                )
                accounts.append(account)
            return accounts
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}", exc_info=True)
            return []

    @strawberry.field
    def draft_money_plan(self, info: Info) -> Optional[MoneyPlan]:
        """
        Get the current draft money plan for the authenticated user.
        Returns None if no draft plan exists.
        """
        if not info.context.request.user.is_authenticated:
            return None

        use_case = MoneyPlanUseCases()
        plan_result = use_case.get_current_plan()

        if plan_result.success and plan_result.has_data():
            return MoneyPlan.from_domain(plan_result.data)
        return None

    @strawberry.field
    def money_plan(self, info: Info, id: Optional[relay.GlobalID] = None) -> Optional[MoneyPlan]:
        """
        Get a Money Plan by ID or the current plan if no ID is provided.
        """
        # Check if user is authenticated
        if not info.context.request.user.is_authenticated:
            return None

        use_case = MoneyPlanUseCases()

        if id:
            plan_id = id.node_id
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
            # Start with all plans for the current user
            queryset = OrmMoneyPlan.objects.all()
            # Apply filters
            if filter:
                queryset = queryset.filter(is_archived=filter.is_archived)

                if filter.status:
                    if filter.status == "draft":
                        queryset = queryset.filter(committed=False)
                    elif filter.status == "committed":
                        queryset = queryset.filter(committed=True)
            else:
                # Default behavior: show non-archived plans
                queryset = queryset.filter(is_archived=False)
            # Order by most recent first by default
            queryset = queryset.order_by("-created_at")
            # Convert cursor strings to created_at timestamps if provided
            after_ts = None if after is None else strawberry.relay.from_base64(after)[1]
            before_ts = None if before is None else strawberry.relay.from_base64(before)[1]
            # Apply cursor-based pagination
            if after_ts is not None:
                # Parse the timestamp and filter
                queryset = queryset.filter(created_at__lt=after_ts)
            if before_ts is not None:
                # Parse the timestamp and filter
                queryset = queryset.filter(created_at__gt=before_ts)
            # Reverse order and limits for 'last' pagination
            if last:
                queryset = queryset.order_by("created_at")
                queryset = queryset[:last]
                plans = list(queryset)
                plans.reverse()  # Reverse back to descending order
            else:
                # Apply first limit if specified
                if first:
                    queryset = queryset[:first]
                plans = list(queryset)
            # No plans found
            if not plans:
                return MoneyPlanConnection(
                    edges=[],
                    page_info=relay.PageInfo(
                        has_next_page=False,
                        has_previous_page=False,
                        start_cursor=None,
                        end_cursor=None,
                    ),
                )
            # Create edges with cursors based on created_at timestamps
            edges = []
            for plan in plans:
                # Convert ORM plan to GraphQL type
                edges.append(
                    strawberry.relay.Edge(
                        node=MoneyPlan.from_orm(plan),
                        cursor=strawberry.relay.to_base64("MoneyPlan", str(plan.created_at)),
                    )
                )
            # Calculate has_next_page and has_previous_page
            if first:
                # Check if there are more plans with older timestamps
                min_date = min(p.created_at for p in plans)
                has_next = OrmMoneyPlan.objects.filter(
                    is_archived=filter.is_archived if filter else False, created_at__lt=min_date
                ).exists()
                has_previous = after_ts is not None
            else:  # last
                # Check if there are more plans with newer timestamps
                max_date = max(p.created_at for p in plans)
                has_previous = OrmMoneyPlan.objects.filter(
                    is_archived=filter.is_archived if filter else False, created_at__gt=max_date
                ).exists()
                has_next = before_ts is not None
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

    @strawberry.field
    def shared_plan(self, info: Info, token: str) -> Optional[MoneyPlan]:
        """Get a shared money plan by token without authentication."""
        use_case = MoneyPlanUseCases()
        logger.info(f"Getting shared plan with token: {token}")
        result = use_case.get_shared_plan(token)

        if result.success and result.has_data():
            return MoneyPlan.from_domain(result.data)
        return None


# GraphQL mutations
@strawberry.type
class MoneyPlanMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_common.gql_error_handler
    def start_plan(self, info: Info, input: PlanStartInput) -> graphql_common.MutationResponse:
        """
        Start a new Money Plan.
        """
        use_case = MoneyPlanUseCases()

        try:
            if input.copy_from:
                # Create plan by copying structure from existing plan
                plan_result = use_case.copy_plan_structure(
                    source_plan_id=input.copy_from.node_id,
                    initial_balance=input.initial_balance,
                    notes=input.notes,
                    plan_date=input.plan_date,
                )
                if not plan_result.success:
                    return graphql_common.ApplicationError(message=plan_result.message)
                plan_id = plan_result.data
            else:
                # Create plan with provided allocations if any
                default_allocations = None
                if input.default_allocations:
                    default_allocations = [config.to_domain() for config in input.default_allocations]

                plan_result = use_case.start_plan(
                    initial_balance=input.initial_balance,
                    default_allocations=default_allocations,
                    notes=input.notes,
                    plan_date=input.plan_date,
                )

                if not plan_result.success:
                    return graphql_common.ApplicationError(message=plan_result.message)
                plan_id = plan_result.data

            get_plan_result = use_case.get_plan(plan_id)

            if not get_plan_result.success:
                return graphql_common.ApplicationError(message=get_plan_result.message)

            # Return a Success response with the moneyPlan data
            return graphql_common.Success.from_node(
                MoneyPlan.from_domain(get_plan_result.data),
                is_message_displayable=True,
                message="Plan created successfully.",
            )
        except PlanAlreadyCommittedError as e:
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def allocate_funds(self, info: Info, input: AllocateFundsInput) -> graphql_common.MutationResponse:
        """
        Allocate funds to a bucket within an account.
        """
        use_case = MoneyPlanUseCases()

        try:
            result = use_case.allocate_funds(
                plan_id=input.plan_id,
                account_id=input.account_id,
                bucket_name=input.name,
                amount=input.amount,
            )

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            plan_result = use_case.get_plan(input.plan_id)
            if not plan_result.success:
                return graphql_common.ApplicationError(message=plan_result.message)

            return graphql_common.Success.from_node(
                MoneyPlan.from_domain(plan_result.data),
                is_message_displayable=True,
                message="Funds allocated successfully.",
            )
        except (MoneyPlanError, ValueError) as e:
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def adjust_plan_balance(
        self, info: Info, input: PlanBalanceAdjustInput
    ) -> graphql_common.MutationResponse:
        """
        Adjust the overall plan balance.
        """
        use_case = MoneyPlanUseCases()
        plan_id = input.plan_id.node_id

        try:
            result = use_case.adjust_plan_balance(plan_id=plan_id, adjustment=input.adjustment)

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            return graphql_common.EmptySuccess(
                is_message_displayable=True,
                message="Plan balance adjusted successfully.",
            )
        except (MoneyPlanError, ValueError) as e:
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def change_account_configuration(
        self, info: Info, input: AccountConfigurationChangeInput
    ) -> graphql_common.MutationResponse:
        """
        Change the bucket configuration for an account.
        """
        use_case = MoneyPlanUseCases()

        try:
            bucket_configs = [config.to_domain() for config in input.new_bucket_config]
            plan_id = input.plan_id.node_id

            result = use_case.change_account_configuration(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
                new_bucket_config=bucket_configs,
            )

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return graphql_common.ApplicationError(message=plan_result.message)

            return graphql_common.Success.from_node(
                MoneyPlan.from_domain(plan_result.data),
                is_message_displayable=True,
                message="Account configuration updated successfully.",
            )
        except (MoneyPlanError, ValueError) as e:
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def add_account(self, info: Info, input: AddAccountInput) -> graphql_common.MutationResponse:
        """
        Add an account to a Money Plan.
        """
        use_case = MoneyPlanUseCases()

        account_id = input.account_id.node_id
        plan_id = input.plan_id.node_id
        logger.info(f"Adding account '{account_id}' to plan {plan_id}")

        buckets = None
        if input.buckets:
            buckets = [bucket.to_domain() for bucket in input.buckets]
            logger.info(f"With buckets: {[b.name for b in buckets]}")
        else:
            logger.info("No buckets specified, will use default bucket")

        try:
            # Check if the plan exists and belongs to the current user first
            try:
                plan_result = use_case.get_plan(plan_id)
                if not plan_result.success:
                    return graphql_common.ApplicationError(message=plan_result.message)
            except (MoneyPlan.DoesNotExist, OrmMoneyPlan.DoesNotExist):
                return graphql_common.ApplicationError(
                    message="Plan not found or you don't have permission to modify it."
                )

            # Call add_account method which now returns UseCaseResult
            account_result = use_case.add_account(
                plan_id=plan_id, account_id=account_id, buckets=buckets, notes=input.notes
            )

            if not account_result.success:
                logger.info(f"Error adding account: {account_result.message}")
                return graphql_common.ApplicationError(
                    message=f"Failed to add account: {account_result.message}"
                )

            try:
                # Query for PlanAccount
                # It's ok to use ORM here, following CQRS pattern
                plan_account = OrmPlanAccount.objects.get(plan_id=plan_id, account_id=account_id)

                return graphql_common.Success.from_node(
                    PlanAccount.from_orm(plan_account, plan_id),
                    is_message_displayable=True,
                    message="Account added successfully.",
                )
            except OrmPlanAccount.DoesNotExist:
                return graphql_common.ApplicationError(message="Failed to retrieve the created account.")
        except MoneyPlanError as e:
            logger.error(f"Money plan error adding account: {e}", exc_info=True)
            return graphql_common.ApplicationError(message=str(e))
        except Exception as e:
            logger.error(f"Error adding account: {e}", exc_info=True)
            return graphql_common.ApplicationError(message=f"An unexpected error occurred: {str(e)}")

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def commit_plan(self, info: Info, input: CommitPlanInput) -> graphql_common.MutationResponse:
        """
        Commit a Money Plan.
        """
        use_case = MoneyPlanUseCases()

        plan_id = input.plan_id.node_id

        # Call commit_plan method which now returns UseCaseResult
        commit_result = use_case.commit_plan(plan_id=plan_id)

        if not commit_result.success:
            logger.info(f"Error committing plan: {commit_result.message}")
            return graphql_common.ApplicationError(message=f"Failed to commit plan: {commit_result.message}")

        return graphql_common.EmptySuccess(
            is_message_displayable=True,
            message="Your money plan was committed",
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def archive_plan(self, info: Info, input: ArchivePlanInput) -> graphql_common.MutationResponse:
        """Archive a money plan to prevent further modifications."""
        try:
            use_case = MoneyPlanUseCases()
            plan_id = input.plan_id.node_id

            archive_result = use_case.archive_plan(plan_id)
            if not archive_result.success:
                return graphql_common.ApplicationError(message=archive_result.message)

            return graphql_common.EmptySuccess(
                is_message_displayable=True,
                message="Plan archived successfully.",
            )
        except (MoneyPlanError, ValueError) as e:
            logger.error("Error archiving plan: %s", str(e), exc_info=True)
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_account(self, info: Info, input: RemoveAccountInput) -> graphql_common.MutationResponse:
        """Remove an account from a Money Plan."""
        use_case = MoneyPlanUseCases()

        try:
            plan_id = input.plan_id.node_id
            remove_result = use_case.remove_account(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
            )

            if not remove_result.success:
                return graphql_common.ApplicationError(message=remove_result.message)

            plan_result = use_case.get_plan(plan_id)
            if not plan_result.success:
                return graphql_common.ApplicationError(message=plan_result.message)

            return graphql_common.Success.from_node(
                MoneyPlan.from_domain(plan_result.data),
                is_message_displayable=True,
                message="Account removed successfully.",
            )
        except (MoneyPlanError, ValueError) as e:
            logger.error(f"Error removing account: {e}", exc_info=True)
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_account_checked_state(
        self, info: Info, input: SetAccountCheckedStateInput
    ) -> graphql_common.MutationResponse:
        """Set the checked state of an account."""
        use_case = MoneyPlanUseCases()

        try:
            plan_id = input.plan_id.node_id
            account_id = input.account_id.node_id

            result = use_case.set_account_checked_state(
                plan_id=plan_id,
                account_id=account_id,
                is_checked=input.is_checked,
            )

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            # Return the updated plan
            return graphql_common.EmptySuccess(
                is_message_displayable=True,
                message="Account checked off" if input.is_checked else "Account unchecked",
            )
        except (MoneyPlanError, ValueError) as e:
            logger.error(f"Error setting account checked state: {e}", exc_info=True)
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def edit_plan_notes(self, info: Info, input: EditPlanNotesInput) -> graphql_common.MutationResponse:
        """
        Edit the notes of a plan.
        """
        use_case = MoneyPlanUseCases()

        try:
            plan_id = input.plan_id.node_id
            result = use_case.edit_plan_notes(plan_id=plan_id, notes=input.notes)

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            return graphql_common.EmptySuccess(
                is_message_displayable=True,
                message="Plan notes updated successfully.",
            )
        except OrmMoneyPlan.DoesNotExist:
            # This happens when a user tries to access a plan that doesn't belong to them
            return graphql_common.ApplicationError(
                message="Plan not found or you don't have permission to modify it."
            )
        except (MoneyPlanError, ValueError) as e:
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def edit_account_notes(self, info: Info, input: EditAccountNotesInput) -> graphql_common.MutationResponse:
        """
        Edit the notes of an account.
        """
        use_case = MoneyPlanUseCases()

        try:
            plan_id = input.plan_id.node_id
            result = use_case.edit_account_notes(
                plan_id=plan_id,
                account_id=input.account_id.node_id,
                notes=input.notes,
            )

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            return graphql_common.EmptySuccess(
                is_message_displayable=True,
                message="Account notes updated successfully.",
            )
        except (MoneyPlanError, ValueError) as e:
            return graphql_common.ApplicationError(message=str(e))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def create_share_link(
        self, info: Info, input: CreateShareLinkInput
    ) -> Union[ShareLinkResponse, graphql_common.ApplicationError]:
        """Create a temporary share link for a plan."""
        if not info.context.request.user.is_authenticated:
            return graphql_common.ApplicationError(message="Authentication required")

        try:
            plan_id = input.plan_id.node_id
            use_case = MoneyPlanUseCases()
            result = use_case.create_share_link(plan_id, input.expiry_days, info.context.request.user)

            if result.success:
                frontend_url = settings.FRONTEND_URL
                return ShareLinkResponse(
                    token=result.data.token,
                    expires_at=result.data.expires_at,
                    url=f"{frontend_url}/shared/{result.data.token}",
                )
            return graphql_common.ApplicationError(message=result.message)
        except Exception as e:
            return graphql_common.ApplicationError(message=str(e))


@strawberry.type
class AccountMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_common.gql_error_handler
    def create(self, info: Info, input: CreateAccountInput) -> graphql_common.MutationResponse:
        """
        Create a new account.
        """
        use_case = AccountUseCases()

        try:
            result = use_case.create_account(
                name=input.name,
                notes=input.notes,
            )

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            return graphql_common.Success.from_node(
                Account.from_domain(result.data),
                is_message_displayable=True,
                message="Account created successfully.",
            )
        except Exception as e:
            logger.error(f"Error creating account: {e}", exc_info=True)
            return graphql_common.ApplicationError(message=str(e))

    # TODO improve naming
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_common.gql_error_handler
    def update(self, info: Info, input: UpdateAccountInput) -> graphql_common.MutationResponse:
        """
        Update an existing account.
        """
        use_case = AccountUseCases()

        try:
            result = use_case.update_account(
                account_id=input.account_id.node_id,
                name=input.name,
                notes=input.notes,
            )

            if not result.success:
                return graphql_common.ApplicationError(message=result.message)

            return graphql_common.Success.from_node(
                Account.from_domain(result.data),
                is_message_displayable=True,
                message="Account updated successfully.",
            )
        except Exception as e:
            logger.error(f"Error updating account: {e}", exc_info=True)
            return graphql_common.ApplicationError(message=str(e))


@strawberry.type
class Mutation:
    @strawberry.field
    def money_plan(self, info: Info) -> MoneyPlanMutations:
        return MoneyPlanMutations()

    @strawberry.field
    def auth(self, info: Info) -> AuthMutations:
        return AuthMutations()

    @strawberry.field
    def account(self, info: Info) -> AccountMutations:
        return AccountMutations()


schema = strawberry.federation.Schema(query=Query, mutation=Mutation, extensions=[DjangoOptimizerExtension])
