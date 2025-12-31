from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None


@dataclass
class NotFoundError(Exception):
    message: str
    detail: str | None = None
    code: str = "NOT_FOUND"


@dataclass
class ValidationError(Exception):
    message: str
    detail: str | None = None
    code: str = "VALIDATION_ERROR"


@dataclass
class AuthorizationError(Exception):
    message: str
    detail: str | None = None
    code: str = "FORBIDDEN"


@dataclass
class BenchlingError(Exception):
    message: str
    detail: str | None = None
    code: str = "BENCHLING_ERROR"


@dataclass
class BatchError(Exception):
    message: str
    detail: str | None = None
    code: str = "BATCH_ERROR"


def _error_response(status_code: int, message: str, detail: str | None, code: str | None):
    payload = ErrorResponse(error=message, detail=detail, code=code)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    code = None
    if exc.status_code == status.HTTP_400_BAD_REQUEST:
        code = "VALIDATION_ERROR"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "AUTH_REQUIRED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    return _error_response(exc.status_code, str(exc.detail), None, code)


def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, exc.message, exc.detail, exc.code)


def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return _error_response(status.HTTP_400_BAD_REQUEST, exc.message, exc.detail, exc.code)


def authorization_handler(_: Request, exc: AuthorizationError) -> JSONResponse:
    return _error_response(status.HTTP_403_FORBIDDEN, exc.message, exc.detail, exc.code)


def benchling_handler(_: Request, exc: BenchlingError) -> JSONResponse:
    return _error_response(status.HTTP_502_BAD_GATEWAY, exc.message, exc.detail, exc.code)


def batch_handler(_: Request, exc: BatchError) -> JSONResponse:
    return _error_response(status.HTTP_502_BAD_GATEWAY, exc.message, exc.detail, exc.code)


def internal_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Internal server error",
        str(exc),
        "INTERNAL_ERROR",
    )


def register_exception_handlers(app: Any) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(ValidationError, validation_handler)
    app.add_exception_handler(AuthorizationError, authorization_handler)
    app.add_exception_handler(BenchlingError, benchling_handler)
    app.add_exception_handler(BatchError, batch_handler)
    app.add_exception_handler(Exception, internal_error_handler)
