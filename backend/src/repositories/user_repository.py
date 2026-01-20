from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.models.domain import User
from src.repositories.mongo.mongo_repository import MongoRepository


class UserRepository(MongoRepository[User, str]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, 'users', User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.find_one({'email': email})
    
    async def find_one(self, filter: dict) -> Optional[User]:
        """Find a user matching the filter."""
        return await super().find_one(filter)
