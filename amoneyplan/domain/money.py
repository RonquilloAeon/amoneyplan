import typing
from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class Currency:
    code: str

    def __eq__(self, other: "Currency") -> bool:
        return self.code == other.code


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency

    @classmethod
    def parse(cls, amount: int | str, currency: Currency = None) -> "Money":
        if not currency:
            currency = Currency("USD")
        return cls(amount=Decimal(amount), currency=currency)

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")

        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __radd__(self, other: typing.Any) -> "Money":
        return self.__add__(
            isinstance(other, Money)
            and other
            or Money.parse(other, currency=self.currency)
        )

    def __eq__(self, other: "Money") -> bool:
        return self.amount == other.amount and self.currency == other.currency
