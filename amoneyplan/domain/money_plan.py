from datetime import date

from ulid import ULID

from . import Entity


class MoneyPlan(Entity):
    def __init__(
        self,
        id: str,
        date: date,
    ):
        super().__init__(id)
        self._date = date

    @classmethod
    def create(cls, date: date, id: str = None) -> "MoneyPlan":
        return cls(
            id or str(ULID()),
            date,
        )

    @property
    def date(self) -> date:
        return self._date
