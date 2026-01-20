from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    await db.client.admin.command('ping')
    print('Connected to MongoDB')


async def close_mongo_connection():
    db.client.close()
    print('Disconnected from MongoDB')


async def get_database():
    if db.client is None:
        raise RuntimeError('Database not connected')
    return db.client[settings.mongodb_db_name]
