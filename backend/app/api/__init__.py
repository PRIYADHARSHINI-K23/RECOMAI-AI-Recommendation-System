from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.items import router as items_router
from app.api.interactions import router as interactions_router
from app.api.recommendations import router as recommendations_router
from app.api.search import router as search_router
from app.api.insights import router as insights_router
from app.api.admin import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(items_router)
api_router.include_router(interactions_router)
api_router.include_router(recommendations_router)
api_router.include_router(search_router)
api_router.include_router(insights_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
