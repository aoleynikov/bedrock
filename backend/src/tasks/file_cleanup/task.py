import time
import asyncio
from typing import Dict, Any
from src.tasks.celery.celery_app import celery_app
from src.tasks.context import get_task_correlation_id, set_task_correlation_id
from src.tasks.metrics import celery_tasks_total, celery_task_duration_seconds
from src.logging.logger import get_logger
from src.database.connection import DatabaseConnection
from src.repositories.uploaded_file_repository import UploadedFileRepository
from src.repositories.user_repository import UserRepository
from src.dependencies import get_file_storage_service
from src.tasks.file_cleanup.handlers import (
    AvatarFileCleanupHandler,
    DocumentFileCleanupHandler,
    DefaultFileCleanupHandler
)
from src.tasks.file_cleanup.pagination import create_cleanup_chunks
from src.tasks.queue import enqueue

logger = get_logger(__name__, 'tasks')

@celery_app.task(name='cleanup_unused_files', bind=True)
def cleanup_unused_files(self, max_age_hours: int = 6, correlation_id: str = None):
    """
    Scheduled task to clean up unused files older than specified hours.
    
    This is the coordinator task that:
    1. Counts total files to process
    2. Splits work into chunks
    3. Queues chunk processing tasks
    
    File lifecycle:
    - User uploads file → UploadedFile record created
    - Client has ~6h to bind file to entity (e.g., set as avatar)
    - This job runs every 6h to clean up unbound files older than 6h
    
    Args:
        max_age_hours: Maximum age in hours before cleanup (default: 6)
        correlation_id: Correlation ID for request tracking
    """
    set_task_correlation_id(correlation_id)
    task_correlation_id = get_task_correlation_id()
    task_id = self.request.id
    
    start_time = time.time()
    
    logger.info(
        f'File cleanup task started',
        extra={
            'correlation_id': task_correlation_id,
            'task_name': 'cleanup_unused_files',
            'task_id': task_id,
            'max_age_hours': max_age_hours
        }
    )
    
    try:
        # Run async cleanup coordinator (creates chunks and queues them)
        result = asyncio.run(_run_cleanup_coordinator(max_age_hours, task_correlation_id, task_id))
        
        duration = time.time() - start_time
        
        celery_tasks_total.labels(
            task_name='cleanup_unused_files',
            status='success'
        ).inc()
        
        celery_task_duration_seconds.labels(
            task_name='cleanup_unused_files',
            status='success'
        ).observe(duration)
        
        logger.info(
            f'File cleanup task completed',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'cleanup_unused_files',
                'task_id': task_id,
                'duration': duration * 1000,
                **result
            }
        )
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        
        celery_tasks_total.labels(
            task_name='cleanup_unused_files',
            status='failure'
        ).inc()
        
        celery_task_duration_seconds.labels(
            task_name='cleanup_unused_files',
            status='failure'
        ).observe(duration)
        
        logger.error(
            f'File cleanup task failed: {str(e)}',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'cleanup_unused_files',
                'task_id': task_id,
                'duration': duration * 1000,
            },
            exc_info=True,
        )
        raise


async def _run_cleanup_coordinator(max_age_hours: int, correlation_id: str, task_id: str) -> Dict[str, Any]:
    """
    Async coordinator that creates chunks and queues processing tasks.
    
    Database connection: Motor uses connection pooling automatically.
    We ensure connection exists, but Motor reuses connections from pool.
    """
    # Ensure database is connected (Motor handles connection pooling automatically)
    try:
        db = DatabaseConnection.get_db()
    except RuntimeError:
        # First connection attempt - Motor will create connection pool
        await DatabaseConnection.connect()
        db = DatabaseConnection.get_db()
    
    uploaded_file_repository = UploadedFileRepository(db)
    
    # Create chunks for each file type
    file_types = ['avatar', 'document', None]  # None for untyped
    all_chunks = []
    
    for file_type in file_types:
        try:
            chunks = await create_cleanup_chunks(
                uploaded_file_repository,
                file_type,
                max_age_hours,
                chunk_size=1000
            )
            all_chunks.extend(chunks)
        except Exception as e:
            logger.error(
                f'Failed to create chunks for {file_type}',
                error=e,
                extra={
                    'correlation_id': correlation_id,
                    'task_id': task_id,
                    'file_type': file_type
                }
            )
    
    # Queue chunk processing tasks
    queued_tasks = []
    for chunk in all_chunks:
        try:
            task = enqueue(
                'process_cleanup_chunk',
                correlation_id=correlation_id,
                **chunk
            )
            queued_tasks.append(task.id)
        except Exception as e:
            logger.error(
                f'Failed to queue chunk task',
                error=e,
                extra={
                    'correlation_id': correlation_id,
                    'task_id': task_id,
                    'chunk': chunk
                }
            )
    
    logger.info(
        f'Queued {len(queued_tasks)} chunk processing tasks',
        extra={
            'correlation_id': correlation_id,
            'task_id': task_id,
            'chunk_count': len(all_chunks),
            'queued_tasks': len(queued_tasks)
        }
    )
    
    return {
        'status': 'coordinated',
        'max_age_hours': max_age_hours,
        'chunks_created': len(all_chunks),
        'tasks_queued': len(queued_tasks),
        'task_ids': queued_tasks
    }


@celery_app.task(name='process_cleanup_chunk', bind=True)
def process_cleanup_chunk(
    self,
    file_type: str,
    skip: int,
    limit: int,
    max_age_hours: int,
    correlation_id: str = None
):
    """
    Process a single chunk of files for cleanup.
    
    Args:
        file_type: Type of files to process (or None for untyped)
        skip: Number of files to skip
        limit: Maximum number of files to process
        max_age_hours: Maximum age in hours
        correlation_id: Correlation ID for request tracking
    """
    set_task_correlation_id(correlation_id)
    task_correlation_id = get_task_correlation_id()
    task_id = self.request.id
    
    start_time = time.time()
    
    logger.info(
        f'Processing cleanup chunk',
        extra={
            'correlation_id': task_correlation_id,
            'task_name': 'process_cleanup_chunk',
            'task_id': task_id,
            'file_type': file_type,
            'skip': skip,
            'limit': limit,
            'max_age_hours': max_age_hours
        }
    )
    
    try:
        result = asyncio.run(_run_cleanup_chunk(
            file_type, skip, limit, max_age_hours, task_correlation_id, task_id
        ))
        
        duration = time.time() - start_time
        
        celery_tasks_total.labels(
            task_name='process_cleanup_chunk',
            status='success'
        ).inc()
        
        celery_task_duration_seconds.labels(
            task_name='process_cleanup_chunk',
            status='success'
        ).observe(duration)
        
        logger.info(
            f'Cleanup chunk processed',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'process_cleanup_chunk',
                'task_id': task_id,
                'duration': duration * 1000,
                **result
            }
        )
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        
        celery_tasks_total.labels(
            task_name='process_cleanup_chunk',
            status='failure'
        ).inc()
        
        celery_task_duration_seconds.labels(
            task_name='process_cleanup_chunk',
            status='failure'
        ).observe(duration)
        
        logger.error(
            f'Cleanup chunk failed: {str(e)}',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'process_cleanup_chunk',
                'task_id': task_id,
                'duration': duration * 1000,
            },
            exc_info=True,
        )
        raise


async def _run_cleanup_chunk(
    file_type: str,
    skip: int,
    limit: int,
    max_age_hours: int,
    correlation_id: str,
    task_id: str
) -> Dict[str, Any]:
    """
    Process a single chunk of files.
    
    Database connection: Motor uses connection pooling automatically.
    Connections are reused from the pool - no need to create new ones.
    """
    # Ensure database is connected (Motor handles connection pooling automatically)
    try:
        db = DatabaseConnection.get_db()
    except RuntimeError:
        # First connection attempt - Motor will create connection pool
        await DatabaseConnection.connect()
        db = DatabaseConnection.get_db()
    
    uploaded_file_repository = UploadedFileRepository(db)
    user_repository = UserRepository(db)
    file_storage_service = get_file_storage_service()
    
    # Select appropriate handler
    if file_type == 'avatar':
        handler = AvatarFileCleanupHandler(
            uploaded_file_repository,
            file_storage_service,
            user_repository
        )
    elif file_type == 'document':
        handler = DocumentFileCleanupHandler(
            uploaded_file_repository,
            file_storage_service,
            user_repository
        )
    else:
        handler = DefaultFileCleanupHandler(
            uploaded_file_repository,
            file_storage_service,
            user_repository
        )
    
    # Process chunk with pagination
    result = await handler.cleanup_files(max_age_hours, skip=skip, limit=limit)
    
    return {
        'status': 'completed',
        'file_type': file_type,
        'skip': skip,
        'limit': limit,
        **result
    }
