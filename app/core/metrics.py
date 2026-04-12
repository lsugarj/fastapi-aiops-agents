from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace  # 必须加

# =========================
# 指标定义
# =========================

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1,
             0.25, 0.5, 1, 2, 5)
)

IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "In progress requests"
)

EXCEPTION_COUNT = Counter(
    "http_exceptions_total",
    "Total exceptions",
    ["method", "path", "exception"],
)


# =========================
# 核心：带 trace_id 的 observe
# =========================
def observe_latency_with_trace(method: str, path: str, duration: float):
    span = trace.get_current_span()
    ctx = span.get_span_context()

    exemplar = None
    if ctx.is_valid:
        exemplar = {
            "trace_id": format(ctx.trace_id, "032x")
        }

    REQUEST_LATENCY.labels(method, path).observe(
        duration,
        exemplar=exemplar
    )