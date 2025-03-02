from ulid import ULID


class Entity:
    _id: str = None

    def __init__(self, id: str):
        self._id = id

    def __eq__(self, o: object) -> bool:
        return self.id == getattr(o, "id", None)

    @staticmethod
    def generate_id() -> str:
        return str(ULID())

    @property
    def id(self):
        return self._id
