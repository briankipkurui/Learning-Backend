from typing import Tuple
import secrets
from pathlib import Path
import re

def _validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Validate if the file has an allowed extension.

    :param filename: Name of the file to validate.
    :param allowed_extensions: Set of allowed file extensions (e.g., {'pdf', 'docx'}).
    :return: True if the file extension is allowed, False otherwise.
    """
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in allowed_extensions


def _validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate if the file size is within the allowed limit.

    :param file_size: Size of the file in bytes.
    :param max_size: Maximum allowed file size in MBs.
    :return: True if the file size is within the limit, False otherwise.
    """
    return file_size <= max_size * 1024 * 1024


def validate_file(filename: str, file_size: int, allowed_extensions: set, max_size: int) -> Tuple[bool, str]:
    """
    Validate the file based on its extension and size.

    :param filename: Name of the file to validate.
    :param file_size: Size of the file in bytes.
    :param allowed_extensions: Set of allowed file extensions (e.g., {'pdf', 'docx'}).
    :param max_size: Maximum allowed file size in bytes.
    :return: Tuple (is_valid, message). is_valid is True if valid, False otherwise. message contains error details if invalid.
    """
    if not _validate_file_extension(filename, allowed_extensions):
        return False, f"Invalid file type. Allowed types are: {[', '.join(allowed_extensions)]}"
    
    if not _validate_file_size(file_size, max_size):
        return False, f"File size exceeds the maximum limit of {max_size} MB"
    
    return True, "File is valid"

def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and special characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Get file extension
        file_path = Path(filename)
        name = file_path.stem
        ext = file_path.suffix
        
        # Remove special characters, keep only alphanumeric, hyphens, and underscores
        safe_name = re.sub(r'[^\w\-]', '_', name)
        
        # Limit length
        safe_name = safe_name[:100]
        
        if not safe_name:
            safe_name = secrets.token_hex(10)
        
        return f"{safe_name}{ext}"