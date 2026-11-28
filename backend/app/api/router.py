from fastapi import APIRouter
from backend.app.api.endpoints import analytics

api_router = APIRouter()
api_router.include_router(analytics.router)
