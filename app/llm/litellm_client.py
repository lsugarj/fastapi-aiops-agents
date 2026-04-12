"""LiteLLM 客户端实现"""
from typing import Any, Dict, List, Optional, AsyncGenerator
import litellm
from litellm import acompletion
from app.llm.base import BaseLLMClient, LLMResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class LiteLLMClient(BaseLLMClient):
    """LiteLLM 客户端 - 统一多模型调用"""

    def __init__(
            self,
            model: str,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            **kwargs
    ):
        self._model = model
        self.api_key = api_key
        self.base_url = base_url
        self.extra_kwargs = kwargs

        # 配置 litellm
        if api_key:
            litellm.api_key = api_key

        logger.info(f"初始化 LiteLLM 客户端，模型: {model}")

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        try:
            response = await acompletion(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
                api_base=self.base_url,
                **{**self.extra_kwargs, **kwargs}
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                raw_response=response
            )
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    async def stream_chat(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        try:
            response = await acompletion(
                model=self._model,
                messages=messages,
                temperature=temperature,
                stream=True,
                api_key=self.api_key,
                api_base=self.base_url,
                **kwargs
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"流式调用失败: {e}")
            raise