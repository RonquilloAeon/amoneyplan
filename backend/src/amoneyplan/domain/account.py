"""
Account domain models for the money management app.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from amoneyplan.domain.money import Money


@dataclass
class Bucket:
    """
    Represents a bucket (or sub-account) within an account.
    Each bucket has a name, category, and allocated amount.
    """

    name: str
    category: str
    allocated_amount: Money = field(default_factory=lambda: Money(0))

    def __str__(self) -> str:
        return f"{self.name} ({self.category}): {self.allocated_amount}"


@dataclass
class Account:
    """
    Represents a financial account (e.g., "Wealthfront", "Apple Card").
    An account has a unique ID, a name, and contains one or more buckets.
    """

    account_id: str
    name: str
    buckets: Dict[str, Bucket] = field(default_factory=dict)
    is_checked: bool = field(default=False)
    notes: str = ""

    @classmethod
    def create(
        cls, account_id: str, name: str, buckets: Optional[List[Union[Bucket, dict]]] = None, notes: str = ""
    ) -> "Account":
        """
        Factory method to create a new account with a generated ID.
        If no buckets are provided or added during creation, creates a default bucket.

        Args:
            account_id: id for the account.
            name: The name of the account
            buckets: Optional list of buckets to add to the account. Can be Bucket objects or dicts.
            notes: Optional notes for the account.
        """
        account = cls(account_id=account_id, name=name, buckets={}, notes=notes)

        if buckets:
            # If buckets are provided, use those
            for bucket_data in buckets:
                if isinstance(bucket_data, dict):
                    bucket = Bucket(
                        name=bucket_data["name"],
                        category=bucket_data["category"],
                        allocated_amount=Money(bucket_data["allocated_amount"]),
                    )
                else:
                    bucket = bucket_data
                account.buckets[bucket.name] = bucket
        else:
            # Only create default bucket if no buckets were provided
            default_bucket = Bucket(name="Default", category="default")
            account.buckets[default_bucket.name] = default_bucket

        return account

    def add_bucket(self, bucket_name: str, category: str, initial_amount: Money = None) -> Bucket:
        """
        Add a new bucket to this account.
        """
        if not initial_amount:
            initial_amount = Money(0)

        bucket = Bucket(name=bucket_name, category=category, allocated_amount=initial_amount)

        self.buckets[bucket_name] = bucket
        return bucket

    def get_bucket(self, bucket_name: str) -> Optional[Bucket]:
        """
        Get a bucket by name.
        """
        return self.buckets.get(bucket_name)

    def get_total_allocated(self) -> Money:
        """
        Calculate the total amount allocated across all buckets.
        """
        total = Money(0)
        for bucket in self.buckets.values():
            total += bucket.allocated_amount
        return total

    def set_checked_state(self, is_checked: bool) -> None:
        """Change the checked state of the account."""
        self.is_checked = is_checked

    def edit_notes(self, notes: str):
        """
        Edit the notes of the account.

        Args:
            notes: The new notes for the account
        """
        self.notes = notes

    def __str__(self) -> str:
        return f"{self.name} ({len(self.buckets)} buckets)"


@dataclass
class PlanAccountAllocation:
    """
    Represents an allocation of funds to an account within a Money Plan.
    """

    account: Account

    def get_total_allocated(self) -> Money:
        """
        Get the total amount allocated to this account across all buckets.
        """
        return self.account.get_total_allocated()
