from opentelemetry import trace


def get_trace_id() -> str:
    span = trace.get_current_span()
    ctx = span.get_span_context()

    if not ctx.is_valid:
        return ""

    return format(ctx.trace_id, "032x")


def get_span_id() -> str:
    span = trace.get_current_span()
    ctx = span.get_span_context()

    if not ctx.is_valid:
        return ""

    return format(ctx.span_id, "016x")