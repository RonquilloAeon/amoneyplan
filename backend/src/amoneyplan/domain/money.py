# ruff: noqa
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Union


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
    currency: Currency

    def __init__(self, amount: Union[Decimal, float, int, str] = 0, currency: Currency = Currency("USD")):
        """
        Initialize with an amount, converting to Decimal if needed.
        """
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, (int, float)):
            amount = Decimal(str(amount))

        # Ensure two decimal places for consistency
        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "currency", currency)

    @classmethod
    def parse(cls, amount: Union[Decimal, float, int, str], currency: Currency = Currency("USD")) -> "Money":
        """
        Create a new Money instance from an amount and currency.
        """
        return cls(amount, currency)

    def __add__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    f"Cannot add money with different currencies: {self.currency.code} and {other.currency.code}"
                )
            return Money(self.amount + other.amount, self.currency)
        return Money(self.amount + Decimal(str(other)), self.currency)

    def __sub__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    f"Cannot subtract money with different currencies: {self.currency.code} and {other.currency.code}"
                )
            return Money(self.amount - other.amount, self.currency)
        return Money(self.amount - Decimal(str(other)), self.currency)

    def __mul__(self, other):
        return Money(self.amount * Decimal(str(other)), self.currency)

    def __truediv__(self, other):
        return Money(self.amount / Decimal(str(other)), self.currency)

    def __lt__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    f"Cannot compare money with different currencies: {self.currency.code} and {other.currency.code}"
                )
            return self.amount < other.amount
        return self.amount < Decimal(str(other))

    def __le__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    f"Cannot compare money with different currencies: {self.currency.code} and {other.currency.code}"
                )
            return self.amount <= other.amount
        return self.amount <= Decimal(str(other))

    def __gt__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    f"Cannot compare money with different currencies: {self.currency.code} and {other.currency.code}"
                )
            return self.amount > other.amount
        return self.amount > Decimal(str(other))

    def __ge__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    f"Cannot compare money with different currencies: {self.currency.code} and {other.currency.code}"
                )
            return self.amount >= other.amount
        return self.amount >= Decimal(str(other))

    def __eq__(self, other):
        if isinstance(other, Money):
            return self.currency == other.currency and self.amount == other.amount
        try:
            return self.amount == Decimal(str(other))
        except TypeError:
            return False

    def __str__(self):
        return f"{self.currency.code} {self.amount:.2f}"

    def __repr__(self):
        return f"Money('{self.amount:.2f}', Currency('{self.currency.code}'))"

    @property
    def as_float(self) -> float:
        """Return the monetary value as a float"""
        return float(self.amount)

    @property
    def as_decimal(self) -> Decimal:
        """Return the monetary value as a Decimal"""
        return self.amount
