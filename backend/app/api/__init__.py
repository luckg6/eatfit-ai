from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.memories import router as memories_router
from app.api.meals import router as meals_router
from app.api.advice import router as advice_router
from app.api.records import router_weights, router_body_fat, router_trainings
from app.api.health import router as health_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(memories_router)
api_router.include_router(meals_router)
api_router.include_router(advice_router)
api_router.include_router(router_weights)
api_router.include_router(router_body_fat)
api_router.include_router(router_trainings)
api_router.include_router(health_router)