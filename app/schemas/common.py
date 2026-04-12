from pydantic import BaseModel, Field, ConfigDict
from typing import Generic, TypeVar, List
from datetime import datetime
from pydantic.generics import GenericModel


T = TypeVar("T")

# ========================
# 通用基础字段（复用）
# ========================
class IDModel(BaseModel):
    id: int = Field(..., description="唯一ID")


class TimestampModel(BaseModel):
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class SoftDeleteModel(BaseModel):
    is_deleted: bool = Field(False, description="是否删除")


# ========================
# request base model
# ========================
class RequestBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid"
    )

# ========================
# response base model
# ========================
class ResponseBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore"   # 忽略多余字段（推荐）
    )

# ========================
# 分页请求
# ========================
class PageParamsRequestBaseModel(RequestBaseModel):
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(10, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


# ========================
# 分页响应（泛型）
# ========================
class PageResult(GenericModel, Generic[T]):
    total: int = Field(..., description="总条数")
    items: List[T] = Field(..., description="数据列表")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")


# ========================
# 通用布尔返回
# ========================
class BoolResult(ResponseBaseModel):
    success: bool


# ========================
# 通用ID返回（创建成功）
# ========================
class IDResult(ResponseBaseModel):
    id: int