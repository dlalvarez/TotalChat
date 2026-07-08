from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.admin import router as admin_router
from app.api.errors import domain_error_handler, http_error_handler, validation_error_handler
from app.api.health import router as health_router
from app.core.config import get_settings
from app.services.errors import DomainError


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="TotalChat API",
        version="0.1.0",
        description="Multi-tenant conversational SaaS platform API.",
    )

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    app.include_router(health_router)
    app.include_router(admin_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": settings.service_name,
            "status": "ok",
        }

    return app


app = create_app()
