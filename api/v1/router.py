from fastapi import APIRouter

from api.v1.endpoints import tasks

# Create API router
api_router = APIRouter()

# Include task endpoints
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"]) 