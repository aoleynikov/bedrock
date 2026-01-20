from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)
ID = TypeVar('ID')


class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass

    @abstractmethod
    async def get_by_id(self, id: ID) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass

    @abstractmethod
    async def update(self, id: ID, entity: T) -> Optional[T]:
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        pass

    @abstractmethod
    async def find_one(self, filter: dict) -> Optional[T]:
        pass

    @abstractmethod
    async def find_many(self, filter: dict, skip: int = 0, limit: int = 100) -> List[T]:
        pass
