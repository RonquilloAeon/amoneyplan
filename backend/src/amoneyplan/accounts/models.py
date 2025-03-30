from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from amoneyplan.common.models import BaseModel, SafeCuid16Field

from .tenancy import get_current_account


class User(AbstractUser):
    """Custom user model."""

    id = SafeCuid16Field(editable=False, primary_key=True, unique=True)


class AccountQuerySet(models.QuerySet):
    def for_current_account(self):
        account = get_current_account()
        if account:
            return self.filter(user_account=account)
        return self.none()


class AccountManager(models.Manager):
    def get_queryset(self):
        return AccountQuerySet(self.model, using=self._db).for_current_account()


# Unscoped manager to fetch all records, ignoring tenant scoping.
class UnscopedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class Account(BaseModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_accounts",
        on_delete=models.CASCADE,
        help_text="Primary owner of the account.",
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="AccountMembership",
        related_name="accounts",
        help_text="Users associated with this account.",
        through_fields=("account", "user"),
    )

    def __str__(self):
        return self.name


class AccountMembership(BaseModel):
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("viewer", "Viewer"),
    ]
    STATUS_CHOICES = [("active", "Active"), ("pending", "Pending"), ("disabled", "Disabled")]
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    invited_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="invitations_sent",
        help_text="User who sent the invitation.",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="viewer")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")

    class Meta:
        unique_together = ("account", "user")

    def __str__(self):
        return f"{self.user} in {self.account} as {self.role}"


class TenantScopedModel(BaseModel):
    user_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="%(class)ss")

    # This manager will be used for normal queries (automatically scoped)
    objects = AccountManager()
    # This manager lets you query across all accounts (e.g., for admin tasks)
    unscoped = UnscopedManager()

    class Meta:
        abstract = True
