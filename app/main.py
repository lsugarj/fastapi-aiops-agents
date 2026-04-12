from contextlib import asynccontextmanager
from app.api.v1.kubernetes_agent import router as agent_router
from app.core.tracing import init_tracer
from app.exceptions.handlers import register_exception_handlers
from app.core.logging import init_logging, get_logger
from app.middlewares.metrics import MetricsMiddleware
from app.middlewares.trace import TraceMiddleware
from app.middlewares.logging import LoggingMiddleware
from fastapi import FastAPI
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


init_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== 启动阶段 =====
    logger.info("日志初始化成功")
    yield
    # ===== 关闭阶段 =====

app = FastAPI(lifespan=lifespan)
# 初始化 OpenTelemetry
init_tracer(app)
# 注册middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TraceMiddleware)
# 注册异常处理
register_exception_handlers(app)
# 注册路由
app.include_router(agent_router, prefix="/api")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
