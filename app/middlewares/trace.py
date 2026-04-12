from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import (
    SpanContext,
    TraceFlags,
    NonRecordingSpan,
    set_span_in_context, TraceState,
)

from app.core.context import get_trace_id

TRACE_HEADER = "X-Trace-Id"
trace_state = TraceState.from_header(["k=v"])


class TraceMiddleware(BaseHTTPMiddleware):
    """
    企业级 Trace Middleware（兼容新旧链路）

    优先级：
    1. traceparent（标准）
    2. X-Trace-Id（历史系统）
    3. 自动生成（OTel）
    """

    async def dispatch(self, request: Request, call_next):
        tracer = trace.get_tracer(__name__)

        # =========================
        # 1. 标准链路提取（W3C）
        # =========================
        ctx = extract(dict(request.headers))
        span_ctx = trace.get_current_span(ctx).get_span_context()

        # =========================
        # 2. fallback：兼容老系统
        # =========================
        if not span_ctx.is_valid:
            legacy_trace_id = request.headers.get(TRACE_HEADER)
            if legacy_trace_id:
                ctx = self._build_context_from_legacy(legacy_trace_id)

        # =========================
        # 3. 创建 span（统一入口）
        # =========================
        with tracer.start_as_current_span(
            name=f"{request.method} {request.url.path}",
            context=ctx,
            kind=trace.SpanKind.SERVER,
        ) as span:

            # =========================
            # 4. 设置常用属性（大厂标准）
            # =========================
            self._set_http_attributes(span, request)

            trace_id = get_trace_id()

            # 注入 request（方便业务使用）
            request.state.trace_id = trace_id

            try:
                response = await call_next(request)

                # 设置响应状态码
                span.set_attribute("http.status_code", response.status_code)

            except Exception as e:
                # 异常记录（关键）
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise

            # =========================
            # 5. 向下游传播（双写）
            # =========================
            headers = {}
            inject(headers)  # 标准 traceparent

            for k, v in headers.items():
                response.headers[k] = v

            # 兼容老系统
            response.headers[TRACE_HEADER] = trace_id

            return response

    # =========================
    # 构建 legacy context（核心桥接）
    # =========================
    def _build_context_from_legacy(self, trace_id: str):
        try:
            span_context = SpanContext(
                trace_id=int(trace_id, 16),
                span_id=self._generate_span_id(),
                is_remote=True,
                trace_flags=TraceFlags(0x01),
                trace_state=trace_state,
            )
            return set_span_in_context(NonRecordingSpan(span_context))
        except Exception:
            return None

    # =========================
    # 生成 span_id
    # =========================
    def _generate_span_id(self) -> int:
        import random

        return random.getrandbits(64)

    # =========================
    # 设置 HTTP 标准属性（OTel规范）
    # =========================
    def _set_http_attributes(self, span, request: Request):
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.target", request.url.path)
        span.set_attribute("http.host", request.client.host if request.client else "")
        span.set_attribute("http.scheme", request.url.scheme)

        if request.headers.get("user-agent"):
            span.set_attribute("http.user_agent", request.headers["user-agent"])