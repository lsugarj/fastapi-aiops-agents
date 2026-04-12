from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.config import get_settings


def init_tracer(app: FastAPI):
    settings = get_settings()
    # 设置服务名称
    resource = Resource(attributes={
        SERVICE_NAME: settings.app.name
    })
    # 创建 TracerProvider
    provider = TracerProvider(resource=resource)
    # 配置 OTLP 导出器（发送到 Jaeger）
    exporter = OTLPSpanExporter(
        endpoint=settings.opentelemetry.otel_exporter_endpoint, # Jaeger OTLP gRPC 端口
        insecure=True,
    )
    # 添加批量处理器（提高性能）
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    # 设置为全局 TracerProvider
    trace.set_tracer_provider(provider)
    # 自动埋点
    FastAPIInstrumentor.instrument_app(app)