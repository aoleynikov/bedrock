from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict, Any
from pydantic import BaseModel
from src.database.interfaces import IRepository

T = TypeVar('T', bound=BaseModel)
ID = TypeVar('ID')


class BaseRepository(IRepository[T, ID], ABC, Generic[T, ID]):
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @abstractmethod
    def _get_collection(self):
        pass

    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        pass
