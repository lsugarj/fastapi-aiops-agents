"""链路追踪 Agent - 预留扩展"""
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


class TraceAgent(BaseAgent):
    """链路追踪 Agent - 分析服务调用链"""

    def _build_system_prompt(self) -> str:
        return """你是一个分布式链路追踪专家。你可以分析服务调用链，定位性能瓶颈。

## 功能说明
当前版本支持基础分析，完整 Jaeger 集成正在开发中。

## 分析要点
- 识别慢调用和错误调用
- 分析依赖关系
- 给出优化建议
"""

    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        # TODO: 集成 Jaeger 工具
        return f"[信息] Jaeger 集成开发中，当前工具 {tool_name} 暂不可用"

    async def analyze_trace(self, trace_id: str) -> str:
        """分析指定 trace"""
        prompt = f"""
请分析 Trace ID: {trace_id}

请说明如何分析该链路：
1. 查看调用链路中的错误
2. 识别最耗时的服务调用
3. 给出优化建议
"""
        return await self.chat(prompt)