import typing
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Union, Optional


@dataclass(frozen=True)
class Currency:
    code: str

    def __eq__(self, other: "Currency") -> bool:
        return self.code == other.code


@dataclass(frozen=True)
class Money:
    """
    Money value object for representing and operating on currency values.
    Internally uses Decimal to avoid floating point precision issues.
    """
    amount: Decimal
    
    def __init__(self, amount: Union[Decimal, float, int, str] = 0):
        """
        Initialize with an amount, converting to Decimal if needed.
        """
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        
        # Ensure two decimal places for consistency
        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        object.__setattr__(self, 'amount', amount)
    
    def __add__(self, other):
        if isinstance(other, Money):
            return Money(self.amount + other.amount)
        return Money(self.amount + Decimal(str(other)))
    
    def __sub__(self, other):
        if isinstance(other, Money):
            return Money(self.amount - other.amount)
        return Money(self.amount - Decimal(str(other)))
    
    def __mul__(self, other):
        return Money(self.amount * Decimal(str(other)))
    
    def __truediv__(self, other):
        return Money(self.amount / Decimal(str(other)))
    
    def __lt__(self, other):
        if isinstance(other, Money):
            return self.amount < other.amount
        return self.amount < Decimal(str(other))
    
    def __le__(self, other):
        if isinstance(other, Money):
            return self.amount <= other.amount
        return self.amount <= Decimal(str(other))
    
    def __gt__(self, other):
        if isinstance(other, Money):
            return self.amount > other.amount
        return self.amount > Decimal(str(other))
    
    def __ge__(self, other):
        if isinstance(other, Money):
            return self.amount >= other.amount
        return self.amount >= Decimal(str(other))
    
    def __eq__(self, other):
        if isinstance(other, Money):
            return self.amount == other.amount
        try:
            return self.amount == Decimal(str(other))
        except:
            return False
    
    def __str__(self):
        return f"${self.amount:.2f}"
    
    def __repr__(self):
        return f"Money('{self.amount:.2f}')"
    
    @property
    def as_float(self) -> float:
        """Return the monetary value as a float"""
        return float(self.amount)
    
    @property
    def as_decimal(self) -> Decimal:
        """Return the monetary value as a Decimal"""
        return self.amount
