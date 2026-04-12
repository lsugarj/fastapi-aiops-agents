from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import HTTPException as FastAPIHTTPException
from app.schemas.response import Response
from app.exceptions.codes import Code
from app.utils.validation import format_validation_errors
from app.exceptions.business import BusinessException
from app.core.logging import get_logger

logger = get_logger("exception")


def register_exception_handlers(app):

    # =========================
    # 参数异常（WARNING）
    # =========================
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = format_validation_errors(exc)

        logger.warning(
            "validation error",
            extra={
                "extra_data": {
                    "event": "VALIDATION_ERROR",
                    "severity": "LOW",
                    "method": request.method,
                    "path": request.url.path,
                    "errors": errors,
                }
            },
        )

        return JSONResponse(
            status_code=422,
            content=Response.fail(
                code=Code.VALIDATION_ERROR,
                message="参数校验失败",
                error=errors,
            ).model_dump(),
        )

    # =========================
    # 业务异常（WARNING）
    # =========================
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        logger.warning(
            "business error",
            extra={
                "extra_data": {
                    "event": "BUSINESS_ERROR",
                    "severity": "LOW",
                    "method": request.method,
                    "path": request.url.path,
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )

        return JSONResponse(
            status_code=200,
            content=Response.fail(
                code=exc.code,
                message=exc.message,
            ).model_dump(),
        )

    # =========================
    # HTTP异常（WARNING）
    # =========================
    @app.exception_handler(StarletteHTTPException)
    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc):
        if exc.status_code == 404:
            code = Code.ROUTE_NOT_FOUND
            message = "Resource not found"
        elif exc.status_code == 401:
            code = Code.NO_LOGIN
            message = exc.detail
        elif exc.status_code == 403:
            code = Code.NO_PERMISSION
            message = exc.detail
        else:
            code = exc.status_code
            message = exc.detail

        logger.warning(
            "http error",
            extra={
                "extra_data": {
                    "event": "HTTP_ERROR",
                    "severity": "LOW",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                }
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=Response.fail(
                code=code,
                message=message,
            ).model_dump(),
        )

    # =========================
    # 系统异常（ERROR + 堆栈🔥）
    # =========================
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "system error",
            extra={
                "extra_data": {
                    "event": "SYSTEM_ERROR",
                    "severity": "HIGH",
                    "method": request.method,
                    "path": request.url.path,
                    "query": request.url.query,
                }
            },
        )

        return JSONResponse(
            status_code=500,
            content=Response.fail(
                code=50000,
                message="服务器内部错误",
            ).model_dump(),
        )