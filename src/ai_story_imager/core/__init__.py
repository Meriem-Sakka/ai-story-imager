"""
Core module for AI Story Imager
Contains configuration and error definitions.
"""

from ai_story_imager.core.config import get_config, Config
from ai_story_imager.core.errors import (
    ImageValidationError,
    APIConfigurationError,
    APIError,
    APITimeoutError,
    APIRateLimitError,
    APIInvalidResponseError,
    StoryGenerationError
)

__all__ = [
    'get_config',
    'Config',
    'ImageValidationError',
    'APIConfigurationError',
    'APIError',
    'APITimeoutError',
    'APIRateLimitError',
    'APIInvalidResponseError',
    'StoryGenerationError',
]

