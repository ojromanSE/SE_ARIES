"""
SE_ARIES — Internal Petroleum Economics Platform
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.base import init_db
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup."""
    await init_db()
    # Seed default admin user if needed
    await _seed_admin()
    yield


async def _seed_admin():
    """Create default admin user if none exists."""
    from app.db.base import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@se-aries.local",
                full_name="Administrator",
                hashed_password=get_password_hash("admin123"),
                role="admin",
            )
            db.add(admin)
            await db.commit()


app = FastAPI(
    title="SE_ARIES",
    description="Internal Petroleum Economics & Reserves Platform — ARIES-compatible",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return JSONResponse({
        "app": "SE_ARIES — Internal Petroleum Economics Platform",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": settings.API_V1_STR,
    })
