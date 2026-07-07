from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="TotalChat API",
        version="0.1.0",
        description="Multi-tenant conversational SaaS platform API.",
    )

    app.include_router(health_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": settings.service_name,
            "status": "ok",
        }

    return app


app = create_app()
