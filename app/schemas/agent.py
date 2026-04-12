"""数据模型"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.schemas.common import RequestBaseModel


class AgentType(str, Enum):
    """Agent 类型"""
    AIOPS = "aiops"
    LOG = "log"
    TRACE = "trace"


class ChatRequest(RequestBaseModel):
    """聊天请求"""
    message: str
    agent_type: AgentType | None =AgentType.AIOPS
    session_id: str | None = None
    namespace: str | None = "default"


class ToolCall(BaseModel):
    """工具调用"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent响应"""
    message: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    session_id: Optional[str] = None


class InspectionReport(BaseModel):
    """巡检报告"""
    cluster_health: str
    node_status: Dict[str, Any]
    pod_anomalies: List[Dict[str, Any]]
    deployment_status: List[Dict[str, Any]]
    recommendations: List[str]