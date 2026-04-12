import os
import json
import logging
from datetime import datetime, UTC
from logging.handlers import TimedRotatingFileHandler
import re

from opentelemetry import trace

from app.core.config import get_settings

settings = get_settings()
logging_config = settings.logging


# =========================
# Trace Context 注入（核心）
# =========================
class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        span = trace.get_current_span()
        ctx = span.get_span_context()

        if ctx.is_valid:
            record.trace_id = format(ctx.trace_id, "032x")
            record.span_id = format(ctx.span_id, "016x")
            record.trace_flags = int(ctx.trace_flags)
        else:
            record.trace_id = ""
            record.span_id = ""
            record.trace_flags = 0

        return True


# =========================
# JSON Formatter
# =========================
class JsonFormatter(logging.Formatter):
    ALLOWED_FIELDS = {
        "http.method",
        "http.target",
        "http.status_code",
        "duration_ms",
        "client_ip",
        "user_id",
    }

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),

            # OTel 标准字段
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
            "trace_flags": getattr(record, "trace_flags", 0),

            "logger": record.name,
            "module": record.module,
            "line": record.lineno,

            # 服务标识（建议加）
            "service.name": settings.app.name,
        }

        # 只保留白名单字段（防止日志膨胀）
        for key in self.ALLOWED_FIELDS:
            if hasattr(record, key):
                log[key] = getattr(record, key)

        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False)


# =========================
# 时间 + 大小 双切割 Handler
# =========================
class SizeAndTimeRotatingHandler(TimedRotatingFileHandler):
    def __init__(self, filename, max_bytes, *args, **kwargs):
        super().__init__(filename, *args, **kwargs)
        self.max_bytes = max_bytes

    def shouldRollover(self, record):
        if super().shouldRollover(record):
            return 1

        if self.stream is None:
            self.stream = self._open()

        if self.stream.tell() >= self.max_bytes:
            return 1

        return 0


# =========================
# 工具函数
# =========================
def _parse_size(size: str) -> int:
    size = size.strip().upper()
    match = re.match(r"^(\d+)(KB|MB|GB)?$", size)

    if not match:
        raise ValueError(f"Invalid size format: {size}")

    number, unit = match.groups()
    number = int(number)

    if unit == "KB":
        return number * 1024
    elif unit == "MB":
        return number * 1024 * 1024
    elif unit == "GB":
        return number * 1024 * 1024 * 1024
    else:
        return number


# =========================
# Handler 构建
# =========================
def _build_handler(filename: str, level: int):
    max_bytes = _parse_size(logging_config.max_bytes)

    handler = SizeAndTimeRotatingHandler(
        filename=os.path.join(logging_config.dir, filename),
        when="midnight",
        interval=1,
        backupCount=logging_config.backup_count,
        encoding="utf-8",
        max_bytes=max_bytes,
    )

    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())

    # ✅ 注入 trace context
    handler.addFilter(TraceContextFilter())

    return handler


# =========================
# 初始化日志系统
# =========================
def init_logging():
    os.makedirs(logging_config.dir, exist_ok=True)

    logging.root.handlers = []

    app_handler = _build_handler("app.log", logging.INFO)
    error_handler = _build_handler("error.log", logging.ERROR)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    console_handler.addFilter(TraceContextFilter())

    logging.basicConfig(
        level=logging.INFO,
        handlers=[app_handler, error_handler, console_handler],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)