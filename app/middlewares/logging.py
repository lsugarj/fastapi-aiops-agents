import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("access")


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start = time.time()

        # 低基数
        route = request.scope.get("route")
        path = route.path if route else request.url.path
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except Exception as e:
            raise

        finally:
            cost = round((time.time() - start) * 1000, 2)

            logger.info(
                "access_log",
                extra={
                    "http.method": request.method,
                    "http.target": path,
                    "http.status_code": status_code,
                    "duration_ms": cost,
                    "client_ip": request.client.host if request.client else None,
                    "user_id": getattr(request.state, "user_id", None),
                }
            )