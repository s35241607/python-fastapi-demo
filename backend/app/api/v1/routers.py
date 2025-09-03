from fastapi import APIRouter

from app.api.v1.test_errors import router as test_errors_router

api_router = APIRouter()

# Include test error routes (remove in production)
api_router.include_router(test_errors_router)


@api_router.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "message": "API is running"}
