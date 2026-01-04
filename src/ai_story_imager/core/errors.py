"""
Custom exceptions for the AI Story Imager application.

All exceptions inherit from StoryGenerationError to provide a common base
for error handling throughout the application.
"""


class StoryGenerationError(Exception):
    """
    Base exception for all story generation-related errors.
    
    All custom exceptions in this module inherit from this class,
    allowing for unified error handling.
    """
    pass


class ImageValidationError(StoryGenerationError):
    """
    Raised when image validation fails.
    
    This includes cases where:
    - Image file is too large
    - Unsupported file type
    - Corrupted or invalid image data
    - Image processing errors
    """
    pass


class APIConfigurationError(StoryGenerationError):
    """
    Raised when API configuration is invalid or missing.
    
    This includes cases where:
    - API key is missing or invalid
    - API key format is incorrect
    - Model initialization fails
    """
    pass


class APIError(StoryGenerationError):
    """
    Base exception for API-related errors.
    
    All API-specific errors inherit from this class.
    """
    pass


class APITimeoutError(APIError):
    """
    Raised when an API call times out.
    
    Indicates that the API request exceeded the maximum allowed time
    and was terminated.
    """
    pass


class APIRateLimitError(APIError):
    """
    Raised when API rate limit is exceeded.
    
    Indicates that too many requests have been made within a time period
    and the API is temporarily blocking further requests.
    """
    pass


class APIInvalidResponseError(APIError):
    """
    Raised when API returns invalid or malformed response.
    
    Indicates that the API response could not be parsed or does not
    match the expected format.
    """
    pass

