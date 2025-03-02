"""
Account domain models for the money management app.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from uuid import UUID, uuid4

from amoneyplan.domain.money import Money


@dataclass
class Bucket:
    """
    Represents a bucket (or sub-account) within an account.
    Each bucket has a name, category, and allocated amount.
    """
    bucket_name: str
    category: str
    allocated_amount: Money = field(default_factory=lambda: Money(0))
    
    def __str__(self) -> str:
        return f"{self.bucket_name} ({self.category}): {self.allocated_amount}"


@dataclass
class Account:
    """
    Represents a financial account (e.g., "Wealthfront", "Apple Card").
    An account has a unique ID, a name, and contains one or more buckets.
    """
    account_id: UUID
    account_name: str
    buckets: Dict[str, Bucket] = field(default_factory=dict)
    
    @classmethod
    def create(cls, account_name: str, buckets: Optional[List[Bucket]] = None) -> 'Account':
        """
        Factory method to create a new account with a generated UUID.
        If no buckets are provided, creates a default bucket.
        """
        account = cls(
            account_id=uuid4(),
            account_name=account_name,
            buckets={}
        )
        
        # If no buckets provided, create a default one
        if not buckets:
            default_bucket = Bucket(bucket_name="Default", category="Default")
            account.buckets[default_bucket.bucket_name] = default_bucket
        else:
            for bucket in buckets:
                account.buckets[bucket.bucket_name] = bucket
                
        return account
    
    def add_bucket(self, bucket_name: str, category: str, initial_amount: Money = None) -> Bucket:
        """
        Add a new bucket to this account.
        """
        if not initial_amount:
            initial_amount = Money(0)
            
        bucket = Bucket(
            bucket_name=bucket_name,
            category=category,
            allocated_amount=initial_amount
        )
        
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
    
    def __str__(self) -> str:
        return f"{self.account_name} ({len(self.buckets)} buckets)"


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
