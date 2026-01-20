from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from src.models.domain import UploadedFile
from src.repositories.mongo.mongo_repository import MongoRepository


class UploadedFileRepository(MongoRepository[UploadedFile, str]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, 'uploaded_files', UploadedFile)
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """Expose collection for pagination utilities."""
        return self._db[self.collection_name]

    async def get_by_file_key(self, file_key: str) -> Optional[UploadedFile]:
        """Get uploaded file by its storage key."""
        return await self.find_one({'file_key': file_key})

    async def get_by_owner(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[UploadedFile]:
        """Get all files uploaded by a specific user."""
        return await self.find_many({'owner_id': owner_id}, skip=skip, limit=limit)

    async def delete_by_file_key(self, file_key: str) -> bool:
        """Delete uploaded file record by file key."""
        file_record = await self.get_by_file_key(file_key)
        if not file_record:
            return False
        return await self.delete(file_record.id)
    
    async def find_many(self, filter: dict, skip: int = 0, limit: int = 100) -> List[UploadedFile]:
        """Find multiple uploaded files matching the filter."""
        return await super().find_many(filter, skip=skip, limit=limit)
