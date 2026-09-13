from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Healthcheck endpoint returning operational status of the service."""
    return {
        "status": "ok",
        "service": "masubvention_mlops",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "role": "Virtual Consultant"
    }
