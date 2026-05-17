from fastapi import APIRouter

from app.api.v1 import devices, measurements, analytics, users

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(measurements.router, prefix="/devices", tags=["measurements"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
