from typing import Dict, Any
from datetime import datetime, timedelta
from src.repositories.uploaded_file_repository import UploadedFileRepository
from src.logging.logger import get_logger

logger = get_logger(__name__, 'tasks')


async def get_file_count_for_cleanup(
    uploaded_file_repository: UploadedFileRepository,
    file_type: str,
    max_age_hours: int
) -> int:
    """
    Get total count of files that need cleanup for a given type.
    
    Args:
        uploaded_file_repository: Repository to query
        file_type: Type of files to count (or None for untyped)
        max_age_hours: Maximum age in hours
    
    Returns:
        Total count of files matching criteria
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
    
    if file_type:
        filter_query = {
            'used_for': file_type,
            'created_at': {'$lt': cutoff_time}
        }
    else:
        filter_query = {
            '$or': [
                {'used_for': None},
                {'used_for': {'$exists': False}}
            ],
            'created_at': {'$lt': cutoff_time}
        }
    
    # Use count_documents for accurate count
    # Access protected method for pagination utilities
    collection = uploaded_file_repository._get_collection()
    count = await collection.count_documents(filter_query)
    return count


async def create_cleanup_chunks(
    uploaded_file_repository: UploadedFileRepository,
    file_type: str,
    max_age_hours: int,
    chunk_size: int = 1000
) -> list[Dict[str, Any]]:
    """
    Create chunk definitions for paginated cleanup processing.
    
    Args:
        uploaded_file_repository: Repository to query
        file_type: Type of files to process (or None for untyped)
        max_age_hours: Maximum age in hours
        chunk_size: Number of files per chunk
    
    Returns:
        List of chunk definitions with skip/limit for processing
    """
    total_count = await get_file_count_for_cleanup(
        uploaded_file_repository,
        file_type,
        max_age_hours
    )
    
    chunks = []
    for skip in range(0, total_count, chunk_size):
        chunks.append({
            'file_type': file_type,
            'skip': skip,
            'limit': chunk_size,
            'max_age_hours': max_age_hours
        })
    
    logger.info(
        f'Created {len(chunks)} chunks for {file_type or "untyped"} files',
        extra={
            'file_type': file_type,
            'total_count': total_count,
            'chunk_size': chunk_size,
            'chunk_count': len(chunks)
        }
    )
    
    return chunks
