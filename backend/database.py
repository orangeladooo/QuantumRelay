"""
database.py - MongoDB connection for PQC-Chatt using Motor (async).
"""

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "pqcchat"

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Open MongoDB connection — call on app startup."""
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    print(f"[DB] Connected to MongoDB: {MONGO_URL}/{DB_NAME}")


async def close_db():
    """Close MongoDB connection — call on app shutdown."""
    global client
    if client:
        client.close()
        print("[DB] MongoDB connection closed.")


def get_db():
    """Return the active database instance."""
    return db
