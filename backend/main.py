"""
Hybrid Athlete Platform - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import health, users, assessments, goals, plans, workouts
from core.config import settings
from db.postgres import init_db, close_db
from db.mongodb import mongodb_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    print("✓ Database connections established")
    yield
    # Shutdown
    await close_db()
    mongodb_client.close()
    print("✓ Database connections closed")


app = FastAPI(
    title="Hybrid Athlete Platform API",
    description="Intelligent, personalized training platform for hybrid athletes",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(assessments.router, prefix="/api/v1", tags=["Assessments"])
app.include_router(goals.router, prefix="/api/v1", tags=["Goals"])
app.include_router(plans.router, prefix="/api/v1", tags=["Training Plans"])
app.include_router(workouts.router, prefix="/api/v1", tags=["Workouts"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hybrid Athlete Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
