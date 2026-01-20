"""
Constants for file type detection and validation.
"""

# Supported image file extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

# Mapping of file extensions to MIME content types
CONTENT_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.txt': 'text/plain',
    '.json': 'application/json',
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.pdf': 'application/pdf',
}

# Default content type for unknown files
DEFAULT_CONTENT_TYPE = 'application/octet-stream'


def is_image_file(filename: str) -> bool:
    """
    Check if a filename has an image extension.
    
    Args:
        filename: Filename to check
    
    Returns:
        True if filename has an image extension, False otherwise
    """
    if not filename:
        return False
    return filename.lower().endswith(IMAGE_EXTENSIONS)


def get_content_type(filename: str) -> str:
    """
    Get content type for a filename based on its extension.
    
    Args:
        filename: Filename to check
    
    Returns:
        MIME content type or default if not recognized
    """
    if not filename:
        return DEFAULT_CONTENT_TYPE
    
    filename_lower = filename.lower()
    for ext, content_type in CONTENT_TYPES.items():
        if filename_lower.endswith(ext):
            return content_type
    
    return DEFAULT_CONTENT_TYPE
