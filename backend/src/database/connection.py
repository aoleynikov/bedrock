from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.config import settings


class DatabaseConnection:
    """
    Singleton database connection manager with connection pooling.
    
    Motor automatically manages connection pooling. Best practices:
    - Use a single MongoClient instance (singleton pattern)
    - Connection pool is shared across all operations
    - Pool size is managed automatically (default: 100 max connections)
    - Connections are reused efficiently
    """
    _client: AsyncIOMotorClient = None
    _db: AsyncIOMotorDatabase = None

    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB with connection pooling.
        
        Motor's AsyncIOMotorClient automatically handles:
        - Connection pooling (default maxPoolSize=100)
        - Connection reuse
        - Automatic reconnection on failures
        """
        if cls._client is None:
            # Create singleton client with connection pool settings
            # Motor manages the pool automatically - no need to manually manage connections
            cls._client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=50,  # Maximum connections in pool
                minPoolSize=5,  # Minimum connections to maintain
                maxIdleTimeMS=30000  # Close idle connections after 30s
            )
            await cls._client.admin.command('ping')
            cls._db = cls._client[settings.mongodb_db_name]

    @classmethod
    async def disconnect(cls):
        """
        Disconnect from MongoDB.
        
        Note: In Celery tasks, we typically don't disconnect as the connection
        pool is shared and managed by Motor. Only disconnect on application shutdown.
        """
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.
        
        For Celery tasks: Connection is reused from pool automatically.
        No need to create new connections - Motor handles pooling.
        """
        if cls._db is None:
            raise RuntimeError('Database not connected. Call connect() first.')
        return cls._db
