"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres import get_session
from db.mongodb import get_mongodb
import time

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@router.get("/health/db")
async def database_health(
    session: AsyncSession = Depends(get_session),
    mongodb = Depends(get_mongodb)
):
    """Check database connections"""
    try:
        # Check PostgreSQL
        await session.execute("SELECT 1")
        postgres_status = "connected"
    except Exception as e:
        postgres_status = f"error: {str(e)}"

    try:
        # Check MongoDB
        await mongodb.command("ping")
        mongodb_status = "connected"
    except Exception as e:
        mongodb_status = f"error: {str(e)}"

    return {
        "status": "healthy" if postgres_status == "connected" and mongodb_status == "connected" else "unhealthy",
        "postgres": postgres_status,
        "mongodb": mongodb_status,
        "timestamp": time.time()
    }
