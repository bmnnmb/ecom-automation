"""
API Gateway 统一错误处理模块

提供标准化的错误响应格式和自定义异常类，确保所有adapter服务返回一致的错误结构。

统一错误响应格式:
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "人类可读的错误信息",
        "detail": "详细错误信息（可选）",
        "request_id": "请求追踪ID"
    }
}
"""
from enum import Enum
from typing import Any, Optional, Dict
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger


class ErrorCode(str, Enum):
    """统一错误码定义"""
    # 通用错误 (1xxx)
    INTERNAL_ERROR = "GATEWAY_1000"
    SERVICE_UNAVAILABLE = "GATEWAY_1001"
    RATE_LIMIT_EXCEEDED = "GATEWAY_1002"
    TIMEOUT = "GATEWAY_1003"

    # 认证/鉴权错误 (2xxx)
    AUTH_REQUIRED = "GATEWAY_2000"
    AUTH_TOKEN_EXPIRED = "GATEWAY_2001"
    AUTH_TOKEN_INVALID = "GATEWAY_2002"
    AUTH_PERMISSION_DENIED = "GATEWAY_2003"
    AUTH_SHOP_NOT_BOUND = "GATEWAY_2004"

    # 请求参数错误 (3xxx)
    VALIDATION_ERROR = "GATEWAY_3000"
    INVALID_PARAMETER = "GATEWAY_3001"
    MISSING_PARAMETER = "GATEWAY_3002"

    # 业务错误 (4xxx)
    RESOURCE_NOT_FOUND = "GATEWAY_4000"
    RESOURCE_ALREADY_EXISTS = "GATEWAY_4001"
    OPERATION_CONFLICT = "GATEWAY_4002"
    PLATFORM_ERROR = "GATEWAY_4003"

    # 下游服务错误 (5xxx)
    ADAPTER_ERROR = "GATEWAY_5000"
    ADAPTER_TIMEOUT = "GATEWAY_5001"
    ADAPTER_AUTH_FAILED = "GATEWAY_5002"
    OMS_ERROR = "GATEWAY_5003"


# 错误码到HTTP状态码的映射
ERROR_HTTP_STATUS: Dict[str, int] = {
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.TIMEOUT: 504,
    ErrorCode.AUTH_REQUIRED: 401,
    ErrorCode.AUTH_TOKEN_EXPIRED: 401,
    ErrorCode.AUTH_TOKEN_INVALID: 401,
    ErrorCode.AUTH_PERMISSION_DENIED: 403,
    ErrorCode.AUTH_SHOP_NOT_BOUND: 400,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.INVALID_PARAMETER: 400,
    ErrorCode.MISSING_PARAMETER: 400,
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.RESOURCE_ALREADY_EXISTS: 409,
    ErrorCode.OPERATION_CONFLICT: 409,
    ErrorCode.PLATFORM_ERROR: 502,
    ErrorCode.ADAPTER_ERROR: 502,
    ErrorCode.ADAPTER_TIMEOUT: 504,
    ErrorCode.ADAPTER_AUTH_FAILED: 502,
    ErrorCode.OMS_ERROR: 502,
}


class ErrorResponse(JSONResponse):
    """标准化错误响应"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        detail: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        status_code = ERROR_HTTP_STATUS.get(code, 500)
        body = {
            "success": False,
            "error": {
                "code": code.value,
                "message": message,
                "request_id": request_id,
            },
        }
        if detail is not None:
            body["error"]["detail"] = detail
        super().__init__(status_code=status_code, content=body)


# ============================================================
# 自定义异常类
# ============================================================

class ApiError(Exception):
    """API异常基类"""
    def __init__(
        self,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        message: str = "Internal server error",
        detail: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(ApiError):
    """资源不存在"""
    def __init__(self, resource: str = "资源", resource_id: Optional[str] = None):
        message = f"{resource}不存在"
        if resource_id:
            message = f"{resource} '{resource_id}' 不存在"
        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
        )


class ValidationError(ApiError):
    """请求参数验证失败"""
    def __init__(self, message: str = "请求参数验证失败", detail: Optional[Any] = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            detail=detail,
        )


class AuthError(ApiError):
    """认证/鉴权错误"""
    def __init__(
        self,
        message: str = "认证失败",
        code: ErrorCode = ErrorCode.AUTH_REQUIRED,
        detail: Optional[Any] = None,
    ):
        super().__init__(code=code, message=message, detail=detail)


class ServiceError(ApiError):
    """下游服务调用错误"""
    def __init__(
        self,
        service: str,
        message: str = "下游服务调用失败",
        code: ErrorCode = ErrorCode.ADAPTER_ERROR,
        detail: Optional[Any] = None,
    ):
        self.service = service
        super().__init__(
            code=code,
            message=f"[{service}] {message}",
            detail=detail,
        )


# ============================================================
# 异常处理器注册
# ============================================================

def setup_error_handlers(app: FastAPI) -> None:
    """将统一异常处理器注册到FastAPI应用"""

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            f"API Error: [{exc.code.value}] {exc.message} "
            f"| path={request.url.path} method={request.method} "
            f"| request_id={request_id}"
        )
        return ErrorResponse(
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        # 提取第一个错误的可读信息
        first = errors[0] if errors else {}
        loc = " -> ".join(str(x) for x in first.get("loc", []))
        msg = first.get("msg", "参数格式错误")
        detail_msg = f"字段 '{loc}': {msg}" if loc else msg
        logger.warning(
            f"Validation Error: {detail_msg} "
            f"| path={request.url.path} method={request.method} "
            f"| request_id={request_id}"
        )
        return ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message="请求参数验证失败",
            detail=detail_msg,
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc} "
            f"| path={request.url.path} method={request.method} "
            f"| request_id={request_id}"
        )
        return ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message="服务内部错误，请稍后重试",
            request_id=request_id,
        )
