"""
Account domain models for the money management app.
"""

from dataclasses import dataclass


@dataclass
class Account:
    id: str
    name: str

    notes: str = ""

    @classmethod
    def create(
        cls,
        id: str,
        name: str,
        notes: str = "",
    ):
        return cls(
            id=id,
            name=name,
            notes=notes,
        )
