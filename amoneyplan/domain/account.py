from . import Entity, Id, IllegalStateError
from .category import Category
from .money import Money


class Account(Entity):
    def __init__(
        self,
        id: Id,
        name: str,
        is_disbursed: bool = False,
        categories: list[Category] = None,
    ):
        super().__init__(id)
        self._name = name
        self._categories: dict[str, Category] = {}
        self._is_disbursed = is_disbursed

        if categories is not None:
            for category in categories:
                self.add_category(category)

    @property
    def allocated_funds(self) -> Money:
        return sum(category.amount for category in self.categories)

    @property
    def categories(self) -> list[Category]:
        return list(self._categories.values())

    @property
    def is_disbursed(self) -> bool:
        return self._is_disbursed

    @property
    def name(self) -> str:
        return self._name

    def add_category(self, category: Category):
        if self.is_disbursed:
            raise IllegalStateError(
                "Unable to add a category because the account marked as disbursed."
            )

        if category.name in self._categories:
            raise IllegalStateError(
                f"Unable to add category {category.name!r} because a category with this name already exists in the account."
            )

        self._categories[category.name] = category

    def mark_as_disbursed(self):
        if not self._categories:
            raise IllegalStateError(
                "Unable to mark the account funds as disbursed because it doesn't have any categories."
            )

        self._is_disbursed = True

    def remove_category(self, category: Category):
        del self._categories[category.name]

    def unmark_as_disbursed(self):
        self._is_disbursed = False
