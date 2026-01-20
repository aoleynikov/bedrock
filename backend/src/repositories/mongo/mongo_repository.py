from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from pydantic import BaseModel
from src.repositories.base import BaseRepository

T = TypeVar('T', bound=BaseModel)
ID = TypeVar('ID')


class MongoRepository(BaseRepository[T, ID], Generic[T, ID]):
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str, entity_type: type[T]):
        super().__init__(collection_name)
        self._db = db
        self._entity_type = entity_type

    def _get_collection(self) -> AsyncIOMotorCollection:
        return self._db[self.collection_name]

    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        data = entity.model_dump(exclude_none=True)
        if '_id' in data and isinstance(data['_id'], str):
            try:
                data['_id'] = ObjectId(data['_id'])
            except Exception:
                pass
        return data

    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        if '_id' in data:
            data['id'] = str(data['_id'])
            del data['_id']  # Remove _id to avoid Pydantic validation issues
        return self._entity_type(**data)

    async def create(self, entity: T) -> T:
        collection = self._get_collection()
        data = self._entity_to_dict(entity)
        if '_id' in data:
            del data['_id']
        entity_dict = entity.model_dump()
        if 'created_at' in entity_dict:
            data['created_at'] = datetime.utcnow()
        result = await collection.insert_one(data)
        return await self.get_by_id(str(result.inserted_id))

    async def get_by_id(self, id: ID) -> Optional[T]:
        if not isinstance(id, str):
            return None
        try:
            collection = self._get_collection()
            doc = await collection.find_one({'_id': ObjectId(id)})
            if not doc:
                return None
            return self._dict_to_entity(doc)
        except Exception:
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        collection = self._get_collection()
        cursor = collection.find().skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._dict_to_entity(doc) for doc in docs]
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Alias for get_all for backward compatibility."""
        return await self.get_all(skip=skip, limit=limit)

    async def update(self, id: ID, entity: T) -> Optional[T]:
        if not isinstance(id, str):
            return None
        try:
            collection = self._get_collection()
            # Get all fields including None values to detect fields to unset
            all_data = entity.model_dump(exclude_none=False)
            # Get fields with values (exclude None)
            data = self._entity_to_dict(entity)
            if '_id' in data:
                del data['_id']
            
            # Find fields that are explicitly None and need to be unset
            unset_fields = {}
            for key, value in all_data.items():
                if value is None and key != 'id' and key != '_id':
                    unset_fields[key] = ""
            
            # Build update operation
            update_op = {}
            if data:
                update_op['$set'] = data
            if unset_fields:
                update_op['$unset'] = unset_fields
            
            if not update_op:
                # No changes to make
                return await self.get_by_id(id)
            
            result = await collection.update_one(
                {'_id': ObjectId(id)},
                update_op
            )
            if result.modified_count == 0 and not unset_fields:
                return None
            return await self.get_by_id(id)
        except Exception:
            return None

    async def delete(self, id: ID) -> bool:
        if not isinstance(id, str):
            return False
        try:
            collection = self._get_collection()
            result = await collection.delete_one({'_id': ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def find_one(self, filter: dict) -> Optional[T]:
        collection = self._get_collection()
        doc = await collection.find_one(filter)
        if not doc:
            return None
        return self._dict_to_entity(doc)

    async def find_many(self, filter: dict, skip: int = 0, limit: int = 100) -> List[T]:
        collection = self._get_collection()
        cursor = collection.find(filter).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._dict_to_entity(doc) for doc in docs]
