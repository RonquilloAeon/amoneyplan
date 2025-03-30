from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")
PartialData = TypeVar("PartialData")


class UseCaseException(Exception): ...


@dataclass
class UseCaseResult(Generic[T]):
    success: bool

    data: Optional[T] = None
    error: Optional[Exception] = None
    message: Optional[str] = None
    partial_data: Optional[PartialData] = None

    @classmethod
    def success(cls, data: Optional[T] = None, message: Optional[str] = None):
        """Factory method for successful results."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def failure(cls, error: Exception, message: Optional[str] = None):
        """Factory method for failed results."""
        return cls(success=False, message=message or str(error), error=error)

    @classmethod
    def partial_success(cls, partial_data: Optional[PartialData] = None, message: Optional[str] = None):
        """Factory method for partially successful results."""
        return cls(success=False, message=message, partial_data=partial_data)

    def has_data(self) -> bool:
        """Utility to check if data is present."""
        return self.data is not None

    def has_partial_data(self) -> bool:
        """Utility to check if partial data is present."""
        return self.partial_data is not None
