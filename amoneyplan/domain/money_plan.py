from datetime import date

from . import Entity
from .entry import Entry
from .money import Money


class MoneyPlan(Entity):
    def __init__(
        self,
        id: str,
        date: date,
    ):
        super().__init__(id)
        self._date = date
        self._entries: list[Entry] = []

    @classmethod
    def create(cls, date: date, id: str = None) -> "MoneyPlan":
        return cls(
            id or cls.generate_id(),
            date,
        )

    @classmethod
    #
    def create_with_funds(cls, date: date, entry: Entry) -> "MoneyPlan":
        obj = cls.create(date)
        obj.fund(entry)

        return obj

    @property
    def date(self) -> date:
        return self._date

    @property
    def funds_remaining(self) -> Money:
        return sum(entry.amount for entry in self._entries)

    def fund(self, entry: Entry):
        # TODO must check that allocation is of type debit
        self._entries.append(entry)

    def allocate_funds(self, entry: Entry):
        # TODO must check that allocation is of type credit
        self._entries.append(entry)

    def deallocate_funds(self, entry: Entry):
        self._entries.remove(entry)
