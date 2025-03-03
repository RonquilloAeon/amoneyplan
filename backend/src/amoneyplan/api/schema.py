"""
GraphQL schema for the Money Plan API.
"""
import decimal
from typing import List, Optional, Dict, Union
from uuid import UUID

import strawberry
from django.apps import apps
from strawberry.types import Info

from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    BucketConfig, 
    AccountAllocationConfig,
    MoneyPlanError,
    InsufficientFundsError,
    PlanAlreadyCommittedError,
    BucketNotFoundError,
    AccountNotFoundError,
    InvalidPlanStateError
)


# GraphQL output types
@strawberry.type
class Bucket:
    bucket_name: str
    category: str
    allocated_amount: float

    @staticmethod
    def from_domain(domain_bucket) -> "Bucket":
        return Bucket(
            bucket_name=domain_bucket.bucket_name,
            category=domain_bucket.category,
            allocated_amount=domain_bucket.allocated_amount.as_float
        )


@strawberry.type
class Account:
    account_id: str
    account_name: str
    buckets: List[Bucket]

    @staticmethod
    def from_domain(domain_account) -> "Account":
        return Account(
            account_id=str(domain_account.account_id),
            account_name=domain_account.account_name,
            buckets=[
                Bucket.from_domain(bucket) for bucket in domain_account.buckets.values()
            ]
        )


@strawberry.type
class MoneyPlan:
    id: str
    initial_balance: float
    remaining_balance: float
    accounts: List[Account]
    notes: str
    committed: bool
    timestamp: Optional[str] = None

    @staticmethod
    def from_domain(domain_plan) -> "MoneyPlan":
        return MoneyPlan(
            id=str(domain_plan.id),
            initial_balance=domain_plan.initial_balance.as_float,
            remaining_balance=domain_plan.remaining_balance.as_float,
            accounts=[
                Account.from_domain(allocation.account) 
                for allocation in domain_plan.accounts.values()
            ],
            notes=domain_plan.notes,
            committed=domain_plan.committed,
            timestamp=domain_plan.timestamp.isoformat() if domain_plan.timestamp else None
        )


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
            allocated_amount=Money(self.allocated_amount)
        )


@strawberry.input
class AccountAllocationConfigInput:
    account_id: Optional[str] = None
    account_name: str
    buckets: List[BucketConfigInput]

    def to_domain(self) -> AccountAllocationConfig:
        return AccountAllocationConfig(
            account_id=UUID(self.account_id) if self.account_id else UUID(),
            account_name=self.account_name,
            buckets=[bucket.to_domain() for bucket in self.buckets]
        )


@strawberry.input
class PlanStartInput:
    initial_balance: float
    notes: str = ""
    default_allocations: Optional[List[AccountAllocationConfigInput]] = None


@strawberry.input
class AllocateFundsInput:
    plan_id: str
    account_id: str
    bucket_name: str
    amount: float


@strawberry.input
class ReverseAllocationInput:
    plan_id: str
    account_id: str
    bucket_name: str
    original_amount: float
    corrected_amount: float


@strawberry.input
class PlanBalanceAdjustInput:
    plan_id: str
    adjustment: float
    reason: str = ""


@strawberry.input
class AccountConfigurationChangeInput:
    plan_id: str
    account_id: str
    new_bucket_config: List[BucketConfigInput]


@strawberry.input
class AddAccountInput:
    plan_id: str
    account_name: str
    buckets: Optional[List[BucketConfigInput]] = None


@strawberry.input
class CommitPlanInput:
    plan_id: str


# GraphQL queries
@strawberry.type
class Query:
    @strawberry.field
    def money_plan(self, info: Info, plan_id: Optional[str] = None) -> Optional[MoneyPlan]:
        """
        Get a Money Plan by ID or the current plan if no ID is provided.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        if plan_id:
            try:
                plan = service.get_plan(UUID(plan_id))
                return MoneyPlan.from_domain(plan)
            except (KeyError, ValueError):
                return None
        else:
            plan = service.get_current_plan()
            if plan:
                return MoneyPlan.from_domain(plan)
            return None

    @strawberry.field
    def money_plans(self, info: Info) -> List[MoneyPlan]:
        """
        List all Money Plans.
        """
        service = apps.get_app_config("money_plans").money_planner
        plan_ids = service.list_plans()
        
        plans = []
        for plan_id in plan_ids:
            try:
                plan = service.get_plan(plan_id)
                plans.append(MoneyPlan.from_domain(plan))
            except KeyError:
                continue
                
        return plans


# GraphQL mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    def start_plan(self, info: Info, input: PlanStartInput) -> PlanResult:
        """
        Start a new Money Plan.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            default_allocations = None
            if input.default_allocations:
                default_allocations = [
                    config.to_domain() for config in input.default_allocations
                ]
                
            plan_id = service.create_plan(
                initial_balance=input.initial_balance,
                default_allocations=default_allocations,
                notes=input.notes
            )
            
            plan = service.get_plan(plan_id)
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except Exception as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )

    @strawberry.mutation
    def allocate_funds(self, info: Info, input: AllocateFundsInput) -> PlanResult:
        """
        Allocate funds to a bucket within an account.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            service.allocate_funds(
                plan_id=UUID(input.plan_id),
                account_id=input.account_id,
                bucket_name=input.bucket_name,
                amount=input.amount
            )
            
            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )

    @strawberry.mutation
    def reverse_allocation(self, info: Info, input: ReverseAllocationInput) -> PlanResult:
        """
        Reverse a previous allocation and apply a corrected amount.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            service.reverse_allocation(
                plan_id=UUID(input.plan_id),
                account_id=input.account_id,
                bucket_name=input.bucket_name,
                original_amount=input.original_amount,
                corrected_amount=input.corrected_amount
            )
            
            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )

    @strawberry.mutation
    def adjust_plan_balance(self, info: Info, input: PlanBalanceAdjustInput) -> PlanResult:
        """
        Adjust the overall plan balance.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            service.adjust_plan_balance(
                plan_id=UUID(input.plan_id),
                adjustment=input.adjustment,
                reason=input.reason
            )
            
            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )

    @strawberry.mutation
    def change_account_configuration(self, info: Info, input: AccountConfigurationChangeInput) -> PlanResult:
        """
        Change the bucket configuration for an account.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            bucket_configs = [config.to_domain() for config in input.new_bucket_config]
            
            service.change_account_configuration(
                plan_id=UUID(input.plan_id),
                account_id=input.account_id,
                new_bucket_config=bucket_configs
            )
            
            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )

    @strawberry.mutation
    def add_account(self, info: Info, input: AddAccountInput) -> PlanResult:
        """
        Add an account to a Money Plan.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            buckets = None
            if input.buckets:
                buckets = [bucket.to_domain() for bucket in input.buckets]
                
            account_id = service.add_account(
                plan_id=UUID(input.plan_id),
                account_name=input.account_name,
                buckets=buckets
            )
            
            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )

    @strawberry.mutation
    def commit_plan(self, info: Info, input: CommitPlanInput) -> PlanResult:
        """
        Commit a Money Plan.
        """
        service = apps.get_app_config("money_plans").money_planner
        
        try:
            service.commit_plan(plan_id=UUID(input.plan_id))
            
            plan = service.get_plan(UUID(input.plan_id))
            return PlanResult(
                money_plan=MoneyPlan.from_domain(plan),
                success=True
            )
        except (MoneyPlanError, ValueError) as e:
            return PlanResult(
                error=Error(message=str(e)),
                success=False
            )


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
