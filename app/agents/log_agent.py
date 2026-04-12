"""日志分析 Agent"""
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.kubernetes import k8s_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


class LogAgent(BaseAgent):
    """日志分析 Agent - 专门分析 Pod 日志"""

    def _build_system_prompt(self) -> str:
        return """你是一个 Kubernetes 日志分析专家。你的任务是分析 Pod 日志中的错误和异常。

## 可用工具
1. get_pod_logs(pod_name, namespace, lines) - 获取 Pod 日志

## 分析要点
- 识别错误类型（连接失败、权限错误、OOM、配置错误等）
- 分析错误频率和模式
- 给出根因分析和修复建议

## 输出格式
<action>get_pod_logs</action>
<action_input>{"pod_name": "xxx", "namespace": "default", "lines": 200}</action_input>
"""

    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        if tool_name == "get_pod_logs":
            return await k8s_tools.get_pod_logs(
                parameters.get("pod_name", ""),
                parameters.get("namespace", "default"),
                parameters.get("lines", 200)
            )
        return f"[错误] 未知工具: {tool_name}"

    async def analyze(self, pod_name: str, namespace: str = "default") -> str:
        """分析指定 Pod 的日志"""
        prompt = f"""
请分析 Pod "{pod_name}" (命名空间: {namespace}) 的日志。

步骤：
1. 获取该 Pod 的最近 200 行日志
2. 分析日志中的错误和异常
3. 找出根本原因
4. 给出修复建议

请开始分析。
"""
        return await self.chat(prompt)