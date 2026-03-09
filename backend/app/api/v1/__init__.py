from fastapi import APIRouter
from app.api.v1.endpoints import properties, projects, economics, production, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(properties.router)
api_router.include_router(projects.router)
api_router.include_router(economics.router)
api_router.include_router(production.router)
