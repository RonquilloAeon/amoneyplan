from dataclasses import dataclass


class IllegalStateError(Exception):
    ...


@dataclass(frozen=True)
class Id:
    id: str

    def __post_init__(self):
        if len(self.id) == 0:
            raise ValueError("Id cannot be empty")


class Entity:
    _id: Id

    def __init__(self, id: Id):
        self._id = id

    def __eq__(self, o: object) -> bool:
        return self.id == getattr(o, "id", None)

    @property
    def id(self):
        return self._id
