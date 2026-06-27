import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db, check_database_health
from app.core.redis import check_redis_health
from app.core.middleware import setup_middlewares
from app.core.logger import logger

from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.calender.routes import router as calender_router
from app.modules.notes.routes import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Loading configuration")
    logger.info("Connecting to PostgreSQL")
    try:
        await check_database_health()
    except Exception:
        logger.error("Cannot start application — PostgreSQL is unavailable")
        sys.exit(1)
    logger.info("Connecting to Redis")
    try:
        await check_redis_health()
    except Exception:
        logger.error("Cannot start application — Redis is unavailable")
        sys.exit(1)
    logger.info("Initializing application")
    logger.info("Application ready")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

setup_middlewares(app)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(calender_router, prefix=settings.API_V1_STR)
app.include_router(notes_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["System Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.ENVIRONMENT,
        }
    except Exception as e:
        logger.error(f"Health check failed — database: {str(e)}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": f"disconnected: {str(e)}",
            },
        )
