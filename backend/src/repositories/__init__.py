from src.database.connection import DatabaseConnection
from src.repositories.user_repository import UserRepository
from src.repositories.uploaded_file_repository import UploadedFileRepository


def get_user_repository() -> UserRepository:
    db = DatabaseConnection.get_db()
    return UserRepository(db)


def get_uploaded_file_repository() -> UploadedFileRepository:
    db = DatabaseConnection.get_db()
    return UploadedFileRepository(db)
