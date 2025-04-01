from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
import httpx

class FinanceAPIError(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class DatabaseError(FinanceAPIError):
    def __init__(self, detail: str):
        super().__init__(status_code=503, detail=detail, error_code="DATABASE_ERROR")

class OpenRouterError(FinanceAPIError):
    def __init__(self, detail: str):
        super().__init__(status_code=503, detail=detail, error_code="AI_SERVICE_ERROR")

class ValidationError(FinanceAPIError):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, error_code="VALIDATION_ERROR")

class AuthenticationError(FinanceAPIError):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail, error_code="AUTH_ERROR")

class RateLimitError(FinanceAPIError):
    def __init__(self, detail: str):
        super().__init__(status_code=429, detail=detail, error_code="RATE_LIMIT_EXCEEDED")

async def format_error_response(status_code: int, error_code: str, detail: str) -> Dict[str, Any]:
    return {
        "error": {
            "code": error_code,
            "message": detail,
            "status": status_code,
            "type": error_code.lower()
        }
    }

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content=await format_error_response(503, "DATABASE_ERROR", str(exc))
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc, FinanceAPIError):
        return JSONResponse(
            status_code=exc.status_code,
            content=await format_error_response(exc.status_code, exc.error_code, exc.detail)
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=await format_error_response(exc.status_code, "API_ERROR", exc.detail)
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content=await format_error_response(400, "VALIDATION_ERROR", str(exc.detail))
    )
