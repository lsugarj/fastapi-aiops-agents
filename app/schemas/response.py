from typing import Generic, TypeVar, Any
from pydantic.generics import GenericModel
from pydantic import BaseModel
from app.core.context import get_trace_id

T = TypeVar("T")


class ResponseModel(GenericModel, Generic[T]):
    code: int
    message: str
    data: T | None = None
    error: Any | None = None
    trace_id: str | None = None


class Response(BaseModel):
    @staticmethod
    def success(*, data: Any = None, message: str = "success") -> ResponseModel[T]:
        trace_id = get_trace_id()
        return ResponseModel[T](
            code=0,
            message=message,
            data=data,
            trace_id=trace_id
        )

    @staticmethod
    def fail(*, code: int, message: str, error: Any = None) -> ResponseModel[Any]:
        trace_id = get_trace_id()
        return ResponseModel[Any](
            code=code,
            message=message,
            error=error,
            trace_id=trace_id
        )
