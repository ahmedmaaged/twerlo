from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from app.config import settings
import asyncio

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def get_database():
    return mongodb.database

async def connect_to_mongo():
    """Create database connection"""
    mongodb.client = AsyncIOMotorClient(settings.mongodb_url)
    mongodb.database = mongodb.client[settings.database_name]
    
    # Create indexes
    await create_indexes()
    print(f"Connecting to MongoDB at: {settings.mongodb_url}")

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        print("Disconnected from MongoDB")

async def create_indexes():
    """Create necessary indexes for better performance"""
    
    # Users collection indexes
    users_collection = mongodb.database.users
    user_indexes = [
        IndexModel([("email", ASCENDING)], unique=True),
    ]
    await users_collection.create_indexes(user_indexes)
    
    # Query logs collection indexes  
    logs_collection = mongodb.database.query_logs
    log_indexes = [
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("timestamp", ASCENDING)]),
    ]
    await logs_collection.create_indexes(log_indexes)
    
    # Documents collection indexes
    documents_collection = mongodb.database.documents
    doc_indexes = [
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("filename", ASCENDING)]),
    ]
    await documents_collection.create_indexes(doc_indexes)
