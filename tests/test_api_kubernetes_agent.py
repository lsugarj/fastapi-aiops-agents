from fastapi.testclient import TestClient

from app.llm.base import LLMResponse


class _StaticLLM:
    async def chat(self, messages, temperature=0.7, max_tokens=None, **kwargs):
        return LLMResponse(content="report", model="dummy", usage={}, raw_response=None)

    async def stream_chat(self, messages, temperature=0.7, **kwargs):
        if False:
            yield None

    @property
    def model_name(self) -> str:
        return "dummy"


def test_health_and_chat(monkeypatch):
    monkeypatch.setattr("app.agents.base.llm_router.get_client", lambda *_args, **_kwargs: _StaticLLM())

    import app.core.tracing as tracing
    from opentelemetry.sdk.trace.export import SpanExportResult

    class _DummyExporter:
        def __init__(self, *args, **kwargs):
            pass

        def export(self, spans):
            return SpanExportResult.SUCCESS

        def shutdown(self):
            return None

    monkeypatch.setattr(tracing, "OTLPSpanExporter", _DummyExporter)

    from app.main import app

    client = TestClient(app)

    r = client.get("/api/v1/agents/kubernetes/health")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["trace_id"]
    assert body["data"]["status"] == "healthy"

    r = client.post(
        "/api/v1/agents/kubernetes/chat",
        json={"message": "hi", "agent_type": "aiops", "namespace": "default"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["trace_id"]
    assert body["data"]["message"] == "report"
