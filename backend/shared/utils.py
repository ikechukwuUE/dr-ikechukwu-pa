"""
Shared Utility Functions
========================
Common utility functions used across all domains.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_text_from_agent_result(result: Any) -> str:
    """
    Extract text content from agent result, handling MessageTextContent objects.
    
    This function safely extracts text from various agent result formats,
    including MessageTextContent objects that may have a 'text' attribute.
    
    Args:
        result: Agent result object (typically from BeeAI framework)
        
    Returns:
        Extracted text as string, or empty string if extraction fails
    """
    try:
        if result.output and len(result.output) > 0:
            last_message = result.output[-1]
            if hasattr(last_message, 'content'):
                content = last_message.content
                # Handle MessageTextContent object
                try:
                    # Try to access text attribute
                    text_value = getattr(content, 'text', None)
                    if text_value is not None:
                        return str(text_value)
                    else:
                        return str(content)
                except (AttributeError, TypeError):
                    # If text attribute doesn't exist, convert to string
                    return str(content)
            else:
                return str(last_message)
    except Exception as e:
        logger.warning(f"Error extracting text from agent result: {e}")
    return ""
