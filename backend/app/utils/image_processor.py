"""
Image Processor Utilities
========================
Base64 encoding and image processing for multimodal vision pipelines.
"""

import base64
import io
from typing import Optional, Tuple, List
from PIL import Image
import structlog

logger = structlog.get_logger()

# Supported image formats
SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "GIF", "BMP"}

# Maximum image dimensions (to reduce payload size for API calls)
MAX_DIMENSION = 2048

# Quality for JPEG compression
JPEG_QUALITY = 85


def encode_image_to_base64(image_data: bytes) -> str:
    """
    Encode raw image bytes to base64 string.
    
    Args:
        image_data: Raw image bytes
    
    Returns:
        Base64 encoded string (without data URI prefix)
    """
    return base64.b64encode(image_data).decode("utf-8")


def decode_base64_to_image(base64_string: str) -> bytes:
    """
    Decode base64 string to image bytes.
    
    Args:
        base64_string: Base64 encoded image string
    
    Returns:
        Raw image bytes
    """
    # Remove data URI prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",", 1)[1]
    
    return base64.b64decode(base64_string)


def resize_image_if_needed(image: Image.Image) -> Image.Image:
    """
    Resize image if it exceeds maximum dimensions.
    
    Args:
        image: PIL Image
    
    Returns:
        Resized image (or original if within limits)
    """
    width, height = image.size
    
    if width <= MAX_DIMENSION and height <= MAX_DIMENSION:
        return image
    
    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = MAX_DIMENSION
        new_height = int(height * (MAX_DIMENSION / width))
    else:
        new_height = MAX_DIMENSION
        new_width = int(width * (MAX_DIMENSION / height))
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def process_uploaded_image(file_content: bytes, target_format: str = "PNG") -> Tuple[bytes, str]:
    """
    Process an uploaded image file.
    
    Args:
        file_content: Raw file bytes
        target_format: Target image format (default: PNG)
    
    Returns:
        Tuple of (processed image bytes, mime type)
    """
    try:
        image = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        
        # Resize if needed
        image = resize_image_if_needed(image)
        
        # Save to buffer
        output = io.BytesIO()
        image.save(output, format=target_format, quality=JPEG_QUALITY)
        output.seek(0)
        
        mime_type = f"image/{target_format.lower()}"
        
        return output.getvalue(), mime_type
        
    except Exception as e:
        logger.error("image_processing_failed", error=str(e))
        raise ValueError(f"Failed to process image: {str(e)}")


def encode_image_for_openrouter(file_content: bytes) -> str:
    """
    Encode image for OpenRouter API consumption.
    
    Converts image to base64 and wraps in data URI format
    that OpenRouter expects for vision models.
    
    Args:
        file_content: Raw image file bytes
    
    Returns:
        Base64 string with data URI prefix for OpenRouter
    """
    processed_bytes, mime_type = process_uploaded_image(file_content)
    base64_encoded = base64.b64encode(processed_bytes).decode("utf-8")
    
    return f"data:{mime_type};base64,{base64_encoded}"


def validate_image_file(filename: str, file_content: bytes) -> bool:
    """
    Validate an image file.
    
    Args:
        filename: Original filename
        file_content: File bytes
    
    Returns:
        True if valid image
    
    Raises:
        ValueError: If invalid
    """
    # Check file extension
    extension = filename.split(".")[-1].upper() if "." in filename else ""
    
    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format: {extension}. "
            f"Supported: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # Try to open as image
    try:
        image = Image.open(io.BytesIO(file_content))
        image.verify()
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")
    
    return True


def get_image_dimensions(file_content: bytes) -> Tuple[int, int]:
    """
    Get image dimensions.
    
    Args:
        file_content: Raw image bytes
    
    Returns:
        Tuple of (width, height)
    """
    image = Image.open(io.BytesIO(file_content))
    return image.size


def create_thumbnail(file_content: bytes, size: Tuple[int, int] = (256, 256)) -> bytes:
    """
    Create a thumbnail of an image.
    
    Args:
        file_content: Raw image bytes
        size: Target thumbnail size (default: 256x256)
    
    Returns:
        Thumbnail image bytes
    """
    image = Image.open(io.BytesIO(file_content))
    image.thumbnail(size, Image.Resampling.LANCZOS)
    
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    
    return output.getvalue()


def process_multiple_images(files: List[bytes]) -> List[str]:
    """
    Process multiple images for OpenRouter vision models.
    
    Args:
        files: List of image file bytes
    
    Returns:
        List of base64 encoded images with data URI prefix
    """
    encoded_images = []
    
    for file_content in files:
        try:
            encoded = encode_image_for_openrouter(file_content)
            encoded_images.append(encoded)
        except Exception as e:
            logger.warning("image_encoding_skipped", error=str(e))
            continue
    
    return encoded_images


__all__ = [
    "encode_image_to_base64",
    "decode_base64_to_image",
    "resize_image_if_needed",
    "process_uploaded_image",
    "encode_image_for_openrouter",
    "validate_image_file",
    "get_image_dimensions",
    "create_thumbnail",
    "process_multiple_images",
    "SUPPORTED_FORMATS",
    "MAX_DIMENSION",
]