"""LLM 路由器 - 多模型智能路由"""
from typing import Optional

from app.core.config import get_settings
from app.llm.base import BaseLLMClient
from app.llm.litellm_client import LiteLLMClient

llm_config = get_settings().llm

class LLMRouter:
    """LLM 路由器 - 统一入口"""

    _instance = None
    _clients: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化各个模型的客户端"""
        # DeepSeek 客户端（默认）
        self._clients["deepseek"] = LiteLLMClient(
            model=llm_config.deepseek_default_model,
            api_key=llm_config.deepseek_api_key,
            base_url=llm_config.deepseek_base_url
        )

        # OpenAI 客户端（可选）
        if llm_config.openai_api_key:
            self._clients["openai"] = LiteLLMClient(
                model="gpt-4o-mini",
                api_key=llm_config.openai_api_key
            )

        # Anthropic 客户端（可选）
        if llm_config.anthropic_api_key:
            self._clients["anthropic"] = LiteLLMClient(
                model="claude-3-haiku-20240307",
                api_key=llm_config.anthropic_api_key
            )

        self._default_client = "deepseek"

    def get_client(self, name: Optional[str] = None) -> BaseLLMClient:
        """获取 LLM 客户端"""
        client_name = name or self._default_client
        if client_name not in self._clients:
            raise ValueError(f"未知的模型客户端: {client_name}")
        return self._clients[client_name]

    def list_clients(self) -> list:
        """列出所有可用客户端"""
        return list(self._clients.keys())


# 全局路由器实例
llm_router = LLMRouter()