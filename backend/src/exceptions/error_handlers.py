from fastapi import HTTPException, status
from src.i18n.translator import Translator


def translate_error_message(translator: Translator, error_msg: str) -> str:
    """
    Translate an error message from a ValueError.
    
    Handles:
    - Translation keys: 'errors.file.empty' -> translated message
    - Parameterized errors: 'errors.file.size_exceeds:10485760' -> translated with params
    - Plain strings: 'Some error' -> returned as-is
    
    Args:
        translator: Translator instance (may be None)
        error_msg: Error message from ValueError
    
    Returns:
        Translated error message or original if not a translation key
    """
    # Check if it's a translation key (contains dots like 'errors.xxx' or 'validation.xxx')
    if '.' not in error_msg or not (error_msg.startswith('errors.') or error_msg.startswith('validation.')):
        return error_msg
    
    # Handle parameterized errors (format: 'errors.xxx:param')
    if ':' in error_msg:
        key, param = error_msg.split(':', 1)
        # For size_exceeds, extract max_size parameter
        if key == 'errors.file.size_exceeds':
            return translator.t(key, max_size=param) if translator else f'File size exceeds maximum allowed size ({param} bytes)'
        else:
            return translator.t(key) if translator else error_msg
    
    # Regular translation key
    return translator.t(error_msg) if translator else error_msg


def raise_translated_error(
    translator: Translator,
    error: ValueError,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> None:
    """
    Translate a ValueError and raise HTTPException.
    
    Args:
        translator: Translator instance
        error: ValueError exception
        status_code: HTTP status code (default: 400)
    
    Raises:
        HTTPException with translated error message
    """
    error_msg = str(error)
    detail = translate_error_message(translator, error_msg)
    raise HTTPException(status_code=status_code, detail=detail)
