"""
Repository classes for the Money Plan app.
"""

import uuid
from datetime import date
from typing import Iterator, List, Optional, Tuple

from django.db import transaction
from django.db.models import QuerySet

from amoneyplan.domain.account import Account as DomainAccount
from amoneyplan.domain.account import Bucket as DomainBucket
from amoneyplan.domain.account import PlanAccountAllocation
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import MoneyPlan as DomainMoneyPlan

from .models import Account, Bucket, MoneyPlan, PlanAccount


# Add domain adapter functions to convert between Django models and domain objects
def to_domain_bucket(bucket: Bucket) -> DomainBucket:
    """Convert a Django Bucket model to a domain Bucket object."""
    return DomainBucket(
        bucket_name=bucket.name, category=bucket.category, allocated_amount=Money(bucket.allocated_amount)
    )


def to_domain_account(account: Account, plan_account: PlanAccount, buckets: List[Bucket]) -> DomainAccount:
    """Convert Django Account and PlanAccount models to a domain Account object."""
    domain_account = DomainAccount(
        account_id=account.id,
        name=account.name,
        is_checked=plan_account.is_checked,
        notes=plan_account.notes,
        buckets={},
    )

    # Add buckets
    for bucket in buckets:
        domain_bucket = to_domain_bucket(bucket)
        domain_account.buckets[domain_bucket.bucket_name] = domain_bucket

    return domain_account


def to_domain_plan_account_allocation(plan_account: PlanAccount) -> PlanAccountAllocation:
    """Convert a Django PlanAccount model to a domain PlanAccountAllocation object."""
    buckets = plan_account.buckets.all()
    account = plan_account.account

    domain_account = to_domain_account(account, plan_account, buckets)
    return PlanAccountAllocation(account=domain_account)


def to_domain_money_plan(plan: MoneyPlan) -> DomainMoneyPlan:
    """
    Convert a Django MoneyPlan model to a domain MoneyPlan object.
    This adapter function maintains compatibility with the existing GraphQL schema
    that expects a MoneyPlan object with the eventsourcing structure.
    """
    # Create a domain money plan with initial properties
    domain_plan = DomainMoneyPlan.__new__(DomainMoneyPlan)
    domain_plan._id = plan.id
    domain_plan.initial_balance = Money(plan.initial_balance)
    domain_plan.remaining_balance = Money(plan.remaining_balance)
    domain_plan.notes = plan.notes
    domain_plan.committed = plan.committed
    domain_plan.is_archived = plan.is_archived
    domain_plan.created_at = plan.created_at
    domain_plan.plan_date = plan.plan_date
    domain_plan.archived_at = plan.archived_at

    # Convert accounts and buckets
    domain_plan.accounts = {}

    for plan_account in plan.plan_accounts.all().select_related("account").prefetch_related("buckets"):
        account_id = plan_account.account.id
        domain_plan.accounts[account_id] = to_domain_plan_account_allocation(plan_account)

    return domain_plan


class MoneyPlanRepository:
    """Repository for MoneyPlan entity."""

    def get_by_id(self, plan_id: uuid.UUID, user_id: str) -> MoneyPlan:
        """Get a money plan by ID and user ID."""
        return MoneyPlan.objects.get(id=plan_id, owner_id=user_id)

    def get_current_plan(self, user_id: str) -> Optional[MoneyPlan]:
        """Get the current uncommitted and not archived plan for a user."""
        return (
            MoneyPlan.objects.filter(owner_id=user_id, committed=False, is_archived=False)
            .order_by("-created_at")
            .first()
        )

    @transaction.atomic
    def save(self, money_plan: MoneyPlan) -> None:
        """Save a money plan."""
        money_plan.save()

    @transaction.atomic
    def create(
        self, initial_balance: float, owner_id: str, notes: str = "", plan_date: Optional[date] = None
    ) -> MoneyPlan:
        """Create a new money plan."""
        plan = MoneyPlan(
            id=uuid.uuid4(),
            initial_balance=initial_balance,
            remaining_balance=initial_balance,
            notes=notes,
            plan_date=plan_date or date.today(),
            owner_id=owner_id,
        )
        plan.save()
        return plan

    def list_plans(
        self, user_id: str, is_archived: bool = False, limit: Optional[int] = None, desc: bool = True
    ) -> QuerySet:
        """List money plans for a user."""
        query = MoneyPlan.objects.filter(owner_id=user_id, is_archived=is_archived)
        if desc:
            query = query.order_by("-created_at")
        else:
            query = query.order_by("created_at")

        if limit:
            query = query[:limit]

        return query

    def get_plans_paginated(
        self,
        user_id: str,
        gt_id: Optional[uuid.UUID] = None,
        lte_id: Optional[uuid.UUID] = None,
        desc: bool = True,
        limit: Optional[int] = None,
    ) -> Iterator[Tuple[int, MoneyPlan]]:
        """
        Get paginated money plans for position-based pagination.
        Returns tuples of (position, plan) where position can be used as a cursor.
        """
        # Base query
        query = MoneyPlan.objects.filter(owner_id=user_id)

        # Apply pagination filters
        if gt_id:
            # Find the creation time of the reference plan
            ref_time = MoneyPlan.objects.get(id=gt_id).created_at
            if desc:
                query = query.filter(created_at__lt=ref_time)
            else:
                query = query.filter(created_at__gt=ref_time)

        if lte_id:
            # Find the creation time of the reference plan
            ref_time = MoneyPlan.objects.get(id=lte_id).created_at
            if desc:
                query = query.filter(created_at__gte=ref_time)
            else:
                query = query.filter(created_at__lte=ref_time)

        # Apply sorting
        query = query.order_by("-created_at" if desc else "created_at")

        # Apply limit
        if limit:
            query = query[:limit]

        # Generate positions for the plans
        position = 0
        for plan in query:
            position += 1
            yield position, plan


class AccountRepository:
    """Repository for Account entity."""

    def get_by_id(self, account_id: uuid.UUID, user_id: str) -> Account:
        """Get an account by ID and user ID."""
        return Account.objects.get(id=account_id, owner_id=user_id)

    def find_by_name(self, name: str, user_id: str) -> Optional[Account]:
        """Find an account by name and user ID."""
        return Account.objects.filter(name=name, owner_id=user_id).first()

    def get_or_create(self, name: str, user_id: str) -> Tuple[Account, bool]:
        """Get or create an account."""
        return Account.objects.get_or_create(name=name, owner_id=user_id, defaults={"id": uuid.uuid4()})

    @transaction.atomic
    def save(self, account: Account) -> None:
        """Save an account."""
        account.save()


class PlanAccountRepository:
    """Repository for PlanAccount entity."""

    def get_by_id(self, plan_account_id: uuid.UUID) -> PlanAccount:
        """Get a plan account by ID."""
        return PlanAccount.objects.get(id=plan_account_id)

    def find_by_account_and_plan(self, account_id: uuid.UUID, plan_id: uuid.UUID) -> Optional[PlanAccount]:
        """Find a plan account by account ID and plan ID."""
        return PlanAccount.objects.filter(account_id=account_id, plan_id=plan_id).first()

    @transaction.atomic
    def create(self, plan_id: uuid.UUID, account_id: uuid.UUID) -> PlanAccount:
        """Create a new plan account."""
        plan_account = PlanAccount(id=uuid.uuid4(), plan_id=plan_id, account_id=account_id)
        plan_account.save()
        return plan_account

    @transaction.atomic
    def save(self, plan_account: PlanAccount) -> None:
        """Save a plan account."""
        plan_account.save()


class BucketRepository:
    """Repository for Bucket entity."""

    def get_by_id(self, bucket_id: uuid.UUID) -> Bucket:
        """Get a bucket by ID."""
        return Bucket.objects.get(id=bucket_id)

    def find_by_name_and_plan_account(self, name: str, plan_account_id: uuid.UUID) -> Optional[Bucket]:
        """Find a bucket by name and plan account ID."""
        return Bucket.objects.filter(name=name, plan_account_id=plan_account_id).first()

    @transaction.atomic
    def create(
        self, plan_account_id: uuid.UUID, name: str, category: str, allocated_amount: float = 0
    ) -> Bucket:
        """Create a new bucket."""
        bucket = Bucket(
            id=uuid.uuid4(),
            plan_account_id=plan_account_id,
            name=name,
            category=category,
            allocated_amount=allocated_amount,
        )
        bucket.save()
        return bucket

    @transaction.atomic
    def save(self, bucket: Bucket) -> None:
        """Save a bucket."""
        bucket.save()
