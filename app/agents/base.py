"""Agent 基础类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.llm.router import llm_router
from app.core.config import get_settings
from app.core.logging import get_logger

llm_config = get_settings().llm

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Agent 抽象基类"""

    def __init__(self, model_name: Optional[str] = None):
        self.llm_client = llm_router.get_client(model_name)
        self.system_prompt = self._build_system_prompt()
        self.max_iterations = llm_config.agent_max_iterations
        self.temperature = llm_config.agent_temperature

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        pass

    @abstractmethod
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        pass

    def _parse_tool_call(self, response: str) -> Optional[tuple]:
        """解析工具调用"""
        import re
        # 格式: <action>tool_name</action>\n<action_input>{"key": "value"}</action_input>
        pattern = r'<action>(.*?)</action>\s*<action_input>(.*?)</action_input>'
        match = re.search(pattern, response, re.DOTALL)

        if match:
            tool_name = match.group(1).strip()
            params_str = match.group(2).strip()
            import json
            try:
                params = json.loads(params_str)
            except:
                params = {}
            return tool_name, params
        return None

    async def chat(self, user_input: str) -> str:
        """处理用户输入"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        for iteration in range(self.max_iterations):
            response = await self.llm_client.chat(
                messages=messages,
                temperature=self.temperature
            )

            assistant_msg = response.content
            logger.debug(f"Agent 思考 [{iteration}]: {assistant_msg[:200]}...")

            # 检查是否有工具调用
            tool_call = self._parse_tool_call(assistant_msg)

            if tool_call:
                tool_name, params = tool_call
                logger.info(f"调用工具: {tool_name}, 参数: {params}")

                tool_result = await self._execute_tool(tool_name, params)

                messages.append({"role": "assistant", "content": assistant_msg})
                messages.append(
                    {"role": "user", "content": f"工具执行结果:\n{tool_result}\n\n请继续分析并给出最终回答。"})
            else:
                # 无工具调用，返回最终回答
                return assistant_msg

        return "达到最大迭代次数，请简化查询或稍后重试。"