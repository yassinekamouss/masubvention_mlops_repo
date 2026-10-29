import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.extract import router as extract_router
from app.api.v1.endpoints.rules import router as rules_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)


def create_app() -> FastAPI:
    """Application factory for FastAPI instance."""
    is_production = settings.ENVIRONMENT.lower() == "production"

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Microservice IA pour l'analyse des dossiers d'investissement et la rédaction experte.",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    # CORS configuration - restricted to authorized local/internal origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(api_v1_router)
    app.include_router(health_router)  # Direct /health access at root level
    app.include_router(extract_router)  # Direct /extract alias at root level
    app.include_router(rules_router)    # Direct /rules/generate alias at root level

    return app


__all__ = ["create_app"]

