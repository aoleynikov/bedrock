from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from src.services.file_storage_service import FileStorageService
from src.services.user_service import UserService
from src.dependencies import get_file_storage_service, get_user_service
from src.auth.dependencies import get_current_user
from src.models.domain import User
from src.i18n.translator import get_translator
from src.exceptions.error_handlers import raise_translated_error
from src.constants.file_types import is_image_file, get_content_type

router = APIRouter()


class FileUploadResponse(BaseModel):
    file_key: str
    url: str
    original_filename: str


class UploadUrlResponse(BaseModel):
    file_key: str
    upload_url: str
    method: str
    expires_in: Optional[int] = None
    used_for: Optional[str] = None


class AvatarUpdateRequest(BaseModel):
    file_key: str


@router.get('/files/upload-url', response_model=UploadUrlResponse)
async def get_upload_url(
    request: Request,
    filename: str = Query(..., description='Original filename'),
    content_type: Optional[str] = Query(None, description='MIME type of the file'),
    prefix: Optional[str] = Query('', description='Optional prefix for file organization'),
    used_for: Optional[str] = Query(None, description='Purpose of the file (e.g., avatar, document)'),
    expires_in: int = Query(3600, description='URL expiration time in seconds (for S3)'),
    current_user: User = Depends(get_current_user),
    file_storage_service: FileStorageService = Depends(get_file_storage_service)
):
    """
    Get upload URL (presigned or regular) for file upload.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    try:
        result = await file_storage_service.generate_upload_url(
            filename=filename,
            content_type=content_type,
            prefix=prefix,
            expires_in=expires_in
        )
        # Store used_for in result for client to pass back during upload
        if used_for:
            result['used_for'] = used_for
        return UploadUrlResponse(**result)
    except ValueError as e:
        raise_translated_error(translator, e)


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post('/files/upload', response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    file_key: Optional[str] = Query(None, description='Pre-generated file key (from upload-url endpoint). If not provided, will be generated from filename.'),
    used_for: Optional[str] = Query(None, description='Purpose of the file (e.g., avatar, document)'),
    current_user: User = Depends(get_current_user),
    file_storage_service: FileStorageService = Depends(get_file_storage_service)
):
    """
    Unified file upload endpoint.
    
    Gateway: HTTP endpoint -> Service layer
    
    File keys use simple format: uuid/filename.ext
    UUID ensures uniqueness - every upload creates a new file (no overwrites).
    The file_key is the source of truth for all metadata.
    """
    translator = get_translator(request)
    
    # Validate file is provided
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translator.t('errors.file.empty') if translator else 'File is required'
        )
    
    try:
        original_filename = file.filename or 'upload'
        # Extract prefix from query params if provided
        prefix = request.query_params.get('prefix', '')
        file_key, original_filename = file_storage_service.prepare_upload_key(
            original_filename=original_filename,
            custom_key=file_key,
            prefix=prefix
        )
        
        # Use FastAPI's streaming capabilities - stream file directly to storage
        # This avoids loading entire file into memory
        stored_key, file_size = await file_storage_service.store_file_stream(
            file_stream=file,
            content_type=file.content_type,
            original_filename=original_filename,
            custom_key=file_key,
            owner_id=current_user.id,
            used_for=used_for,
            max_size=MAX_FILE_SIZE
        )
        
        file_url = file_storage_service.get_file_url(stored_key)
        extracted_filename = file_storage_service.extract_original_filename(stored_key)
        
        return FileUploadResponse(
            file_key=stored_key,
            url=file_url,
            original_filename=extracted_filename
        )
    except ValueError as e:
        raise_translated_error(translator, e)


@router.post('/users/me/avatar')
async def upload_avatar(
    request: Request,
    avatar_data: AvatarUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    file_storage_service: FileStorageService = Depends(get_file_storage_service)
):
    """
    Set user avatar using file_key.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    
    # Verify file exists in storage first
    if not await file_storage_service.file_exists(avatar_data.file_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translator.t('errors.file.not_found') if translator else 'File not found'
        )
    
    # Get UploadedFile record (if exists)
    uploaded_file = await file_storage_service.get_file_by_key(avatar_data.file_key)
    
    # Validate file ownership (if UploadedFile record exists) - check this first
    # If record exists, enforce ownership. If not, we can't verify ownership but still allow
    # (this is a trade-off: without records, we can't enforce ownership, but files without
    # records might be from before the tracking system was added)
    if uploaded_file:
        # Ensure both IDs are strings for comparison
        file_owner_id = str(uploaded_file.owner_id) if uploaded_file.owner_id else None
        current_user_id = str(current_user.id) if current_user.id else None
        
        if file_owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=translator.t('errors.file.unauthorized') if translator else 'You do not have permission to use this file'
            )
        # Validate file is marked for avatar use (only if record exists)
        if uploaded_file.used_for != 'avatar':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=translator.t('errors.file.invalid_usage') if translator else 'File is not marked for avatar use'
            )
    
    # Validate file type is an image
    filename = file_storage_service.extract_original_filename(avatar_data.file_key)
    if not is_image_file(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translator.t('errors.file.invalid_type') if translator else 'File must be an image'
        )
    
    try:
        updated_user = await user_service.set_avatar(
            user_id=current_user.id,
            file_key=avatar_data.file_key
        )
        
        return user_service.to_response(updated_user)
    except ValueError as e:
        raise_translated_error(translator, e)


@router.delete('/users/me/avatar')
async def delete_avatar(
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user avatar.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    try:
        updated_user = await user_service.delete_avatar(current_user.id)
        return user_service.to_response(updated_user)
    except ValueError as e:
        raise_translated_error(translator, e)


@router.get('/files/{file_key:path}')
async def get_file(
    request: Request,
    file_key: str,
    file_storage_service: FileStorageService = Depends(get_file_storage_service)
):
    """
    Retrieve a file by its storage key.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    try:
        file_data = await file_storage_service.retrieve_file(file_key)
        
        if file_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=translator.t('errors.file.not_found') if translator else 'File not found'
            )
        
        # Extract original filename from key
        original_filename = file_storage_service.extract_original_filename(file_key)
        
        # Determine content type from file extension
        content_type = get_content_type(original_filename)
        
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                'Content-Disposition': f'inline; filename="{original_filename}"'
            }
        )
    except ValueError as e:
        raise_translated_error(translator, e)
