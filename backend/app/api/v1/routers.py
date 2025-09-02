from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "message": "API is running"}
