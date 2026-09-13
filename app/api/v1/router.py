from fastapi import APIRouter
from app.api.v1.endpoints.extract import router as extract_router
from app.api.v1.endpoints.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount route groups
api_v1_router.include_router(extract_router)
api_v1_router.include_router(health_router)
