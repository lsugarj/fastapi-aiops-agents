import pytest

from app.llm.base import LLMResponse


class _SeqLLM:
    def __init__(self, contents):
        self._contents = list(contents)
        self.calls = []

    async def chat(self, messages, temperature=0.7, max_tokens=None, **kwargs):
        self.calls.append(messages)
        content = self._contents.pop(0)
        return LLMResponse(content=content, model="dummy", usage={}, raw_response=None)

    async def stream_chat(self, messages, temperature=0.7, **kwargs):
        if False:
            yield None

    @property
    def model_name(self) -> str:
        return "dummy"


@pytest.mark.asyncio
async def test_aiops_agent_tool_call_then_final(monkeypatch):
    from app.agents.kubernetes_agent import AIOpsAgent
    from app.tools.kubernetes import k8s_tools

    llm = _SeqLLM(
        [
            '<action>get_nodes_status</action>\n<action_input>{}</action_input>',
            "final report",
        ]
    )

    monkeypatch.setattr("app.agents.base.llm_router.get_client", lambda *_args, **_kwargs: llm)

    called = {"count": 0}

    async def _fake_nodes_status():
        called["count"] += 1
        return "nodes"

    monkeypatch.setattr(k8s_tools, "get_nodes_status", _fake_nodes_status)

    agent = AIOpsAgent()
    result = await agent.chat("inspect")

    assert result == "final report"
    assert called["count"] == 1
    assert len(llm.calls) == 2

