"""AIOps Agent - K8s 智能巡检"""
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.kubernetes import k8s_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIOpsAgent(BaseAgent):
    """K8s 智能巡检 Agent"""

    def __init__(self, model_name: str = None):
        super().__init__(model_name)
        self.current_namespace = "default"

    def _build_system_prompt(self) -> str:
        return """你是一个 Kubernetes 集群智能巡检专家。你可以调用工具来检查集群状态。

## 可用工具
1. get_nodes_status() - 获取所有节点的健康状态和资源容量
2. get_pods(namespace) - 获取指定命名空间的 Pod 状态
3. get_deployments(namespace) - 获取 Deployment 副本状态
4. get_pod_logs(pod_name, namespace, lines) - 获取 Pod 日志（默认100行）
5. get_namespace_summary() - 获取所有命名空间摘要
6. get_pod_anomalies(namespace) - 获取异常 Pod 列表

## 巡检流程
1. 首先调用 get_nodes_status() 检查节点健康
2. 调用 get_namespace_summary() 了解全局情况
3. 发现异常时，调用 get_pod_anomalies() 定位问题 Pod
4. 对异常 Pod 调用 get_pod_logs() 分析原因
5. 给出具体的修复建议

## 输出格式
当需要调用工具时，严格输出以下格式：
<action>工具名称</action>
<action_input>{"参数名": "参数值"}</action_input>

例如：
<action>get_pods</action>
<action_input>{"namespace": "default"}</action_input>

## 注意事项
- 巡检时优先检查节点健康
- 发现 CrashLoopBackOff 的 Pod 一定要获取日志
- 给出修复建议时要具体可操作
"""

    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        tool_map = {
            "get_nodes_status": k8s_tools.get_nodes_status,
            "get_pods": lambda **kwargs: k8s_tools.get_pods(kwargs.get("namespace", "default")),
            "get_deployments": lambda **kwargs: k8s_tools.get_deployments(kwargs.get("namespace", "default")),
            "get_pod_logs": lambda **kwargs: k8s_tools.get_pod_logs(
                kwargs.get("pod_name", ""),
                kwargs.get("namespace", "default"),
                kwargs.get("lines", 100)
            ),
            "get_namespace_summary": k8s_tools.get_namespace_summary,
            "get_pod_anomalies": lambda **kwargs: k8s_tools.get_pod_anomalies(kwargs.get("namespace", "default")),
        }

        if tool_name not in tool_map:
            return f"[错误] 未知工具: {tool_name}"

        try:
            result = await tool_map[tool_name](**parameters)
            return result
        except Exception as e:
            logger.error(f"工具执行失败 {tool_name}: {e}")
            return f"[工具执行错误] {str(e)}"

    async def inspect(self, namespace: str = "default") -> str:
        """执行完整巡检"""
        self.current_namespace = namespace
        prompt = f"""
请对 Kubernetes 集群进行全面健康巡检，重点检查 {namespace} 命名空间。

请按以下步骤执行：
1. 检查所有节点状态
2. 获取所有命名空间摘要
3. 获取 {namespace} 命名空间的异常 Pod
4. 对发现的异常 Pod 获取日志进行分析
5. 生成巡检报告，包含问题和修复建议

请开始巡检。
"""
        return await self.chat(prompt)