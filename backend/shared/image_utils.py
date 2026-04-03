"""
Image Processing Utilities — Multimodal Support
================================================
Provides secure image processing functions for multimodal AI pipelines.
Handles base64 encoding, validation, and OpenRouter API payload creation.

Security Features:
- Format validation (JPEG, PNG, WebP only)
- File size limits (10MB max)
- Content validation
- Secure encoding
"""

import base64
import io
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed image formats
ALLOWED_FORMATS = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp'
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_image_format(image_data: str) -> bool:
    """
    Validate image format from base64 string.
    
    Args:
        image_data: Base64 encoded image string
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        # Check if it's a valid base64 string
        if not image_data or not isinstance(image_data, str):
            return False
        
        # Decode base64 to check format
        image_bytes = base64.b64decode(image_data)
        
        # Check file signatures
        if image_bytes[:3] == b'\xff\xd8\xff':
            return True  # JPEG
        elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return True  # PNG
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return True  # WebP
        
        return False
        
    except Exception as e:
        logger.error(f"Image format validation error: {e}")
        return False


def validate_image_size(image_bytes: bytes) -> bool:
    """
    Validate image file size.
    
    Args:
        image_bytes: Image bytes to validate
        
    Returns:
        True if size is acceptable, False otherwise
    """
    return len(image_bytes) <= MAX_FILE_SIZE


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename:
        return False
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def get_image_format(image_bytes: bytes) -> Optional[str]:
    """
    Detect image format from bytes.
    
    Args:
        image_bytes: Image bytes to analyze
        
    Returns:
        MIME type string or None if unknown
    """
    try:
        if image_bytes[:3] == b'\xff\xd8\xff':
            return 'image/jpeg'
        elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return 'image/webp'
        return None
    except Exception as e:
        logger.error(f"Image format detection error: {e}")
        return None


# ============================================================================
# ENCODING FUNCTIONS
# ============================================================================

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Encode image file to base64 string.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded string or None if error
    """
    try:
        path = Path(image_path)
        
        # Validate file exists
        if not path.exists():
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Validate extension
        if not validate_file_extension(path.name):
            logger.error(f"Invalid file extension: {path.suffix}")
            return None
        
        # Read and encode
        with open(path, 'rb') as f:
            image_bytes = f.read()
        
        # Validate size
        if not validate_image_size(image_bytes):
            logger.error(f"Image file too large: {len(image_bytes)} bytes")
            return None
        
        # Encode to base64
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info(f"Image encoded successfully: {path.name}")
        return base64_string
        
    except Exception as e:
        logger.error(f"Image encoding error: {e}")
        return None


def encode_image_bytes_to_base64(image_bytes: bytes) -> Optional[str]:
    """
    Encode image bytes to base64 string.
    
    Args:
        image_bytes: Image bytes to encode
        
    Returns:
        Base64 encoded string or None if error
    """
    try:
        # Validate size
        if not validate_image_size(image_bytes):
            logger.error(f"Image bytes too large: {len(image_bytes)} bytes")
            return None
        
        # Encode to base64
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info(f"Image bytes encoded successfully: {len(image_bytes)} bytes")
        return base64_string
        
    except Exception as e:
        logger.error(f"Image bytes encoding error: {e}")
        return None


def decode_base64_to_image(base64_string: str) -> Optional[bytes]:
    """
    Decode base64 string to image bytes.
    
    Args:
        base64_string: Base64 encoded string
        
    Returns:
        Image bytes or None if error
    """
    try:
        # Validate base64 string
        if not base64_string or not isinstance(base64_string, str):
            logger.error("Invalid base64 string")
            return None
        
        # Decode base64
        image_bytes = base64.b64decode(base64_string)
        
        # Validate size
        if not validate_image_size(image_bytes):
            logger.error(f"Decoded image too large: {len(image_bytes)} bytes")
            return None
        
        logger.info(f"Base64 decoded successfully: {len(image_bytes)} bytes")
        return image_bytes
        
    except Exception as e:
        logger.error(f"Base64 decoding error: {e}")
        return None


# ============================================================================
# OPENROUTER API FUNCTIONS
# ============================================================================

def create_openrouter_image_payload(image_base64: str, mime_type: str = "image/jpeg") -> dict:
    """
    Create OpenRouter API image payload.
    
    Args:
        image_base64: Base64 encoded image string
        mime_type: MIME type of the image
        
    Returns:
        OpenRouter API payload dictionary
    """
    try:
        # Validate base64 string
        if not validate_image_format(image_base64):
            logger.error("Invalid image format for OpenRouter payload")
            return {}
        
        # Create data URL
        data_url = f"data:{mime_type};base64,{image_base64}"
        
        payload = {
            "type": "image_url",
            "image_url": {
                "url": data_url
            }
        }
        
        logger.info(f"OpenRouter image payload created: {mime_type}")
        return payload
        
    except Exception as e:
        logger.error(f"OpenRouter payload creation error: {e}")
        return {}


def create_openrouter_text_payload(text: str) -> dict:
    """
    Create OpenRouter API text payload.
    
    Args:
        text: Text content
        
    Returns:
        OpenRouter API payload dictionary
    """
    return {
        "type": "text",
        "text": text
    }


def create_openrouter_multimodal_message(
    text: str,
    image_base64: str,
    mime_type: str = "image/jpeg"
) -> dict:
    """
    Create OpenRouter multimodal message with text and image.
    
    Args:
        text: Text prompt
        image_base64: Base64 encoded image
        mime_type: MIME type of the image
        
    Returns:
        OpenRouter message dictionary
    """
    try:
        content = []
        
        # Add text payload
        if text:
            content.append(create_openrouter_text_payload(text))
        
        # Add image payload
        if image_base64:
            image_payload = create_openrouter_image_payload(image_base64, mime_type)
            if image_payload:
                content.append(image_payload)
        
        message = {
            "role": "user",
            "content": content
        }
        
        logger.info(f"OpenRouter multimodal message created: {len(content)} content items")
        return message
        
    except Exception as e:
        logger.error(f"OpenRouter multimodal message creation error: {e}")
        return {}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_image_info(image_bytes: bytes) -> dict:
    """
    Get image information from bytes.
    
    Args:
        image_bytes: Image bytes to analyze
        
    Returns:
        Dictionary with image information
    """
    try:
        mime_type = get_image_format(image_bytes)
        
        info = {
            "size_bytes": len(image_bytes),
            "size_kb": round(len(image_bytes) / 1024, 2),
            "size_mb": round(len(image_bytes) / (1024 * 1024), 2),
            "mime_type": mime_type,
            "is_valid": mime_type is not None,
            "is_size_valid": validate_image_size(image_bytes)
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Image info extraction error: {e}")
        return {
            "size_bytes": 0,
            "size_kb": 0,
            "size_mb": 0,
            "mime_type": None,
            "is_valid": False,
            "is_size_valid": False
        }


def compress_image(image_bytes: bytes, quality: int = 85) -> Optional[bytes]:
    """
    Compress image to reduce file size.
    
    Args:
        image_bytes: Original image bytes
        quality: Compression quality (1-100)
        
    Returns:
        Compressed image bytes or None if error
    """
    try:
        from PIL import Image
        
        # Open image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Compress
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_bytes = output.getvalue()
        
        logger.info(f"Image compressed: {len(image_bytes)} -> {len(compressed_bytes)} bytes")
        return compressed_bytes
        
    except ImportError:
        logger.warning("Pillow not installed, skipping compression")
        return image_bytes
    except Exception as e:
        logger.error(f"Image compression error: {e}")
        return image_bytes


def resize_image(
    image_bytes: bytes,
    max_width: int = 1024,
    max_height: int = 1024
) -> Optional[bytes]:
    """
    Resize image to maximum dimensions.
    
    Args:
        image_bytes: Original image bytes
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        
    Returns:
        Resized image bytes or None if error
    """
    try:
        from PIL import Image
        
        # Open image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Calculate new size
        ratio = min(max_width / img.width, max_height / img.height)
        if ratio < 1:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        resized_bytes = output.getvalue()
        
        logger.info(f"Image resized: {img.width}x{img.height}")
        return resized_bytes
        
    except ImportError:
        logger.warning("Pillow not installed, skipping resize")
        return image_bytes
    except Exception as e:
        logger.error(f"Image resize error: {e}")
        return image_bytes


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "MAX_FILE_SIZE",
    "ALLOWED_FORMATS",
    "ALLOWED_EXTENSIONS",
    # Validation
    "validate_image_format",
    "validate_image_size",
    "validate_file_extension",
    "get_image_format",
    # Encoding
    "encode_image_to_base64",
    "encode_image_bytes_to_base64",
    "decode_base64_to_image",
    # OpenRouter
    "create_openrouter_image_payload",
    "create_openrouter_text_payload",
    "create_openrouter_multimodal_message",
    # Utilities
    "get_image_info",
    "compress_image",
    "resize_image",
]
