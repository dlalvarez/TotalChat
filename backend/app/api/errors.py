from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.errors import BusinessRuleViolation, ConflictError, DomainValidationError, ResourceNotFound, SlotNotAvailable


def api_error_response(code: str, message: str, status_code: int, details: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message, "details": details or {}}})


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, DomainValidationError):
        return api_error_response("VALIDATION_ERROR", str(exc), 400)
    if isinstance(exc, ResourceNotFound):
        return api_error_response("RESOURCE_NOT_FOUND", str(exc), 404)
    if isinstance(exc, ConflictError):
        return api_error_response("CONFLICT", str(exc), 409)
    if isinstance(exc, SlotNotAvailable):
        return api_error_response("SLOT_NOT_AVAILABLE", str(exc), 409)
    if isinstance(exc, BusinessRuleViolation):
        return api_error_response("BUSINESS_RULE_VIOLATION", str(exc), 409)
    return api_error_response("INTERNAL_ERROR", "Internal server error.", 500)


async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and {"code", "message"}.issubset(detail):
        return api_error_response(detail["code"], detail["message"], exc.status_code, detail.get("details") or {})
    return api_error_response("INTERNAL_ERROR", "Internal server error.", exc.status_code)


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return api_error_response("VALIDATION_ERROR", "Invalid request parameters.", 422, {"errors": exc.errors()})
