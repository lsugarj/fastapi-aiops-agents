"""LLM 基础抽象"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """消息结构"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Any


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""

    @abstractmethod
    async def chat(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        pass

    @abstractmethod
    async def stream_chat(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            **kwargs
    ):
        """流式聊天"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """获取模型名称"""
        pass