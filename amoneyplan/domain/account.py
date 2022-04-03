from dataclasses import dataclass


@dataclass
class Account:
    name: str
    description: str = None
