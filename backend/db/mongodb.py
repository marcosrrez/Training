"""
MongoDB configuration
"""
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# MongoDB client
mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)

# Database
mongodb = mongodb_client.hybrid_athlete

# Collections
workouts_collection = mongodb.workouts
workout_logs_collection = mongodb.workout_logs
research_collection = mongodb.research
training_plans_collection = mongodb.training_plans


async def get_mongodb():
    """Dependency for getting MongoDB database"""
    return mongodb


async def close_mongodb():
    """Close MongoDB connections"""
    mongodb_client.close()
    print("✓ MongoDB connections closed")
