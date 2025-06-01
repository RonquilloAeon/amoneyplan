import logging
from datetime import date
from typing import List, Optional

from django.db import transaction

from amoneyplan.accounts.tenancy import get_current_account
from amoneyplan.domain.account import Account as DomainAccount
from amoneyplan.domain.money import Money
from amoneyplan.domain.money_plan import (
    Bucket as DomainBucket,
)
from amoneyplan.domain.money_plan import (
    MoneyPlan as DomainMoneyPlan,
)
from amoneyplan.domain.money_plan import (
    PlanAccount as DomainPlanAccount,
)
from amoneyplan.domain.money_plan import (
    PlanAccountAllocation,
)

from .models import Account, Bucket, MoneyPlan, PlanAccount

logger = logging.getLogger("django")


class AccountRepository:
    """Repository for Account entity."""

    def get_by_id(self, account_id: str) -> Optional[DomainAccount]:
        """
        Get an account by ID and user account.

        Args:
            account_id: The ID of the account to retrieve

        Returns:
            Domain model instance of the account or None if not found
        """
        try:
            orm_account = Account.objects.get(id=account_id)
            return self._to_domain(orm_account)
        except Account.DoesNotExist:
            return None

    def get_all(self) -> List[DomainAccount]:
        """
        Get all accounts for the current user account.

        Returns:
            List of domain model instances of accounts
        """
        orm_accounts = Account.objects.all()
        return [self._to_domain(account) for account in orm_accounts]

    @transaction.atomic
    def save(self, account: DomainAccount) -> None:
        """
        Save a domain account to the database.

        Args:
            account: Domain account object to save
        """
        # Find or create the Django model instance
        try:
            orm_account = Account.objects.get(id=account.id)
        except Account.DoesNotExist:
            orm_account = None

        # Convert domain model to ORM model
        orm_account = self._from_domain(account, orm_account)

        # Save the model
        orm_account.save()

    def _to_domain(self, orm_account: Account) -> DomainAccount:
        """Convert an ORM account to a domain account."""
        return DomainAccount(
            id=orm_account.id,
            name=orm_account.name,
            notes=orm_account.notes if hasattr(orm_account, "notes") else "",
        )

    def _from_domain(self, domain_account: DomainAccount, orm_account: Optional[Account] = None) -> Account:
        """Convert a domain account to an ORM account."""
        if not orm_account:
            orm_account = Account(
                id=domain_account.id,
                user_account=get_current_account(),
            )

        orm_account.name = domain_account.name
        if hasattr(orm_account, "notes"):
            orm_account.notes = domain_account.notes

        return orm_account


# Add domain adapter functions to convert between Django models and domain objects
def to_domain_bucket(bucket: Bucket) -> DomainBucket:
    """Convert a Django Bucket model to a domain Bucket object."""
    return DomainBucket(
        name=bucket.name, category=bucket.category, allocated_amount=Money(bucket.allocated_amount)
    )


def to_domain_plan_account(
    account: Account, plan_account: PlanAccount, buckets: List[Bucket]
) -> DomainPlanAccount:
    """Convert Django Account and PlanAccount models to a domain Account object."""
    domain_plan_account = DomainPlanAccount(
        account_id=account.id,
        buckets={},
        is_checked=plan_account.is_checked,
        notes=plan_account.notes,
    )

    # Add buckets
    for bucket in buckets:
        domain_bucket = to_domain_bucket(bucket)
        domain_plan_account.buckets[domain_bucket.name] = domain_bucket

    return domain_plan_account


def to_domain_plan_account_allocation(plan_account: PlanAccount) -> PlanAccountAllocation:
    """Convert a Django PlanAccount model to a domain PlanAccountAllocation object."""
    buckets = plan_account.buckets.all().order_by("created_at")
    account = plan_account.account

    domain_account = to_domain_plan_account(account, plan_account, buckets)
    return PlanAccountAllocation(account=domain_account, name=account.name)


def to_domain_money_plan(plan: MoneyPlan) -> DomainMoneyPlan:
    """
    Convert a Django MoneyPlan model to a domain MoneyPlan object.
    This adapter function maintains compatibility with the existing GraphQL schema
    that expects a MoneyPlan object with the eventsourcing structure.
    """

    # Convert accounts and buckets
    accounts = {}

    for plan_account in (
        plan.plan_accounts.all().order_by("created_at").select_related("account").prefetch_related("buckets")
    ):
        account_id = plan_account.account.id
        accounts[account_id] = to_domain_plan_account_allocation(plan_account)

    return DomainMoneyPlan(
        id=plan.id,
        initial_balance=Money(plan.initial_balance),
        remaining_balance=Money(plan.remaining_balance),
        notes=plan.notes,
        committed=plan.committed,
        is_archived=plan.is_archived,
        created_at=plan.created_at,
        plan_date=plan.plan_date,
        archived_at=plan.archived_at,
        accounts=accounts,
    )


def from_domain_money_plan(domain_plan: DomainMoneyPlan, orm_plan: Optional[MoneyPlan] = None) -> MoneyPlan:
    """
    Convert a domain MoneyPlan object to a Django MoneyPlan model.
    If an existing ORM plan is provided, it will be updated.

    Args:
        domain_plan: The domain money plan to convert
        orm_plan: Optional existing ORM plan to update

    Returns:
        Updated or new Django MoneyPlan model
    """
    logger.info("Saving plan %s", domain_plan.id)

    if orm_plan is None:
        # Create new model
        orm_plan = MoneyPlan(
            id=domain_plan.id,
            user_account=get_current_account(),
            initial_balance=domain_plan.initial_balance.as_decimal,
            remaining_balance=domain_plan.remaining_balance.as_decimal,
            notes=domain_plan.notes,
            plan_date=domain_plan.plan_date,
            committed=domain_plan.committed,
            is_archived=domain_plan.is_archived,
            created_at=domain_plan.created_at,
            archived_at=domain_plan.archived_at,
        )
    else:
        # Update existing model
        orm_plan.initial_balance = domain_plan.initial_balance.as_decimal
        orm_plan.remaining_balance = domain_plan.remaining_balance.as_decimal
        orm_plan.notes = domain_plan.notes
        orm_plan.committed = domain_plan.committed
        orm_plan.is_archived = domain_plan.is_archived
        orm_plan.archived_at = domain_plan.archived_at

    return orm_plan


class MoneyPlanRepository:
    """Repository for MoneyPlan entity."""

    def get_by_id(self, plan_id, scoped: bool = True) -> DomainMoneyPlan:
        """
        Get a money plan by ID and user account.

        Returns:
            Domain model instance of the money plan

        Raises:
            MoneyPlan.DoesNotExist: If the plan doesn't exist or doesn't belong to the current user
        """
        if scoped:
            orm_plan = MoneyPlan.objects.get(id=plan_id)
        else:
            orm_plan = MoneyPlan.unscoped.get(id=plan_id)
        return to_domain_money_plan(orm_plan)

    def get_current_plan(self) -> Optional[DomainMoneyPlan]:
        """
        Get the current uncommitted and not archived plan for a user.

        Returns:
            Domain model instance of the current plan or None if no current plan exists
        """
        orm_plan = (
            MoneyPlan.objects.filter(
                committed=False,
                is_archived=False,
            )
            .order_by("-created_at")
            .first()
        )

        if orm_plan:
            return to_domain_money_plan(orm_plan)
        return None

    @transaction.atomic
    def save(self, money_plan: DomainMoneyPlan) -> None:
        """
        Save a domain money plan to the database.

        Args:
            money_plan: Domain money plan object to save
        """
        # Find or create the Django model instance
        try:
            orm_plan = MoneyPlan.objects.get(id=money_plan.id)
        except MoneyPlan.DoesNotExist:
            orm_plan = None

        # Convert domain model to ORM model
        orm_plan = from_domain_money_plan(money_plan, orm_plan)

        # Save the model
        orm_plan.save()

        # Update accounts and buckets
        self._sync_accounts_and_buckets(money_plan, orm_plan)

    def _sync_accounts_and_buckets(self, domain_plan: DomainMoneyPlan, orm_plan: MoneyPlan) -> None:
        """
        Synchronize accounts and buckets between domain model and ORM model.
        This handles creating, updating, and deleting accounts and buckets
        based on the domain model state.

        Args:
            domain_plan: The domain money plan
            orm_plan: The ORM money plan
        """
        # Get existing plan accounts from ORM
        existing_plan_accounts = {
            str(pa.account.id): pa for pa in orm_plan.plan_accounts.all().select_related("account")
        }

        # Process accounts in domain model
        for account_id, allocation in domain_plan.accounts.items():
            domain_plan_account = allocation.account

            # Find or create account and plan_account
            if account_id in existing_plan_accounts:
                # Update existing plan account
                plan_account = existing_plan_accounts[account_id]
                plan_account.is_checked = domain_plan_account.is_checked
                plan_account.notes = domain_plan_account.notes
                plan_account.save()
            else:
                account = Account.objects.get(id=account_id)

                # Create plan account
                plan_account = PlanAccount(
                    plan=orm_plan,
                    account=account,
                    user_account=get_current_account(),
                    is_checked=domain_plan_account.is_checked,
                    notes=domain_plan_account.notes,
                )
                plan_account.save()

            # Process buckets for this account
            self._sync_buckets(domain_plan_account, plan_account)

        # Remove plan accounts that are no longer in the domain model
        domain_account_ids = set(domain_plan.accounts.keys())
        for account_id, plan_account in existing_plan_accounts.items():
            if account_id not in domain_account_ids:
                # Delete the plan account
                plan_account.delete()  # This will cascade and delete associated buckets

    def _sync_buckets(self, domain_account: DomainAccount, plan_account: PlanAccount) -> None:
        """
        Synchronize buckets between a domain account and ORM plan account.

        Args:
            domain_account: The domain account
            plan_account: The ORM plan account
        """
        # Get existing buckets from ORM
        existing_buckets = {bucket.name: bucket for bucket in plan_account.buckets.all()}

        # Process buckets in domain account
        for bucket_name, domain_bucket in domain_account.buckets.items():
            if bucket_name in existing_buckets:
                # Update existing bucket
                bucket = existing_buckets[bucket_name]
                bucket.category = domain_bucket.category
                bucket.allocated_amount = domain_bucket.allocated_amount.as_decimal
                bucket.save()
            else:
                # Create new bucket
                bucket = Bucket(
                    plan_account=plan_account,
                    user_account=get_current_account(),
                    name=domain_bucket.name,
                    category=domain_bucket.category,
                    allocated_amount=domain_bucket.allocated_amount.as_decimal,
                )
                bucket.save()

        # Remove buckets that are no longer in the domain account
        domain_bucket_names = set(domain_account.buckets.keys())
        for bucket_name, bucket in existing_buckets.items():
            if bucket_name not in domain_bucket_names:
                bucket.delete()

    @transaction.atomic
    def create(
        self, initial_balance: float, notes: str = "", plan_date: Optional[date] = None
    ) -> DomainMoneyPlan:
        """
        Create a new money plan domain model and persist it to database.

        Args:
            initial_balance: Initial balance for the plan
            notes: Optional notes
            plan_date: Optional plan date

        Returns:
            The created domain money plan
        """
        # Create ORM model first
        orm_plan = MoneyPlan(
            user_account=get_current_account(),
            initial_balance=initial_balance,
            remaining_balance=initial_balance,
            notes=notes,
            plan_date=plan_date or date.today(),
        )
        orm_plan.save()

        # Convert to domain model and return
        return to_domain_money_plan(orm_plan)
