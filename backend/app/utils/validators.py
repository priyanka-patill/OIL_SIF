import re
import os
from typing import Tuple
from fastapi import HTTPException, status
from app.config.settings import settings


def validate_file_upload(filename: str, file_size: int) -> Tuple[str, str]:
    """Validate uploaded file extension and size constraints."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty"
        )
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.1f} MB"
        )
    
    clean_type = ext.replace(".", "").lower()
    if clean_type in ["xlsx", "xls"]:
        clean_type = "xlsx"
    
    return clean_type, ext


def sanitize_column_name(col_name: str) -> str:
    """Sanitize column name for programmatic and database query safety."""
    col_str = str(col_name).strip()
    # Replace non-alphanumeric with underscore
    sanitized = re.sub(r"[^\w\s]", "", col_str)
    sanitized = re.sub(r"\s+", "_", sanitized).strip("_")
    return sanitized.lower() if sanitized else "unnamed_column"
