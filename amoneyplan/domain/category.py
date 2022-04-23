from dataclasses import dataclass

from .money import Money


@dataclass(frozen=True)
class Category:
    name: str
    amount: Money
    notes: str = ""
