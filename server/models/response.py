"""
Sentry AI — Base Response Wrapper (Pydantic v2)
Standardizes all API outputs: { "status": ..., "data": ..., "message": ... }
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    Uniform envelope for every API response.

    Usage:
        return BaseResponse(status="success", data=my_obj)
        return BaseResponse(status="error", message="Not found", data=None)
    """
    status: str = "success"         # "success" | "error"
    data: T | None = None
    message: str = ""
