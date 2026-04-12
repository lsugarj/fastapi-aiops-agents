"""API 路由 - Agent 接口"""
from fastapi import APIRouter
from typing import Optional

from app.exceptions.business import BusinessException
from app.exceptions.codes import Code
from app.schemas.agent import ChatRequest, AgentResponse, AgentType
from app.agents.kubernetes_agent import AIOpsAgent
from app.agents.log_agent import LogAgent
from app.agents.trace_agent import TraceAgent
from app.core.logging import get_logger
from app.schemas.response import ResponseModel, Response

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/agents/kubernetes", tags=["Agent"])

# Agent 实例缓存
_agents = {}


def get_agent(agent_type: AgentType, model_name: Optional[str] = None):
    """获取 Agent 实例（带缓存）"""
    cache_key = f"{agent_type.value}_{model_name or 'default'}"

    if cache_key not in _agents:
        if agent_type == AgentType.AIOPS:
            _agents[cache_key] = AIOpsAgent(model_name)
        elif agent_type == AgentType.LOG:
            _agents[cache_key] = LogAgent(model_name)
        elif agent_type == AgentType.TRACE:
            _agents[cache_key] = TraceAgent(model_name)
        else:
            raise ValueError(f"未知 Agent 类型: {agent_type}")

    return _agents[cache_key]


@router.post("/chat", response_model=ResponseModel[AgentResponse])
async def chat(request: ChatRequest):
    """通用聊天接口"""
    agent = get_agent(request.agent_type)

    # 构建完整消息（包含命名空间上下文）
    if request.agent_type == AgentType.AIOPS and request.namespace:
        message = f"[命名空间: {request.namespace}]\n{request.message}"
    else:
        message = request.message

    response = await agent.chat(message)

    data = AgentResponse(
        message=response,
        session_id=request.session_id
    )
    return Response.success(data=data)


@router.post("/inspect", response_model=ResponseModel[AgentResponse])
async def inspect_cluster(namespace: str = "default", model_name: Optional[str] = None):
    """集群巡检接口"""
    agent = AIOpsAgent(model_name)
    report = await agent.inspect(namespace)

    data = AgentResponse(
        message=report,
        session_id=f"inspect_{namespace}"
    )
    return Response.success(data=data)


@router.post("/analyze-logs", response_model=ResponseModel[dict])
async def analyze_logs(pod_name: str, namespace: str = "default", model_name: Optional[str] = None):
    """Pod 日志分析接口"""
    agent = LogAgent(model_name)
    analysis = await agent.analyze(pod_name, namespace)

    data = {
        "success": True,
        "pod_name": pod_name,
        "namespace": namespace,
        "analysis": analysis
    }
    return Response.success(data=data)


@router.get("/health", response_model=ResponseModel[dict])
async def health_check():
    """健康检查"""
    data = {
        "status": "healthy",
        "agents": ["aiops", "log", "trace"],
        "models": ["deepseek"]
    }
    return Response.success(data=data)