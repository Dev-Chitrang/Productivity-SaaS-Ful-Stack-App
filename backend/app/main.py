from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import setup_middlewares
from app.core.logger import logger

from app.modules.auth.routes import router as auth_router
from app.modules.users.router import router as users_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0"
)

setup_middlewares(app)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["System Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    logger.info("System health evaluation endpoint invoked.")
    try:
        await db.execute(text("SELECT 1"))
        logger.info("Database connectivity verification: SUCCESS")
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Database connectivity verification: FAILED - Details: {str(e)}")
        return {
            "status": "unhealthy",
            "database": f"disconnected: {str(e)}"
        }, 500
