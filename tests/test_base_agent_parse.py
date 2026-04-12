import pytest

from app.agents.base import BaseAgent
from app.llm.base import LLMResponse


class _DummyLLM:
    async def chat(self, messages, temperature=0.7, max_tokens=None, **kwargs):
        return LLMResponse(content="ok", model="dummy", usage={}, raw_response=None)

    async def stream_chat(self, messages, temperature=0.7, **kwargs):
        if False:
            yield None

    @property
    def model_name(self) -> str:
        return "dummy"


class _DummyAgent(BaseAgent):
    def _build_system_prompt(self) -> str:
        return "system"

    async def _execute_tool(self, tool_name, parameters):
        return "tool"


def test_parse_tool_call_ok(monkeypatch):
    monkeypatch.setattr("app.agents.base.llm_router.get_client", lambda *_args, **_kwargs: _DummyLLM())

    agent = _DummyAgent()
    parsed = agent._parse_tool_call(
        '<action>get_pods</action>\n<action_input>{"namespace": "default"}</action_input>'
    )
    assert parsed == ("get_pods", {"namespace": "default"})


def test_parse_tool_call_invalid_json(monkeypatch):
    monkeypatch.setattr("app.agents.base.llm_router.get_client", lambda *_args, **_kwargs: _DummyLLM())

    agent = _DummyAgent()
    parsed = agent._parse_tool_call(
        "<action>get_pods</action>\n<action_input>{not-json}</action_input>"
    )
    assert parsed == ("get_pods", {})


def test_parse_tool_call_none(monkeypatch):
    monkeypatch.setattr("app.agents.base.llm_router.get_client", lambda *_args, **_kwargs: _DummyLLM())

    agent = _DummyAgent()
    assert agent._parse_tool_call("final answer") is None

