"""
Django ORM models for the Money Plan app.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from amoneyplan.accounts.models import TenantScopedModel
from amoneyplan.common.models import BaseModel
from amoneyplan.common.time import get_utc_now


class Account(TenantScopedModel):
    """Account entity that can be shared across money plans."""

    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["user_account", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_moneyplan_account",
            )
        ]

    def __str__(self):
        return self.name


class MoneyPlan(TenantScopedModel):
    """Money Plan entity."""

    initial_balance = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    plan_date = models.DateField()
    committed = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "Committed" if self.committed else "Draft"
        archived = " (Archived)" if self.is_archived else ""
        return f"Plan {self.plan_date} - {status}{archived}"


class PlanShareLink(TenantScopedModel):
    """Temporary share link for a money plan."""

    plan = models.ForeignKey(MoneyPlan, on_delete=models.CASCADE, related_name="share_links")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def is_valid(self):
        """Check if the link is still valid."""
        return self.expires_at > get_utc_now()

    def __str__(self):
        return f"Share link for {self.plan} (expires: {self.expires_at})"


class PlanAccount(TenantScopedModel):
    """Account allocation within a money plan."""

    plan = models.ForeignKey(MoneyPlan, on_delete=models.CASCADE, related_name="plan_accounts")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="plan_allocations")
    is_checked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "account"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_plan_account",
            )
        ]

    def __str__(self):
        return f"{self.account.name} in {self.plan}"

    def get_total_allocated(self):
        """Calculate the total amount allocated across all buckets."""
        return self.buckets.aggregate(total=models.Sum("allocated_amount"))["total"] or Decimal("0.00")


class Bucket(TenantScopedModel):
    """Bucket within a plan account."""

    plan_account = models.ForeignKey(PlanAccount, on_delete=models.CASCADE, related_name="buckets")
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["plan_account", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_bucket_name",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.category}): {self.allocated_amount}"
