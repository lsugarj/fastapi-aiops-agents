import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import (
    REQUEST_COUNT,
    IN_PROGRESS,
    EXCEPTION_COUNT,
    observe_latency_with_trace,  # 用这个
)

class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        method = request.method

        route = request.scope.get("route")
        path = route.path if route else request.url.path

        IN_PROGRESS.inc()
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code

            REQUEST_COUNT.labels(
                method=method,
                path=path,
                status=status_code
            ).inc()

            return response

        except Exception as e:
            EXCEPTION_COUNT.labels(
                method=method,
                path=path,
                exception=type(e).__name__,
            ).inc()
            raise

        finally:
            duration = time.time() - start_time

            observe_latency_with_trace(method, path, duration)

            IN_PROGRESS.dec()