from .account import Account
from . import Entity
from .money import Money


class Entry(Entity):
    def __init__(
        self, id: str, from_account: Account, to_account: Account, amount: Money
    ):
        super().__init__(id)
        self._from_account = from_account
        self._to_account = to_account
        self._amount = amount

    @classmethod
    def create(
        cls, from_account: Account, to_account: Account, amount: Money, id: str = None
    ) -> "Entry":
        return cls(id or cls.generate_id(), from_account, to_account, amount)

    @property
    def amount(self) -> Money:
        return self._amount
