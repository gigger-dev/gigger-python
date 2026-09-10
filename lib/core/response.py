from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SimpleResponse(BaseModel):
    status_code: int
    message: str
    extra: Any = None


class BasicResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    limit: int = 50
    offset: int
    total: int
    items: Sequence[T]
